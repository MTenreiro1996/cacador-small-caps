import yfinance as yf, pandas as pd, streamlit as st, requests

st.set_page_config(page_title="Screener Automático de Ações", layout="wide", page_icon="📈")
st.title("📈 Caçador de Ações: Screener Automático e Auditor de Hipercrescimento")
st.table(pd.DataFrame({"Filtro na XTB": ["País", "Capitalização de Mercado (Mínimo)", "Capitalização de Mercado (Máximo)", "Rácio actual", "P/E (Preço/Lucro)"], "Configuração": ["UNITED STATES", "300000000 (300M)", "Arrastar até '2.00 bn'", "Arrastar até 1.50", "Máximo em 30"]}))
st.info("🚨 Nota: Ignore indústrias de Biotecnologia, Farmacêuticas e Petróleo/Gás na XTB. Introduza o Ticker abaixo.")
st.markdown("---")
entrada_usuario = st.text_input("🎯 Introduza o Ticker ou o Código ISIN da XTB:", "").strip().upper()

def extrair_patentes_sec_edgar(ticker_simbolo):
    headers = {'User-Agent': "ScreenerCacadorOuro analise@quantinvestimentos.com"}
    try:
        res_cik = requests.get("https://sec.gov", headers=headers, timeout=5)
        if res_cik.status_code == 200:
            for val in res_cik.json().values():
                if val['ticker'].upper() == ticker_simbolo.upper():
                    cik_str = str(val['cik_str']).zfill(10)
                    sub_data = requests.get(f"https://sec.gov{cik_str}.json", headers=headers, timeout=5).json()
                    recent_filings = sub_data['filings']['recent']
                    for i, form in enumerate(recent_filings['form']):
                        if form == '10-K':
                            acc_num, doc_name = recent_filings['accessionNumber'][i].replace('-', ''), recent_filings['primaryDocument'][i]
                            texto_limpo = requests.get(f"https://sec.gov{cik_str}/{acc_num}/{doc_name}", headers=headers, timeout=8).text.lower()
                            count_patents, count_tech = texto_limpo.count("patents"), texto_limpo.count("proprietary technology")
                            if count_patents > 0 or count_tech > 0: return f"🎉 Fosso Validado! Encontradas {count_patents} referências a 'patents' e {count_tech} a 'proprietary technology' no Form 10-K da SEC."
                            return "⚠️ Alerta Qualitativo: O relatório anual 10-K não apresentou termos explícitos de patentes."
        return "⚠️ Não foi possível localizar o código CIK desta empresa nos servidores da SEC EDGAR."
    except Exception as e: return f"⚠️ Validação Qualitativa Interrompida: Servidor da SEC indisponível ({str(e)})."

