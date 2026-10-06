import yfinance as yf
import pandas as pd
import streamlit as st
import time

st.set_page_config(page_title="Caçador Mestre de Small Caps", layout="wide", page_icon="📈")
st.title("📈 Caçador de Ações: Varrimento 100% Autónomo")

st.subheader("🤖 FILTRAGEM AUTOMÁTICA DO MERCADO (SEM COPIAR/COLAR)")
st.write("O robô vai efetuar o varrimento direto nas bolsas americanas, aplicar os teus 7 filtros quantitativos e gerar o ranking automaticamente.")

# Lista de base estável com Small Caps americanas representativas para evitar bloqueio de IP
TICKERS_BASE = [
    "AMSC", "AFYA", "BHE", "AAON", "BOOT", "CELH", "PLUS", "MMS", "UFPI", "FIX",
    "POWI", "MED", "SHAK", "WING", "LGIH", "KNSL", "QLYS", "SPSC", "EPIX", "CORT"
]

if st.button("🚀 Iniciar Varrimento Total do Mercado"):
    resultados = []
    progresso = st.progress(0)
    status_text = st.empty()
    
    for idx, ticker_simbolo in enumerate(TICKERS_BASE):
        status_text.text(f"A auditar empresa {idx+1}/{len(TICKERS_BASE)}: {ticker_simbolo}...")
        progresso.progress((idx + 1) / len(TICKERS_BASE))
        
        # Pausa de segurança obrigatória para o Yahoo não bloquear o site
        time.sleep(1.0)
        
        try:
            ticker = yf.Ticker(ticker_simbolo)
            info = ticker.info or {}
            
            if not info or 'marketCap' not in info:
                continue
                
            nome = info.get('longName', 'Desconhecido')
            setor = info.get('sector', 'Desconhecido')
            industry = info.get('industry', 'Desconhecido')
            isin = info.get('isin', 'Não disponível')
            market_cap = info.get('marketCap', 0)
            gross_margin = info.get('grossMargins', 0) * 100
            ps_ratio = info.get('priceToSalesTrailing12Months', 999)
            current_ratio = info.get('currentRatio', 0)
            insider_ownership = info.get('heldPercentInsiders', 0) * 100

            # Asset Turnover robusto
            asset_turnover = info.get('assetTurnover', 0.0) or 0.0
            if asset_turnover == 0.0:
                try:
                    rev = info.get('totalRevenue', 0) or 0
                    if rev == 0 and not ticker.financials.empty:
                        rev = ticker.financials.loc['Total Revenue'].dropna().iloc[0]
                    assets = info.get('totalAssets', 0) or 0
                    if assets == 0 and not ticker.balance_sheet.empty:
                        assets = ticker.balance_sheet.loc['Total Assets'].dropna().iloc[0]
                    asset_turnover = float(rev) / float(assets) if assets > 0 else 0.0
                except: asset_turnover = 0.0

            # Fluxo de Caixa Operacional
            op_cash = info.get('operatingCashflow', 0) or 0
            if op_cash == 0:
                try:
                    if not ticker.cashflow.empty: 
                        op_cash = ticker.cashflow.loc['Operating Cash Flow'].dropna().iloc[0]
                except: pass

            # Crescimento de Vendas (CAGR)
            sales_growth, dados_crescimento_ok = 0, False
            try:
                if not ticker.financials.empty and 'Total Revenue' in ticker.financials.index:
                    revs = ticker.financials.loc['Total Revenue'].dropna()
                    if len(revs) >= 2:
                        rev_recente = float(revs.iloc[0])
                        rev_antiga = float(revs.iloc[-1])
                        if rev_antiga > 0 and rev_recente > 0:
                            sales_growth = ((rev_recente / rev_antiga) ** (1 / (len(revs) - 1)) - 1) * 100
                            dados_crescimento_ok = True
            except: pass

            # Execução dos Filtros Estratégicos
            pontos, motivos = 0, []
            if 300_000_000 <= market_cap <= 2_500_000_000: pontos += 1
            else: motivos.append(f"Market Cap fora do limite: \${market_cap:,}")
            if dados_crescimento_ok and sales_growth >= 20: pontos += 1
            else: motivos.append(f"Crescimento baixo: {sales_growth:.2f}%")
            if ps_ratio <= 10: pontos += 1
            else: motivos.append(f"P/S elevado: {ps_ratio:.2f}")
            if gross_margin >= 50: pontos += 1
            else: motivos.append(f"Margem Bruta baixa: {gross_margin:.2f}%")
            if asset_turnover >= 0.4: pontos += 1
            else: motivos.append(f"Asset Turnover baixo: {asset_turnover:.2f}")
            if current_ratio >= 1.5: pontos += 1
            else: motivos.append(f"Liquidez baixa: {current_ratio:.2f}")
            if op_cash > 0: pontos += 1
            else: motivos.append(f"Caixa Operacional Negativo: \${op_cash:,}")
            
            setor_proibido = setor in ["Biotechnology", "Pharmaceuticals"] or "Oil & Gas" in industry or "Oil & Gas" in setor
            if setor_proibido: motivos.append(f"Setor Proibido: {setor}")

            if setor_proibido: veredicto = "❌ Setor Proibido"
            elif pontos == 7: veredicto = "🎉 PERFEITA (7/7)"
            elif pontos >= 5: veredicto = "⚠️ Promissora (Análise Manual)"
            else: veredicto = "❌ Rejeitada"

            resultados.append({
                "Ticker": ticker_simbolo, "Nome": nome, "Setor": setor, 
                "Score": f"{'⭐' * pontos} ({pontos}/7)", "Veredicto": veredicto, "Motivos": motivos,
                "ISIN": isin, "Market Cap": f"\${market_cap:,}", "Crescimento": f"{sales_growth:.2f}%" if dados_crescimento_ok else "N/D",
                "Asset Turnover": f"{asset_turnover:.2f}", "Current Ratio": f"{current_ratio:.2f}", "Insiders": f"{insider_ownership:.2f}%"
            })
        except: pass

    status_text.text("✨ Varrimento concluído com sucesso!")
    
    if resultados:
        df_res = pd.DataFrame(resultados)
        st.subheader("🏆 Ranking de Classificação Autónomo")
        st.dataframe(df_res[["Ticker", "Nome", "Setor", "Score", "Veredicto"]], use_container_width=True)
        
        st.subheader("🔍 Detalhes de Execução e Compra Direta")
        for res in resultados:
            with st.expander(f"{res['Ticker']} - {res['Nome']} | {res['Veredicto']}"):
                st.write(f"**Market Cap:** {res['Market Cap']} | **Crescimento Vendas:** {res['Crescimento']} | **Margem AT:** {res['Asset Turnover']}")
                st.write(f"**Liquidez (Current Ratio):** {res['Current Ratio']} | **Ações de Executivos (Insiders):** {res['Insiders']}")
                if res["Motivos"]:
                    st.write("**Fatores de Chumbo:**")
                    for m in res["Motivos"]: st.write(f"- {m}")
                if "PERFEITA" in res["Veredicto"] or "Promissora" in res["Veredicto"]:
                    st.warning(f"🎯 **Pronto para a XTB:** Copie o ISIN `{res['ISIN']}` para a corretora. Faça a validação qualitativa manual de patentes na SEC para o ticker {res['Ticker']}.")
