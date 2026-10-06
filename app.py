import yfinance as yf, pandas as pd, streamlit as st

st.set_page_config(page_title="Screener Automático", layout="wide", page_icon="📈")
st.title("📈 Caçador de Ações: Screener Automático de Hipercrescimento")

st.subheader("🛠️ PASSO 1: CONFIGURAÇÃO DE FILTROS NA XTB")
st.table(pd.DataFrame({"Filtro na XTB": ["País", "Capitalização", "Rácio actual", "P/E", "Margem de ganho"], "Configuração": ["UNITED STATES", "300.00 mn a 2.00 bn", "Mínimo: 1.50", "Máximo: 30", "Mínimo: 10"]}))
st.info("🚨 Ignorar indústrias de Biotechnology, Pharmaceuticals e Oil & Gas Exploration na XTB. Introduza o Ticker abaixo.")
st.markdown("---")

entrada_usuario = st.text_input("🎯 Digite o Ticker ou ISIN da XTB (Ex: AMSC, AFYA):", "").strip().upper()

if st.button("🔍 Iniciar Triagem") and entrada_usuario:
    with st.spinner("A processar dados em tempo real..."):
        ticker_final = entrada_usuario
        if len(entrada_usuario) == 12 and entrada_usuario.isalnum():
            try:
                obj_t = yf.Ticker(entrada_usuario)
                if obj_t.info and 'symbol' in obj_t.info: ticker_final = obj_t.info['symbol'].upper()
            except: pass
            
        try:
            ticker = yf.Ticker(ticker_final)
            info = ticker.info or {}
            
            if not info or 'marketCap' not in info:
                st.error("Erro: Não foram encontrados dados para este Ticker. Verifique a escrita.")
            else:
                nome_empresa, setor_gics, industria_gics, codigo_isin = info.get('longName', 'Desconhecido'), info.get('sector', 'Desconhecido'), info.get('industry', 'Desconhecido'), info.get('isin', 'Não Disponível')
                market_cap, gross_margin_pct = info.get('marketCap', 0), info.get('grossMargins', 0.0) * 100
                net_margin_pct, ps_ratio, current_ratio = info.get('profitMargins', 0.0) * 100, info.get('priceToSalesTrailing12Months', 999.0), info.get('currentRatio', 0.0)
                insider_ownership = info.get('heldPercentInsiders', 0.0) * 100

                setor_proibido = any(x in [setor_gics, industria_gics] for x in ["Biotechnology", "Pharmaceuticals", "Oil & Gas Exploration"])

                asset_turnover = info.get('assetTurnover', 0.0) or 0.0
                if asset_turnover == 0.0 and not ticker.financials.empty and not ticker.balance_sheet.empty:
                    try: asset_turnover = float(ticker.financials.loc['Total Revenue'].dropna().values[0]) / float(ticker.balance_sheet.loc['Total Assets'].dropna().values[0])
                    except: asset_turnover = 0.0

                operating_cash_flow = info.get('operatingCashflow', 0) or 0
                if operating_cash_flow == 0 and not ticker.cashflow.empty and 'Operating Cash Flow' in ticker.cashflow.index:
                    try: operating_cash_flow = float(ticker.cashflow.loc['Operating Cash Flow'].dropna().values[0])
                    except: pass

                sales_growth_cagr, dados_crescimento_ok = 0.0, False
                if not ticker.financials.empty and 'Total Revenue' in ticker.financials.index:
                    try:
                        tabela_receitas = ticker.financials.loc['Total Revenue'].dropna()
                        if len(tabela_receitas) >= 4:
                            sales_growth_cagr = ((float(tabela_receitas.values[0]) / float(tabela_receitas.values[3])) ** (1/3) - 1) * 100
                            dados_crescimento_ok = True
                    except: pass

                pontos_score, motivos_chumbo = 0, []
                if 300000000 <= market_cap <= 2000000000: pontos_score += 1
                else: motivos_chumbo.append(f"Métrica 1 (Market Cap) Violada: \${market_cap:,.0f}")
                if dados_crescimento_ok and sales_growth_cagr >= 20.0: pontos_score += 1
                else: motivos_chumbo.append(f"Métrica 2 (Sales Growth 3Y CAGR) abaixo de 20%: {sales_growth_cagr:.2f}%")
                if ps_ratio < 10.0: pontos_score += 1
                else: motivos_chumbo.append(f"Métrica 3 (P/S Ratio) em bolha (>10): {ps_ratio:.2f}")
                if gross_margin_pct >= 50.0: pontos_score += 1
                else: motivos_chumbo.append(f"Métrica 4 (Gross Margin) abaixo de 50%: {gross_margin_pct:.2f}%")
                if asset_turnover > 0.4 and not setor_proibido: pontos_score += 1
                else:
                    if asset_turnover <= 0.4: motivos_chumbo.append(f"Métrica 5 (Asset Turnover) abaixo de 0.4: {asset_turnover:.2f}")
                    if setor_proibido: motivos_chumbo.append(f"Métrica 5 (Setor Proibido GICS): {setor_gics}")
                if current_ratio > 2.0: pontos_score += 1
                else: motivos_chumbo.append(f"Métrica 6 (Current Ratio) abaixo de 2.0: {current_ratio:.2f}")
                if operating_cash_flow > 0: pontos_score += 1
                else: motivos_chumbo.append(f"Métrica 7 (Operating Cash Flow) Negativo ou Zero: \${operating_cash_flow:,.2f}")
                if net_margin_pct >= 10.0: pontos_score += 1
                else: motivos_chumbo.append(f"Filtro XTB (Margem de Ganho) abaixo de 10%: {net_margin_pct:.2f}%")

                st.subheader(f"📊 Painel Visual: {nome_empresa} ({ticker_final})")
                st.markdown(f"### Pontuação Quantitativa: {'⭐' * pontos_score} ({pontos_score}/8)")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Código ISIN Exato (XTB)", codigo_isin)
                    st.metric("Capitalização de Mercado (Market Cap)", f"\${market_cap:,.0f}")
                    st.metric("Rotação de Ativos (Asset Turnover)", f"{asset_turnover:.2f}")
                    st.metric("Rácio de Liquidez Corrente (Current Ratio)", f"{current_ratio:.2f}")
                with col2:
                    st.metric("Crescimento de Receitas (3Y CAGR)", f"{sales_growth_cagr:.2f}%" if dados_crescimento_ok else "Dados Incompletos")
                    st.metric("Margem Bruta (Gross Margin)", f"{gross_margin_pct:.2f}%")
                    st.metric("Margem de Ganho Líquida (XTB)", f"{net_margin_pct:.2f}%")
                    st.metric("Rácio Price-to-Sales (P/S)", f"{ps_ratio:.2f}")

                st.markdown("---")
                st.subheader("📑 Veredicto do Robô sobre o Fosso Económico (SEC EDGAR)")
                url_sec = f"https://sec.gov{ticker_final}"
                st.warning(f"🔗 [Clique aqui para abrir a SEC EDGAR de forma direta e gratuita]({url_sec}). Abra o Form 10-K mais recente e pressione Ctrl+F por 'patent' para validar as patentes.")

                st.markdown("---")
                if setor_proibido: st.error(f"❌ REJEITADA DIRETAMENTE PELO FILTRO GICS: Indústria proibida ({setor_gics} / {industria_gics}).")
                elif pontos_score == 8: st.success("🎉 FUNIL INTEGRAL CONCLUÍDO! Saúde financeira impecável.")
                elif pontos_score >= 5: st.warning("⚠️ PROMISSORA: Excelente, mas falhou nalguns rácios secundários.")
                else: st.error("❌ REJEITADA: O ativo chumbou em critérios obrigatórios de sobrevivência.")

                if motivos_chumbo:
                    st.markdown("#### Detalhes dos Critérios Não Cumpridos:")
                    for m in motivos_chumbo: st.write(f"- {m}")

                if pontos_score >= 4 and not setor_proibido:
                    st.markdown("---")
                    st.subheader("🚨 AVISO DE VALIDAÇÃO MANUAL OBRIGATÓRIA")
                    st.info(f"Confirme no Yahoo Finance: 1. Fator Fundador como CEO atual | 2. Insider Ownership > 10% (Atualmente em: {insider_ownership:.2f}%).\n\n🎯 Compre na XTB com o ISIN: `{codigo_isin}`.")
        except Exception as e: st.error(f"Erro Crítico: {str(e)}")
