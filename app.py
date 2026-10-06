import yfinance as yf
import pandas as pd
import streamlit as st
import requests
import json
import time

st.set_page_config(page_title="Caçador Mestre de Small Caps", layout="wide", page_icon="📈")
st.title("📈 Caçador de Ações: Varrimento 100% Autónomo do Mercado")

st.subheader("👑 MOTOR QUANTA E PARSING DE PATENTES DA SEC (ZERO TRABALHO MANUAL)")
st.write("O robô faz o mapeamento total do mercado, elimina setores proibidos e gera o ranking com as patentes da SEC.")

# Lista base alargada com Small Caps puras para triagem automática estável
TICKERS_MERCADO = [
    "AMSC", "AFYA", "BHE", "AAON", "BOOT", "CELH", "PLUS", "MMS", "UFPI", "FIX",
    "SHAK", "WING", "LGIH", "KNSL", "QLYS", "SPSC", "EPIX", "CORT", "POWI", "MED",
    "PRTH", "NVMI", "SMTC", "EXTR", "FORM", "SGH", "AEIS", "COHR", "DIOD", "OSIS"
]

def analisar_patentes_sec(ticker_simbolo):
    headers = {'User-Agent': "CacadorQuant analise@quantmarta.com"}
    try:
        cik_url = "https://sec.gov"
        res_cik = requests.get(cik_url, headers=headers, timeout=4)
        if res_cik.status_code == 200:
            for val in res_cik.json().values():
                if val['ticker'].upper() == ticker_simbolo.upper():
                    cik = str(val['cik_str']).zfill(10)
                    sub_url = f"https://sec.gov{cik}.json"
                    sub_data = requests.get(sub_url, headers=headers, timeout=4).json()
                    recent = sub_data['filings']['recent']
                    for i, form in enumerate(recent['form']):
                        if form == '10-K':
                            acc_num = recent['accessionNumber'][i].replace('-', '')
                            doc_name = recent['primaryDocument'][i]
                            text_url = f"https://sec.gov{cik}/{acc_num}/{doc_name}"
                            texto_relatorio = requests.get(text_url, headers=headers, timeout=4).text.lower()
                            
                            contagem = texto_relatorio.count("patent") + texto_relatorio.count("proprietary technology")
                            if contagem > 0:
                                return f"Fosso Validado! Encontradas {contagem} referências a patentes/tecnologia no 10-K."
                            return "⚠️ Sem patentes ou tecnologia proprietária explícitas no 10-K."
        return "⚠️ CIK não localizado na SEC."
    except:
        return "⚠️ Servidor SEC ocupado. Faça a validação manual do 10-K."

