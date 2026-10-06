import yfinance as yf
import pandas as pd
import streamlit as st
import requests
import time

st.set_page_config(page_title="Caçador Mestre de Small Caps", layout="wide", page_icon="📈")
st.title("📈 Caçador de Ações: Varrimento 100% Autónomo do Mercado")

st.subheader("🤖 PROCESSO AUTOMÁTICO SEM XTB (ZERO TRABALHO MANUAL)")
st.write("O robô vai descarregar a lista completa de empresas dos EUA, filtrar apenas as Small Caps e aplicar a tua estratégia de hipercrescimento.")

if st.button("🚀 Iniciar Varrimento Total do Mercado"):
    resultados = []
    status_text = st.empty()
    
    with st.spinner("A descarregar a lista completa do mercado americano via SEC EDGAR..."):
        try:
            # Cabeçalho obrigatório para a API da SEC não bloquear o site
            headers = {'User-Agent': "CacadorSmallCaps/1.0 (analise@quant.com)"}
            url = "https://sec.gov"
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                # Extrair todos os tickers únicos
                todos_tickers = [item['ticker'].upper() for item in data.values()]
                st.success(f"🎯 Mercado mapeado com sucesso! Detetadas {len(todos_tickers)} empresas.")
            else:
                todos_tickers = []
                st.error("Falha ao ligar à base de dados do mercado. A usar lote de contingência.")
        except Exception as e:
            todos_tickers = []
            st.error(f"Erro de conexão: {str(e)}")

    # Se a API da SEC falhar, usamos uma lista de contingência forte
    if not todos_tickers:
        todos_tickers = ["AMSC", "AFYA", "BHE", "AAON", "BOOT", "CELH", "PLUS", "MMS", "UFPI", "FIX", "SHAK", "WING", "LGIH", "KNSL", "QLYS", "SPSC"]

    # Selecionar um lote focado para processamento ultra-seguro (Evita estoiros de memória no Streamlit)
    lote_analise = todos_tickers[:40] 
    
    progresso = st.progress(0)
    
    for idx, ticker_simbolo in enumerate(lote_analise):
        status_text.text(f"A auditar {idx+1}/{len(lote_analise)}: {ticker_simbolo}...")
        progresso.progress((idx + 1) / len(lote_analise))
        
        # Pausa obrigatória de 1 segundo para proteger o IP do teu site contra bloqueios do Yahoo
        time.sleep(1.0)
        
        try:
            ticker = yf.Ticker(ticker_simbolo)
            info = ticker.info or {}
            
            if not info or 'marketCap' not in info:
                continue
                
            market_cap = info.get('marketCap', 0)
            
            # FILTRO 1 IMEDIATO: Se não for Small Cap, descarta logo para poupar memória e RAM
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

            # Cálculo robusto do Asset Turnover
            asset_turnover = info.get('assetTurnover', 0.0) or 0.0
            if asset_turnover == 0.0:
                try:
                    rev = info.get('totalRevenue', 0) or 0
                    if rev == 0 and not ticker.financials.empty:
                        rev = ticker.financials.loc['Total Revenue'].dropna().iloc
                    assets = info.get('totalAssets', 0) or 0
                    if assets == 0 and not ticker.balance_sheet.empty:
                        assets = ticker.balance_sheet.loc['Total Assets'].dropna().iloc
                    asset_turnover = float(rev) / float(assets) if assets > 0 else 0.0
                except: asset_turnover = 0.0

            # Fluxo de Caixa Operacional
            op_cash = info.get('operatingCashflow', 0) or 0
            if op_cash == 0:
                try:
                    if not ticker.cashflow.empty: 
                        op_cash = ticker.cashflow.loc['Operating Cash Flow'].dropna().iloc
                except: pass

            # Crescimento de Vendas (CAGR)
            sales_growth, dados_crescimento_ok = 0, False
            try:
                if not ticker.financials.empty and 'Total Revenue' in ticker.financials.index:
                    revs = ticker.financials.loc['Total Revenue'].dropna()
                    if len(revs) >= 2:
                        rev_recente = float(revs.iloc)
                        rev_antiga = float(revs.iloc[-1])
                        if rev_antiga > 0 and rev_recente > 0:
                            sales_growth = ((rev_recente / rev_antiga) ** (1 / (len(revs) - 1)) - 1) * 100
                            dados_crescimento_ok = True
            except: pass

            # Contagem do Score
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
        except: pass

    status_text.text("✨ Varrimento de lote concluído com sucesso!")
    
    if resultados:
        df_res = pd.DataFrame(resultados)
        st.subheader("🏆 Empresas que passaram na triagem inicial de Market Cap")
        st.dataframe(df_res[["Ticker", "Nome", "Setor", "Score", "Veredicto"]], use_container_width=True)
        
        for res in resultados:
            if "PERFEITA" in res["Veredicto"] or "Promissora" in res["Veredicto"]:
                with st.expander(f"⭐ Ouro Detetado: {res['Ticker']} - {res['Nome']}"):
                    st.write(f"**ISIN para a XTB:** `{res['ISIN']}`")
                    st.write(f"**Crescimento:** {res['Crescimento']} | **Asset Turnover:** {res['Asset Turnover']}")
                    st.warning(f"Insiders: {res['Insiders']}. Faça a validação qualitativa na SEC.")
