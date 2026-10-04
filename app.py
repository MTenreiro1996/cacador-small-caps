import yfinance as yf
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Caçador Mestre de Small Caps", layout="wide", page_icon="📈")

st.title("📈 Caçador de Ações: Varrimento Autónomo do Mercado Total")

# === MANUAL RETIFICADO E ALINHADO COM A XTB ===
st.subheader("🛠️ PASSO 1: CONFIGURAÇÃO DE FILTROS NA XTB (xStation)")
st.write("Antes de usar o robô, abra a XTB ➔ Análise de Mercado ➔ Stock Screener ➔ Clique em 'MOSTRAR MAIS FILTROS' e configure exatamente assim:")

dados_xtb = {
    "Filtro na XTB": ["País", "Capitalização de Mercado (Mínimo)", "Capitalização de Mercado (Máximo)", "Margem de ganho", "Rácio actual", "Nota sobre o Preço (P/S)"],
    "Nome Técnico na xStation": ["Todos os países", "Capitalização de mercado (Esquerda)", "Capitalização de mercado (Direita)", "Margem de ganho (Esquerda)", "Rácio actual (Esquerda)", "--- Não Aplicar no Screener ---"],
    "O que Escrever ou Arrastar": ["Mudar para 'UNITED STATES'", "Digite apenas números: 300000000 (300M)", "Digite apenas números: 2000000000 (2B)", "Arrastar bola até 50.0", "Arrastar bola até 2.0", "Deixe o filtro em branco na XTB. O robô Python calcula o P/S sozinho."],
    "Objetivo Real": ["Isolar mercado EUA", "Filtro Small Caps", "Teto máximo Small Caps", "Poder de Preço (>50%)", "Anti-Falência Corrente (>2.0)", "O robô barra bolhas (P/S > 10) automaticamente."]
}
st.table(pd.DataFrame(dados_xtb))

st.info("🚨 **Nota de Exclusão Direta na XTB:** Olhe para as empresas que a XTB listou e ignore imediatamente as indústrias de Biotecnologia, Farmacêuticas e Petróleo/Gás. Agarre nos sobreviventes e use a caixa abaixo.")

st.markdown("---")

# === PASSO 2: A CAIXA DE TRIAGEM DO ROBÔ ===
st.subheader("🤖 PASSO 2: AUDITORIA PROFUNDA DO ROBÔ PYTHON")
ativo_introduzido = st.text_input("🎯 Digite o Ticker (ex: CELH, PLTR, UPST) ou o código ISIN da XTB encontrado na lista:", "").strip().upper()

def buscar_ticker_por_isin(isin_code):
    if len(isin_code) == 12 and isin_code.isalnum():
        try:
            ticker_obj = yf.Ticker(isin_code)
            if ticker_obj.info and 'symbol' in ticker_obj.info:
                return ticker_obj.info['symbol']
        except:
            pass
    return isin_code