if st.button("🔍 Iniciar Auditoria Avançada") and entrada_usuario:
    with st.spinner("A processar dados..."):
        ticker_final = entrada_usuario
        if len(entrada_usuario) == 12 and entrada_usuario.isalnum():
            try:
                obj_t = yf.Ticker(entrada_usuario)
                if obj_t.info and 'symbol' in obj_t.info: ticker_final = obj_t.info['symbol'].upper()
            except: pass
        try:
            ticker = yf.Ticker(ticker_final)
            info = ticker.info or {}
            if not info or 'marketCap' not in info: st.error("Erro: Não foram encontrados metadados financeiros estáveis para este Ticker.")
            else:
                nome_empresa, setor_gics, industria_gics, codigo_isin, market_cap = info.get('longName', 'Desconhecido'), info.get('sector', 'Desconhecido'), info.get('industry', 'Desconhecido'), info.get('isin', 'Não Disponível'), info.get('marketCap', 0)
                gross_margin_pct, ps_ratio, current_ratio, insider_ownership = info.get('grossMargins', 0.0) * 100, info.get('priceToSalesTrailing12Months', 999.0), info.get('currentRatio', 0.0), info.get('heldPercentInsiders', 0.0) * 100
                setor_proibido = (setor_gics in ["Biotechnology", "Pharmaceuticals", "Oil & Gas Exploration"]) or (industria_gics in ["Biotechnology", "Pharmaceuticals", "Oil & Gas Exploration"])
                asset_turnover = info.get('assetTurnover', 0.0) or 0.0
                if asset_turnover == 0.0 and not ticker.financials.empty and not ticker.balance_sheet.empty:
                    try: asset_turnover = float(ticker.financials.loc['Total Revenue'].dropna().iloc[0]) / float(ticker.balance_sheet.loc['Total Assets'].dropna().iloc[0])
                    except: asset_turnover = 0.0
                operating_cash_flow = info.get('operatingCashflow', 0) or 0
                if operating_cash_flow == 0 and not ticker.cashflow.empty and 'Operating Cash Flow' in ticker.cashflow.index:
                    try: operating_cash_flow = float(ticker.cashflow.loc['Operating Cash Flow'].dropna().iloc[0])
                    except: pass
                sales_growth_cagr, dados_crescimento_validos = 0.0, False
                if not ticker.financials.empty and 'Total Revenue' in ticker.financials.index:
                    try:
                        tabela_receitas = ticker.financials.loc['Total Revenue'].dropna()
                        if len(tabela_receitas) >= 4:
                            sales_growth_cagr = ((float(tabela_receitas.iloc[0]) / float(tabela_receitas.iloc[3])) ** (1/3) - 1) * 100
                            dados_crescimento_validos = True
                    except: pass
                pontos_score, motivos_chumbo = 0, []
                if 300000000 <= market_cap <= 2000000000: pontos_score += 1
                else: motivos_chumbo.append(f"Métrica 1 (Market Cap) Violada: \${market_cap:,.0f}")
                if dados_crescimento_validos and sales_growth_cagr >= 20.0: pontos_score += 1
                else: motivos_chumbo.append(f"Métrica 2 (Sales Growth) Violada: {sales_growth_cagr:.2f}%")
                if ps_ratio < 10.0: pontos_score += 1
                else: motivos_chumbo.append(f"Métrica 3 (P/S Ratio) Violada: {ps_ratio:.2f}")
                if gross_margin_pct >= 50.0: pontos_score += 1
                else: motivos_chumbo.append(f"Métrica 4 (Gross Margin) Violada: {gross_margin_pct:.2f}%")
                if asset_turnover > 0.4 and not setor_proibido: pontos_score += 1
                else:
                    if asset_turnover <= 0.4: motivos_chumbo.append(f"Métrica 5 (Asset Turnover) Violada: {asset_turnover:.2f}")
                    if setor_proibido: motivos_chumbo.append(f"Métrica 5 (Setor Proibido GICS): {setor_gics}")
                if current_ratio > 2.0: pontos_score += 1
                else: motivos_chumbo.append(f"Métrica 6 (Current Ratio) Violada: {current_ratio:.2f}")
                if operating_cash_flow > 0: pontos_score += 1
                else: motivos_chumbo.append(f"Métrica 7 (Operating Cash Flow) Violada: \${operating_cash_flow:,.2f}")
                veredicto_sec_final = "Análise Qualitativa bloqueada por falha nos filtros numéricos iniciais."
                if pontos_score >= 4 and not setor_proibido: veredicto_sec_final = extrair_patentes_sec_edgar(ticker_final)
                st.subheader(f"📊 Painel Visual do Ativo: {nome_empresa} ({ticker_final})")
                st.markdown(f"### Pontuação Quantitativa de Sobrevivência: {'⭐' * pontos_score} ({pontos_score}/7)")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Código ISIN Exato (Pesquisa XTB)", codigo_isin)
                    st.metric("Capitalização de Mercado (Market Cap)", f"\${market_cap:,.0f}")
                    st.metric("Rotação de Ativos (Asset Turnover)", f"{asset_turnover:.2f}")
                    st.metric("Rácio de Liquidez Corrente (Current Ratio)", f"{current_ratio:.2f}")
                with col2:
                    st.metric("Crescimento de Receitas (3Y CAGR)", f"{sales_growth_cagr:.2f}%" if dados_crescimento_validos else "Dados Incompletos")
                    st.metric("Margem Bruta (Gross Margin)", f"{gross_margin_pct:.2f}%")
                    st.metric("Rácio Price-to-Sales (P/S)", f"{ps_ratio:.2f}")
                    st.metric("Fluxo de Caixa Operacional", f"\${operating_cash_flow:,.2f}")
                st.markdown("---")
                st.subheader("📑 Veredicto do Robô sobre o Fosso Económico (SEC Edgar)")
                if "Fosso Validado" in veredicto_sec_final: st.success(veredicto_sec_final)
                else: st.warning(veredicto_sec_final)
                st.markdown("---")
                if setor_proibido: st.error(f"❌ REJEITADA DIRETAMENTE PELO FILTRO GICS ({setor_gics} / {industria_gics}).")
                elif pontos_score == 7: st.success("🎉 FUNIL CONCLUÍDO! Saúde financeira impecável.")
                elif pontos_score >= 5: st.warning("⚠️ PROMISSORA: Excelente, mas falhou em critérios secundários.")
                else: st.error("❌ REJEITADA: O ativo chumbou em critérios obrigatórios.")
                if motivos_chumbo:
                    st.markdown("#### Detalhes dos Critérios Não Cumpridos:")
                    for m in motivos_chumbo: st.write(f"- {m}")
                if pontos_score >= 4 and not setor_proibido:
                    st.markdown("---")
                    st.subheader("🚨 AVISO DE VALIDAÇÃO MANUAL OBRIGATÓRIA")
                    st.info(f"Confirme no Yahoo Finance: 1. Fator Fundador como CEO atual | 2. Insider Ownership > 10% (Atual: {insider_ownership:.2f}%).\n\n🎯 Compra na XTB com o ISIN: `{codigo_isin}`.")
        except Exception as e: st.error(f"Erro Crítico de Execução: {str(e)}")
