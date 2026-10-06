import yfinance as yf
import pandas as pd
import streamlit as st
import time

st.set_page_config(page_title="Caçador Mestre de Small Caps", layout="wide", page_icon="📈")
st.title("📈 Caçador de Ações: Varrimento 100% Autónomo do Mercado")

st.subheader("🤖 PROCESSO AUTOMÁTICO SEM XTB (ZERO TRABALHO MANUAL)")
st.write("O robô efetua a triagem direta no ecossistema de Small Caps dos EUA e aplica a tua estratégia de hipercrescimento.")

if st.button("🚀 Iniciar Varrimento Total do Mercado"):
    resultados = []
    status_text = st.empty()
    
    # 50 Small Caps e Micro Caps americanas selecionadas para a tua estratégia
    todos_tickers = [
        "AMSC", "AFYA", "BHE", "AAON", "BOOT", "CELH", "PLUS", "MMS", "UFPI", "FIX",
        "SHAK", "WING", "LGIH", "KNSL", "QLYS", "SPSC", "EPIX", "CORT", "POWI", "MED",
        "PRTH", "NVMI", "SMTC", "EXTR", "FORM", "SGH", "AEIS", "COHR", "DIOD", "OSIS",
        "SPWR", "NOVT", "TTMI", "VIAV", "ITI", "SANM", "CTS", "CAMP", "BELFA", "POWI",
        "CALX", "PLAB", "CCMP", "AOSL", "CEVA", "PDFS", "UCTT", "QUIK", "RESN", "ATOM"
    ]
    
    todos_tickers = list(dict.fromkeys(todos_tickers))
    progresso = st.progress(0)
    total_lote = len(todos_tickers)
    
    for idx, ticker_simbolo in enumerate(todos_tickers):
        status_text.text(f"A auditar {idx+1}/{total_lote}: {ticker_simbolo}...")
        progresso.progress((idx + 1) / total_lote)
        
        time.sleep(1.0) # Proteção obrigatória contra bloqueios
        
        try:
            ticker = yf.Ticker(ticker_simbolo)
            info = ticker.info
            
            if not info or 'marketCap' not in info:
                continue
                
            market_cap = info.get('marketCap', 0)
            
            if not (300_000_000 <= market_cap <= 2_500_000_000):
                continue
                
            nome = info.get('longName', 'Desconhecido')
            setor = info.get('sector', 'Desconhecido')
            industry = info.get('industry', 'Desconhecido')
            isin = info.get('isin', 'Não disponível')
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
                except: 
                    asset_turnover = 0.0

            # Fluxo de Caixa Operacional
            op_cash = info.get('operatingCashflow', 0) or 0
            if op_cash == 0:
                try:
                    if not ticker.cashflow.empty: 
                        op_cash = ticker.cashflow.loc['Operating Cash Flow'].dropna().iloc[0]
                except: 
                    pass

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
            except: 
                pass

            # Pontuação (7 Filtros)
            pontos, motivos = 0, []
            if 300_000_000 <= market_cap <= 2_500_000_000: pontos += 1
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
            if setor_proibido: motivos.append(f"Setor Proibido GICS: {setor}")

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
        except: 
            pass

    status_text.text("✨ Varrimento de mercado concluído com sucesso!")
    
    if resultados:
        df_res = pd.DataFrame(resultados)
        st.subheader("🏆 Ranking de Classificação das Ações")
        st.dataframe(df_res[["Ticker", "Nome", "Setor", "Score", "Veredicto"]], use_container_width=True)
        
        st.subheader("🔍 Detalhes de Execução e Compra Direta")
        for res in resultados:
            if "PERFEITA" in res["Veredicto"] or "Promissora" in res["Veredicto"]:
                with st.expander(f"⭐ Ouro Detetado: {res['Ticker']} - {res['Nome']}"):
                    st.write(f"**ISIN para a XTB:** `{res['ISIN']}`")
                    st.write(f"**Crescimento:** {res['Crescimento']} | **Asset Turnover:** {res['Asset Turnover']} | **Liquidez:** {res['Current Ratio']}")
                    st.warning(f"Insiders detêm {res['Insiders']}. Faça a validação qualitativa manual de patentes no Form 10-K.")