if st.button("🔍 Iniciar Triagem do Ativo"):
    if not ativo_introduzido:
        st.error("Por favor, digite um Ticker ou ISIN válido.")
    else:
        with st.spinner("O robô está a ligar-se diretamente às bolsas NYSE/NASDAQ em tempo real..."):
            ticker_resolvido = buscar_ticker_por_isin(ativo_introduzido)
            
            try:
                ticker = yf.Ticker(ticker_resolvido)
                info = ticker.info
                
                if not info or 'marketCap' not in info:
                    st.error(f"Erro: Não foram encontrados dados para o ativo '{ticker_resolvido}'.")
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
                    asset_turnover = info.get('assetTurnover', 0)
                    
                    insider_ownership = info.get('heldPercentInsiders', 0) * 100 if info.get('heldPercentInsiders') else 0.0
                    
                    cashflow = ticker.cashflow
                    if not cashflow.empty and 'Operating Cash Flow' in cashflow.index:
                        operating_cash_flow = float(cashflow.loc['Operating Cash Flow'].iloc[0])
                    else:
                        operating_cash_flow = float(info.get('operatingCashflow', 0))
                    
                    financials = ticker.financials
                    sales_growth = 0
                    if not financials.empty and 'Total Revenue' in financials.index:
                        revenues = financials.loc['Total Revenue']
                        if len(revenues) >= 4:
                            rev_recente = float(revenues.iloc[0])
                            rev_antiga = float(revenues.iloc[3])
                            if rev_antiga > 0:
                                sales_growth = ((rev_recente / rev_antiga) ** (1/3) - 1) * 100

                    motivos_rejeicao = []
                    if not (300_000_000 <= market_cap <= 2_000_000_000):
                        motivos_rejeicao.append(f"Métrica 1 (Market Cap) fora do limite (\$300M - \$2B): \${market_cap:,}")
                    if sales_growth < 20:
                        motivos_rejeicao.append(f"Métrica 2 (Sales Growth 3Y CAGR) abaixo de 20%: {sales_growth:.2f}%")
                    if ps_ratio > 10:
                        motivos_rejeicao.append(f"Métrica 3 (P/S Ratio) superior a 10 (Caro/Bolha): {ps_ratio:.2f}")
                    if gross_margin < 50:
                        motivos_rejeicao.append(f"Métrica 4 (Margem Bruta) abaixo de 50%: {gross_margin:.2f}%")
                    if asset_turnover is not None and asset_turnover < 0.4:
                        motivos_rejeicao.append(f"Métrica 5 (Asset Turnover) abaixo de 0.4: {asset_turnover:.2f}")
                    if current_ratio < 2.0:
                        motivos_rejeicao.append(f"Métrica 6 (Current Ratio) abaixo de 2.0 (Risco Falência): {current_ratio:.2f}")
                    if operating_cash_flow <= 0:
                        motivos_rejeicao.append(f"Métrica 7 (Operating Cash Flow) Negativo: \${operating_cash_flow:,}")
                    if setor in ["Biotechnology", "Pharmaceuticals"] or "Oil & Gas Exploration" in industry or "Oil & Gas" in setor:
                        motivos_rejeicao.append(f"Filtro Setorial Proibido GICS: Pertence à indústria especulativa de {setor} ({industry})")

                    st.subheader(f"📊 Relatório de Auditoria: {nome} ({ticker_resolvido})")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("ISIN Exato (XTB)", isin)
                        st.metric("Mercado / Bolsa", exchange)
                        st.metric("Setor GICS", setor)
                        st.metric("Market Cap", f"\${market_cap:,}")
                        st.metric("Asset Turnover", f"{asset_turnover:.2f}" if asset_turnover else "0.00")
                    with col2:
                        st.metric("Sales Growth (3Y CAGR)", f"{sales_growth:.2f}%")
                        st.metric("Margem Bruta", f"{gross_margin:.2f}%")
                        st.metric("P/S Ratio (Preço)", f"{ps_ratio:.2f}")
                        st.metric("Current Ratio (Liquidez)", f"{current_ratio:.2f}")
                        st.metric("Insider Ownership (Python)", f"{insider_ownership:.2f}%")

                    if len(motivos_rejeicao) == 0:
                        st.success("🎉 SUCESSO QUANTITATIVO: A empresa passou em todos os filtros numéricos de sobrevivência!")
                        st.subheader("⚠️ AVISO DE VALIDAÇÃO MANUAL OBRIGATÓRIA (O Método Marta Diogo)")
                        st.warning(
                            f"O robô validou as participações (Insider Ownership) em {insider_ownership:.2f}%.\n\n"
                            "**FALTA COBRIR A ANÁLISE QUALITATIVA MANUALMENTE:**\n"
                            f"- **Métrica 8 (Patentes da SEC):** [Clique aqui para abrir a SEC EDGAR](https://sec.gov), pesquise por {ticker_resolvido}, abra o Form 10-K e procure por 'patent' para validar o fosso económico.\n"
                            "- **Fator Fundador:** Vá à aba 'Profile' do Yahoo Finance e confirme se o CEO é o criador original."
                        )
                        st.subheader("🎯 GUIÃO DE EXECUÇÃO E COMPRA DIRETA NA XTB")
                        st.markdown(f"1. **Pesquisa por ISIN:** Cole `{isin}` na xStation para garantir erro zero.\n2. **Tipo de Conta:** Escolha **Ação Direta (STC)**. Nunca use CFDs.\n3. **Tipo de Ordem:** Execute como **Ordem Limite (Limit Order)**.")
                    else:
                        st.error("❌ REJEITADA PELO ALGORITMO: Esta empresa viola os critérios de segurança e sobrevivência!")
                        st.write("**Motivos detalhados do chumbo no funil:**")
                        for motivo in motivos_rejeicao:
                            st.write(f"- {motivo}")
                        st.warning("⚠️ Veredicto Final: Capital Seguro. Não compre esta empresa na plataforma XTB.")
            except Exception as e:
                st.error(f"Erro ao processar dados do ativo: {e}")
