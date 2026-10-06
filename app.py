import yfinance as yf
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Caçador Mestre de Small Caps", layout="wide", page_icon="📈")
st.title("📈 Caçador de Ações: Varrimento Autónomo do Mercado Total")

st.subheader("🛠️ PASSO 1: CONFIGURAÇÃO DE FILTROS NA XTB")
dados_xtb = {
    "Filtro na XTB": ["País", "Capitalização de Mercado (Mínimo)", "Capitalização de Mercado (Máximo)", "Rácio actual", "P/E (Preço/Lucro)"],
    "Nome Técnico": ["Todos os países", "Capitalização de mercado (Esq)", "Capitalização de mercado (Dir)", "Rácio actual (Esq)", "P/E (Dir)"],
    "Configuração": ["UNITED STATES", "300000000 (300M)", "Arrastar até '2.00 bn'", "Arrastar até 1.50", "Máximo em 30"]
}
st.table(pd.DataFrame(dados_xtb))
st.info("🚨 Nota: Ignore ou limpe EPS, ROE e ROIC na XTB (cursores nos máximos). Use os Tickers abaixo.")
st.markdown("---")

st.subheader("🤖 PASSO 2: AUDITORIA PROFUNDA DO ROBÔ PYTHON")
ativo_introduzido = st.text_input("🎯 Digite o Ticker ou ISIN da XTB:", "").strip().upper()

if st.button("🔍 Iniciar Triagem do Ativo") and ativo_introduzido:
    with st.spinner("A conectar aos servidores financeiros..."):
        ticker_resolvido = ativo_introduzido
        if len(ativo_introduzido) == 12:
            try:
                t_obj = yf.Ticker(ativo_introduzido)
                if t_obj.info and 'symbol' in t_obj.info: ticker_resolvido = t_obj.info['symbol']
            except: pass

        try:
            ticker = yf.Ticker(ticker_resolvido)
            info = ticker.info or {}
            
            if not info or 'marketCap' not in info:
                st.error("⚠️ Erro: Não foi possível obter dados para este Ticker. Tente novamente.")
            else:
                nome = info.get('longName', 'Desconhecido')
                setor = info.get('sector', 'Desconhecido')
                industry = info.get('industry', 'Desconhecido')
                isin = info.get('isin', 'Não disponível')
                market_cap = info.get('marketCap', 0)
                gross_margin = info.get('grossMargins', 0) * 100
                ps_ratio = info.get('priceToSalesTrailing12Months', 999)
                current_ratio = info.get('currentRatio', 0)
                insider_ownership = info.get('heldPercentInsiders', 0) * 100

                # === CÁCULO ROBUSTO DO ASSET TURNOVER ===
                asset_turnover = info.get('assetTurnover', 0.0) or 0.0
                if asset_turnover == 0.0:
                    try:
                        rev = info.get('totalRevenue', 0) or 0
                        if rev == 0 and not ticker.financials.empty:
                            rev = ticker.financials.loc['Total Revenue'].iloc[0]
                        assets = info.get('totalAssets', 0) or 0
                        if assets == 0 and not ticker.balance_sheet.empty:
                            assets = ticker.balance_sheet.loc['Total Assets'].iloc[0]
                        asset_turnover = float(rev) / float(assets) if assets > 0 else 0.0
                    except: asset_turnover = 0.0

                # === CAPTURA DO FLUXO DE CAIXA OPERACIONAL ===
                op_cash = info.get('operatingCashflow', 0) or 0
                if op_cash == 0:
                    try:
                        if not ticker.cashflow.empty: op_cash = ticker.cashflow.loc['Operating Cash Flow'].iloc[0]
                    except: pass

                # === CÁLCULO DO CRESCIMENTO DE VENDAS (CAGR) ===
                sales_growth = 0
                try:
                    if not ticker.financials.empty and 'Total Revenue' in ticker.financials.index:
                        revs = ticker.financials.loc['Total Revenue']
                        sales_growth = ((float(revs.iloc[0]) / float(revs.iloc[-1])) ** (1 / (len(revs) - 1)) - 1) * 100
                except: sales_growth = 0

                # === CONTROLO E FILTROS ===
                pontos, motivos = 0, []
                if 300_000_000 <= market_cap <= 2_000_000_000: pontos += 1
                else: motivos.append(f"Market Cap fora do limite Small Cap: \${market_cap:,}")
                if sales_growth >= 20: pontos += 1
                else: motivos.append(f"Sales Growth 3Y CAGR abaixo de 20%: {sales_growth:.2f}%")
                if ps_ratio <= 10: pontos += 1
                else: motivos.append(f"P/S Ratio superior a 10: {ps_ratio:.2f}")
                if gross_margin >= 50: pontos += 1
                else: motivos.append(f"Margem Bruta abaixo de 50%: {gross_margin:.2f}%")
                if asset_turnover >= 0.4: pontos += 1
                else: motivos.append(f"Asset Turnover abaixo de 0.4: {asset_turnover:.2f}")
                if current_ratio >= 1.5: pontos += 1
                else: motivos.append(f"Current Ratio abaixo de 1.5: {current_ratio:.2f}")
                if op_cash > 0: pontos += 1
                else: motivos.append(f"Operating Cash Flow Negativo ou a Zero: \${op_cash:,}")
                
                setor_proibido = setor in ["Biotechnology", "Pharmaceuticals"] or "Oil & Gas" in industry or "Oil & Gas" in setor
                if setor_proibido: motivos.append(f"Setor proibido GICS: {setor} ({industry})")

                # === DESIGN E OUTPUT ===
                st.subheader(f"📊 Auditoria: {nome} ({ticker_resolvido})")
                st.markdown(f"### Pontuação de Sobrevivência: {'⭐' * pontos} ({pontos}/7)")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("ISIN (XTB)", isin)
                    st.metric("Setor GICS", setor)
                    st.metric("Market Cap", f"\${market_cap:,}")
                    st.metric("Asset Turnover", f"{asset_turnover:.2f}")
                with col2:
                    st.metric("Sales Growth (CAGR)", f"{sales_growth:.2f}%")
                    st.metric("Margem Bruta", f"{gross_margin:.2f}%")
                    st.metric("P/S Ratio", f"{ps_ratio:.2f}")
                    st.metric("Current Ratio", f"{current_ratio:.2f}")

                st.markdown("---")
                if setor_proibido: st.error(f"❌ REJEITADA: Setor Proibido ({setor}).")
                elif pontos == 7: st.success("🎉 PONTUAÇÃO PERFEITA! Passou em todos os critérios.")
                elif pontos >= 5: st.warning(f"⚠️ PROMISSORA ({pontos}/7): Empresa forte, veja os pontos falhados abaixo.")
                else: st.error(f"❌ REJEITADA: Falhou demasiados critérios ({pontos}/7).")

                if motivos:
                    for m in motivos: st.write(f"- {m}")
                if pontos >= 5 and not setor_proibido:
                    st.warning(f"Insiders detêm {insider_ownership:.2f}%. Vá ao Form 10-K na SEC validar as patentes e o Fundador/CEO.")
        except Exception as e:
            st.error(f"Erro ao ler o Ticker: {str(e)}. Tente novamente.")
