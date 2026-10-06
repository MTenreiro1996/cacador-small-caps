import yfinance as yf
import pandas as pd
import streamlit as st

# Configuração da página do Streamlit
st.set_page_config(page_title="Caçador Mestre de Small Caps", layout="wide", page_icon="📈")
st.title("📈 Caçador de Ações: Varrimento Autónomo do Mercado Total")

# === PASSO 1: CONFIGURAÇÃO DE FILTROS NA XTB ===
st.subheader("🛠️ PASSO 1: CONFIGURAÇÃO DE FILTROS NA XTB (xStation)")
dados_xtb = {
    "Filtro na XTB": ["País", "Capitalização de Mercado (Mínimo)", "Capitalização de Mercado (Máximo)", "Rácio actual", "P/E (Preço/Lucro)"],
    "Nome Técnico na xStation": ["Todos os países", "Capitalização de mercado (Esquerda)", "Capitalização de mercado (Direita)", "Rácio actual (Esquerda)", "P/E (Direita)"],
    "O que Escrever ou Arrastar": ["Mudar para 'UNITED STATES'", "Digite: 300000000 (300M)", "Arrastar até ler '2.00 bn'", "Arrastar até 1.50", "Definir máximo em 30"],
    "Objetivo Real": ["Isolar mercado EUA", "Filtro Small Caps", "Teto máximo Small Caps", "Anti-Falência Corrente", "Substituto do filtro P/S"]
}
st.table(pd.DataFrame(dados_xtb))
st.info("🚨 Nota: Desative os filtros de EPS, ROE ou ROIC na XTB arrastando os cursores para os máximos. Cole os sobreviventes abaixo.")
st.markdown("---")

# === PASSO 2: A CAIXA DE TRIAGEM DO ROBÔ ===
st.subheader("🤖 PASSO 2: AUDITORIA PROFUNDA DO ROBÔ PYTHON")
ativo_introduzido = st.text_input("🎯 Digite o Ticker ou o código ISIN da XTB:", "").strip().upper()

def buscar_ticker_por_isin(isin_code):
    if len(isin_code) == 12 and isin_code.isalnum():
        try:
            ticker_obj = yf.Ticker(isin_code)
            if ticker_obj.info and 'symbol' in ticker_obj.info:
                return ticker_obj.info['symbol']
        except: pass
    return isin_code