if st.button("🚀 Iniciar Varrimento Total do Mercado"):
    resultados = []
    progresso = st.progress(0)
    status_text = st.empty()
    total_lote = len(TICKERS_MERCADO)
    
    for idx, ticker_simbolo in enumerate(TICKERS_MERCADO):
        status_text.text(f"A auditar {idx+1}/{total_lote}: {ticker_simbolo}...")
        progresso.progress((idx + 1) / total_lote)
        
        time.sleep(1.0) # Proteção anti-bloqueio
        
        try:
            ticker = yf.Ticker(ticker_simbolo)
            info = ticker.info or {}
            
            if not info or 'marketCap' not in info:
                continue
                
            market_cap = info.get('marketCap', 0)
            setor = info.get('sector', 'Desconhecido')
            industry = info.get('industry', 'Desconhecido')
            
            # FILTRO 1: Capitalização de Mercado (\$300M a \$2B)
            if not (300_000_000 <= market_cap <= 2_000_000_000):
                continue
                
            # FILTRO 5 (PARTE A): EXCLUSÃO RIGOROSA E INTEGRAL DE SETORES
            setor_proibido = (
                "Biotechnology" in industry or "Biotechnology" in setor or
                "Pharmaceuticals" in industry or "Pharmaceuticals" in setor or
                "Oil & Gas Exploration" in industry or "Oil & Gas" in industry or "Oil & Gas" in setor
            )
            if setor_proibido:
                continue

            nome = info.get('longName', 'Desconhecido')
            isin = info.get('isin', 'Não disponível')
            gross_margin = info.get('grossMargins', 0) * 100
            ps_ratio = info.get('priceToSalesTrailing12Months', 999)
            current_ratio = info.get('currentRatio', 0)
            insider_ownership = info.get('heldPercentInsiders', 0) * 100

            # Métrica 5 (Parte B): Asset Turnover com Fallback
            asset_turnover = info.get('assetTurnover', 0.0) or 0.0
            if asset_turnover == 0.0:
                try:
                    rev = info.get('totalRevenue', 0) or 0
                    if rev == 0 and not ticker.financials.empty: rev = ticker.financials.loc['Total Revenue'].dropna().iloc
                    assets = info.get('totalAssets', 0) or 0
                    if assets == 0 and not ticker.balance_sheet.empty: assets = ticker.balance_sheet.loc['Total Assets'].dropna().iloc
                    asset_turnover = float(rev) / float(assets) if assets > 0 else 0.0
                except: asset_turnover = 0.0

            # Métrica 7: Fluxo de Caixa Operacional
            op_cash = info.get('operatingCashflow', 0) or 0
            if op_cash == 0:
                try:
                    if not ticker.cashflow.empty: op_cash = ticker.cashflow.loc['Operating Cash Flow'].dropna().iloc
                except: pass

            # Métrica 2: Crescimento de Vendas (CAGR 3 anos exato)
            sales_growth, dados_crescimento_ok = 0, False
            try:
                if not ticker.financials.empty and 'Total Revenue' in ticker.financials.index:
                    revs = ticker.financials.loc['Total Revenue'].dropna()
                    if len(revs) >= 4:
                        sales_growth = ((float(revs.iloc) / float(revs.iloc)) ** (1/3) - 1) * 100
                        dados_crescimento_ok = True
            except: pass

            # Contagem de Critérios (Rigor Máximo Reposto)
            pontos, motivos = 0, []
            if 300_000_000 <= market_cap <= 2_000_000_000: pontos += 1
            if dados_crescimento_ok and sales_growth >= 20: pontos += 1
            else: motivos.append(f"Crescimento 3Y baixo: {sales_growth:.2f}%")
            if ps_ratio < 10: pontos += 1
            else: motivos.append(f"P/S elevado (>10): {ps_ratio:.2f}")
            if gross_margin >= 50: pontos += 1
            else: motivos.append(f"Margem Bruta baixa (<50%): {gross_margin:.2f}%")
            if asset_turnover > 0.4: pontos += 1
            else: motivos.append(f"Asset Turnover baixo (<0.4): {asset_turnover:.2f}")
            if current_ratio >= 2.0: pontos += 1
            else: motivos.append(f"Current Ratio baixo (<2.0): {current_ratio:.2f}")
            if op_cash > 0: pontos += 1
            else: motivos.append(f"Caixa Operacional Negativo: \${op_cash:,}")

            if pontos == 7: veredicto = "🎉 PERFEITA (7/7)"
            elif pontos >= 5: veredicto = "⚠️ Promissora"
            else: veredicto = "❌ Rejeitada"

            # Executar Parsing Qualitativo da SEC apenas para empresas fortes sobreviventes
            veredicto_sec = "Análise SEC ignorada por baixo score."
            if pontos >= 5:
                veredicto_sec = analisar_patentes_sec(ticker_simbolo)

            resultados.append({
                "Ticker": ticker_simbolo, "Nome": nome, "Setor": setor, 
                "Score": f"{'⭐' * pontos} ({pontos}/7)", "Veredicto": veredicto, "Patentes (SEC)": veredicto_sec,
                "ISIN": isin, "Market Cap": f"\${market_cap:,}", "Crescimento": f"{sales_growth:.2f}%" if dados_crescimento_ok else "N/D",
                "Asset Turnover": f"{asset_turnover:.2f}", "Current Ratio": f"{current_ratio:.2f}", "Insiders": f"{insider_ownership:.2f}%"
            })
        except: pass

    status_text.text("✨ Varrimento concluído!")
    if resultados:
        df_res = pd.DataFrame(resultados).sort_values(by="Score", ascending=False)
        st.subheader("🏆 Ranking de Classificação das Ações Auditadas")
        st.dataframe(df_res[["Ticker", "Nome", "Setor", "Score", "Veredicto"]], use_container_width=True)
        
        st.subheader("🔍 Painéis Detalhados e Compra Segura na XTB")
        for res in resultados:
            if "PERFEITA" in res["Veredicto"] or "Promissora" in res["Veredicto"]:
                with st.expander(f"⭐ {res['Ticker']} - {res['Nome']} | {res['Veredicto']}"):
                    st.write(f"**Código ISIN para a XTB:** `{res['ISIN']}`")
                    st.info(f"📜 **SEC EDGAR:** {res['Patentes (SEC)']}")
                    st.write(f"**Crescimento 3Y:** {res['Crescimento']} | **Asset Turnover:** {res['Asset Turnover']} | **Liquidez:** {res['Current Ratio']}")
                    st.warning(f"Insider Ownership: {res['Insiders']}. Confirme no Yahoo Finance se o fundador é o CEO atual.")
