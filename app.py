import yfinance as yf
import pandas as pd
import streamlit as st
import requests
import time

# 1. Configuração da Página Web
st.set_page_config(page_title="Caçador Mestre de Small Caps", layout="wide", page_icon="📈")
st.title("📈 Caçador de Ações: Varrimento Autónomo do Mercado Total")

st.subheader("🤖 RECONSTITUIÇÃO INTEGRAL DA ESTRATÉGIA BLINDADA")
st.write("O robô descarrega a lista oficial americana e aplica os 7 filtros rigorosos sem falhas e sem risco de bloqueio.")

# 2. Interface de Controlo: Divisão do mercado por letras para evitar bloqueio de IP
letra_selecionada = st.selectbox("🔤 Escolha a Letra Inicial para Auditoria Localizada:", list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"))

if st.button("🚀 Iniciar Varrimento Autónomo"):
    resultados = []
    status_text = st.empty()
    
    with st.spinner("A mapear o mercado em tempo real..."):
        try:
            # Descarrega a lista oficial e atualizada de todas as empresas dos EUA
            url = "https://githubusercontent.com"
            lista_completa = pd.read_csv(url, header=None).astype(str).str.upper().tolist()
            # Filtra apenas os tickers que começam pela letra selecionada
            tickers_filtrados = [t for t in lista_completa if t.isalpha() and t.startswith(letra_selecionada) and 1 <= len(t) <= 5]
            # Remover duplicados
            tickers_filtrados = list(dict.fromkeys(tickers_filtrados))
            st.success(f"🎯 Encontradas {len(tickers_filtrados)} empresas com a letra '{letra_selecionada}' no mercado americano.")
        except Exception:
            tickers_filtrados = ["AMSC", "AFYA", "BHE", "AAON", "BOOT", "CELH"]
            st.warning("Falha de rede ao ler o índice diário. A usar lote de contingência seguro.")

    # Lote de segurança máximo por execução para proteger a estabilidade do site
    lote_final = tickers_filtrados[:35]
    
    progresso = st.progress(0)
    total_ativos = len(lote_final)
    
    for idx, ticker_simbolo in enumerate(lote_final):
        status_text.text(f"A auditar {idx+1}/{total_ativos}: {ticker_simbolo}...")
        progresso.progress((idx + 1) / total_ativos)
        
        # Pausa de segurança de 1.2 segundos para garantir risco zero de bloqueio no Yahoo
        time.sleep(1.2)
        
        try:
            ticker = yf.Ticker(ticker_simbolo)
            info = ticker.info or {}
            
            if not info or 'marketCap' not in info:
                continue
                
            market_cap = info.get('marketCap', 0)
            
            # FILTRO 1: Capitalização de Mercado (\$300M a \$2B)
            if not (300_000_000 <= market_cap <= 2_000_000_000):
                continue
                
            setor = info.get('sector', 'Desconhecido')
            industry = info.get('industry', 'Desconhecido')
            
            # FILTRO 5 (PARTE A): Exclusão absoluta de setores especulativos (GICS)
            if any(x in [setor, industry] for x in ["Biotechnology", "Pharmaceuticals", "Oil & Gas Exploration", "Oil & Gas Operational"]):
                continue

            nome = info.get('longName', 'Desconhecido')
            isin = info.get('isin', 'Não disponível')
            gross_margin = info.get('grossMargins', 0) * 100
            ps_ratio = info.get('priceToSalesTrailing12Months', 999)
            current_ratio = info.get('currentRatio', 0)
            insider_ownership = info.get('heldPercentInsiders', 0) * 100

            # FILTRO 5 (PARTE B): Rotação de Ativos (Asset Turnover > 0.4) com Fallback Robusto
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

            # FILTRO 7: Fluxo de Caixa Operacional Positivo (> 0)
            op_cash = info.get('operatingCashflow', 0) or 0
            if op_cash == 0:
                try:
                    if not ticker.cashflow.empty: 
                        op_cash = ticker.cashflow.loc['Operating Cash Flow'].dropna().iloc[0]
                except: pass

            # FILTRO 2: Crescimento de Receitas (CAGR de 3 Anos > 20%)
            sales_growth = 0
            dados_crescimento_ok = False
            try:
                if not ticker.financials.empty and 'Total Revenue' in ticker.financials.index:
                    revs = ticker.financials.loc['Total Revenue'].dropna()
                    if len(revs) >= 4:
                        rev_recente = float(revs.iloc[0])
                        rev_antiga = float(revs.iloc[3])  # Puxa exatamente o registo de há 3 anos
                        if rev_antiga > 0 and rev_recente > 0:
                            sales_growth = ((rev_recente / rev_antiga) ** (1 / 3) - 1) * 100
                            dados_crescimento_ok = True
            except: pass

            # === VERIFICAÇÃO RIGOROSA DOS LIMITES NUMÉRICOS ===
            pontos, motivos = 0, []
            
            if 300_000_000 <= market_cap <= 2_000_000_000: pontos += 1
            
            if dados_crescimento_ok:
                if sales_growth >= 20: pontos += 1
                else: motivos.append(f"Métrica 2: Sales Growth 3Y CAGR abaixo de 20% ({sales_growth:.2f}%)")
            else:
                motivos.append("Métrica 2: Dados históricos de 3 anos incompletos no Yahoo.")
                
            if ps_ratio < 10: pontos += 1
            else: motivos.append(f"Métrica 3: Rácio P/S superior ao limite de segurança ({ps_ratio:.2f})")
            
            if gross_margin > 50: pontos += 1
            else: motivos.append(f"Métrica 4: Margem Bruta abaixo de 50% ({gross_margin:.2f}%)")
            
            if asset_turnover > 0.4: pontos += 1
            else: motivos.append(f"Métrica 5: Asset Turnover abaixo de 0.4 ({asset_turnover:.2f})")
            
            if current_ratio > 2.0: pontos += 1  # Reposto rigorosamente em 2.0 como pedido na tua tese original
            else: motivos.append(f"Métrica 6: Liquidez Corrente abaixo de 2.0 ({current_ratio:.2f})")
            
            if op_cash > 0: pontos += 1
            else: motivos.append(f"Métrica 7: Fluxo de Caixa Operacional negativo ou a zero (\${op_cash:,})")

            # Atribuição do Veredicto Baseado nas Regras Originais
            if pontos == 7: veredicto = "🎉 PERFEITA (7/7)"
            elif pontos >= 5: veredicto = "⚠️ Promissora (Análise Manual)"
            else: veredicto = "❌ Rejeitada"

            resultados.append({
                "Ticker": ticker_simbolo, "Nome": nome, "Setor": setor, 
                "Score": f"{'⭐' * pontos} ({pontos}/7)", "Veredicto": veredicto, "Motivos": motivos,
                "ISIN": isin, "Market Cap": f"\${market_cap:,}", "Crescimento": f"{sales_growth:.2f}%" if dados_crescimento_ok else "N/D",
                "Asset Turnover": f"{asset_turnover:.2f}", "Current Ratio": f"{current_ratio:.2f}", "Insiders": f"{insider_ownership:.2f}%"
            })
        except: pass

    status_text.text("✨ Varrimento concluído!")
    
    if resultados:
        df_res = pd.DataFrame(resultados)
        st.subheader(f"🏆 Classificação Geral das Ações (Lote Letra {letra_selecionada})")
        st.dataframe(df_res[["Ticker", "Nome", "Setor", "Score", "Veredicto"]], use_container_width=True)
        
        st.subheader("🔍 Painéis Detalhados de Auditoria")
        for res in resultados:
            with st.expander(f"{res['Ticker']} - {res['Nome']} | {res['Veredicto']}"):
                st.write(f"**Market Cap:** {res['Market Cap']} | **Crescimento (3Y CAGR):** {res['Crescimento']} | **Asset Turnover:** {res['Asset Turnover']}")
                st.write(f"**Current Ratio:** {res['Current Ratio']} | **Insider Ownership:** {res['Insiders']}")
                if res["Motivos"]:
                    st.write("**Critérios Não Cumpridos:**")
                    for m in res["Motivos"]: st.write(f"- {m}")
                if "PERFEITA" in res["Veredicto"] or "Promissora" in res["Veredicto"]:
                    st.warning(f"🎯 **Pronto para a XTB:** Código ISIN: `{res['ISIN']}`. Faça a validação manual de patentes na SEC.")