if st.button("🔍 Iniciar Triagem do Ativo"):
    if not ativo_introduzido:
        st.error("Por favor, digite um Ticker ou ISIN válido.")
    else:
        with st.spinner("A conectar aos servidores financeiros em tempo real..."):
            ticker_resolvido = buscar_ticker_por_isin(ativo_introduzido)
            try:
                ticker = yf.Ticker(ticker_resolvido)
                try: info = ticker.info
                except Exception: info = None
                
                if not info or 'marketCap' not in info:
                    st.error(f"⚠️ Servidor Temporariamente Instável. Tente novamente ou verifique diretamente na XTB.")
                else:
                    nome = info.get('longName', 'Desconhecido')
                    setor = info.get('sector', 'Desconhecido')
                    industry = info.get('industry', 'Desconhecido')
                    isin = info.get('isin', 'Não disponível')
                    exchange = info.get('exchange', 'EUA')
                    market_cap = info.get('marketCap', 0)
                    gross_margin = info.get('grossMargins', 0) * 100
                    ps_ratio = info.get('priceToSalesTrailing12Months', 999)
                    current_ratio = info.get('currentRatio', 0)
                    insider_ownership = info.get('heldPercentInsiders', 0) * 100 if info.get('heldPercentInsiders') else 0.0
                    # === CORREÇÃO TÉCNICA E SEGURA DO ASSET TURNOVER ===
                    asset_turnover = info.get('assetTurnover', 0.0)
                    if asset_turnover == 0.0 or asset_turnover is None:
                        total_revenue = info.get('totalRevenue', 0)
                        total_assets = info.get('totalAssets', 0)
                        asset_turnover = total_revenue / total_assets if total_assets > 0 else 0.0
                    
                    # === CAPTURA BLINDADA DO FLUXO DE CAIXA ===
                    operating_cash_flow = 0
                    dados_caixa_disponiveis = True
                    try:
                        cashflow = ticker.cashflow
                        if not cashflow.empty and 'Operating Cash Flow' in cashflow.index:
                            operating_cash_flow = float(cashflow.loc['Operating Cash Flow'].iloc[0])
                        else: operating_cash_flow = float(info.get('operatingCashflow', 0))
                    except Exception:
                        operating_cash_flow = float(info.get('operatingCashflow', 0))
                        if operating_cash_flow == 0: dados_caixa_disponiveis = False
                    
                    # === CAPTURA BLINDADA DO CRESCIMENTO DE VENDAS ===
                    sales_growth = 0
                    dados_crescimento_disponiveis = True
                    try:
                        financials = ticker.financials
                        if not financials.empty and 'Total Revenue' in financials.index:
                            revenues = financials.loc['Total Revenue']
                            if len(revenues) >= 4:
                                sales_growth = ((float(revenues.iloc[0]) / float(revenues.iloc[3])) ** (1/3) - 1) * 100
                            else: dados_crescimento_disponiveis = False
                        else: dados_crescimento_disponiveis = False
                    except Exception: dados_crescimento_disponiveis = False

                    # === NOVO SISTEMA DE PONTUAÇÃO (SCORE) FLEXÍVEL ===
                    pontos, total_filtros, motivos = 0, 7, []
                    
                    if (300_000_000 <= market_cap <= 2_000_000_000): pontos += 1
                    else: motivos.append(f"Market Cap fora do limite Small Cap: \${market_cap:,}")
                        
                    if dados_crescimento_disponiveis:
                        if sales_growth >= 20: pontos += 1
                        else: motivos.append(f"Sales Growth 3Y CAGR abaixo de 20%: {sales_growth:.2f}%")
                    else: motivos.append("Sales Growth 3Y CAGR: Dados indisponíveis no Yahoo de momento (Validar Manualmente)")
                        
                    if ps_ratio <= 10: pontos += 1
                    else: motivos.append(f"P/S Ratio superior a 10 (Caro/Bolha): {ps_ratio:.2f}")
                        
                    if gross_margin >= 50: pontos += 1
                    else: motivos.append(f"Margem Bruta abaixo de 50%: {gross_margin:.2f}%")
                        
                    if asset_turnover >= 0.4: pontos += 1
                    else: motivos.append(f"Asset Turnover abaixo de 0.4: {asset_turnover:.2f}")
                        
                    if current_ratio >= 1.5: pontos += 1
                    else: motivos.append(f"Current Ratio abaixo de 1.5: {current_ratio:.2f}")
                        
                    if dados_caixa_disponiveis:
                        if operating_cash_flow > 0: pontos += 1
                        else: motivos.append(f"Operating Cash Flow Negativo: \${operating_cash_flow:,}")
                    else: motivos.append("Operating Cash Flow: Dados indisponíveis no Yahoo de momento (Validar Manualmente)")
                        
                    setor_proibido = setor in ["Biotechnology", "Pharmaceuticals"] or "Oil & Gas Exploration" in industry or "Oil & Gas" in setor
                    if setor_proibido: motivos.append(f"Setor proibido GICS: {setor} ({industry})")

                    # === RENDERIZAÇÃO DOS RESULTADOS VISUAIS ===
                    st.subheader(f"📊 Relatório de Auditoria: {nome} ({ticker_resolvido})")
                    st.markdown(f"### Pontuação de Sobrevivência: {'⭐' * pontos} ({pontos}/{total_filtros})")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("ISIN Exato (XTB)", isin)
                        st.metric("Mercado / Bolsa", exchange)
                        st.metric("Setor GICS", setor)
                        st.metric("Market Cap", f"\${market_cap:,}")
                        st.metric("Asset Turnover (Calculado)", f"{asset_turnover:.2f}")
                    with col2:
                        st.metric("Sales Growth (3Y CAGR)", f"{sales_growth:.2f}%" if dados_crescimento_disponiveis else "N/D")
                        st.metric("Margem Bruta", f"{gross_margin:.2f}%")
                        st.metric("P/S Ratio (Preço)", f"{ps_ratio:.2f}")
                        st.metric("Current Ratio (Liquidez)", f"{current_ratio:.2f}")
                        st.metric("Insider Ownership (Python)", f"{insider_ownership:.2f}%")

                    st.markdown("---")

                    if setor_proibido: st.error(f"❌ REJEITADA TOTALMENTE: Pertence a um setor proibido pela estratégia ({setor}).")
                    elif pontos == total_filtros: st.success("🎉 PONTUAÇÃO PERFEITA! Cumpre 100% dos critérios matemáticos.")
                    elif pontos >= 5: st.warning(f"⚠️ PROMISSORA ({pontos}/{total_filtros}): Forte, mas com falhas menores.")
                    else: st.error(f"❌ REJEITADA PELO ALGORITMO: Violou critérios a mais ({pontos}/{total_filtros}).")

                    if motivos:
                        st.markdown("#### Detalhes observados pelo funil:")
                        for m in motivos: st.write(f"- {m}")

                    if pontos >= 5 and not setor_proibido:
                        st.subheader("⚠️ VALIDAÇÃO MANUAL OBRIGATÓRIA")
                        st.warning(f"Insider Ownership: {insider_ownership:.2f}%. Procure pelo Form 10-K e valide se o fundador é o CEO.")
                        st.markdown(f"🎯 **Compra na XTB:** Use o ISIN `{isin}`.")
            except Exception as e:
                st.error(f"Erro na triagem: {str(e)}")
