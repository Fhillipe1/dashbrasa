# pages/2_🔥_Resultados São João.py

import streamlit as st
import pandas as pd
from modules import data_handler, sao_joao_handler, visualization
from datetime import date

# --- FUNÇÃO DETETIVE LOCAL (para evitar erros de sincronização) ---
def encontrar_nome_coluna(df, nomes_possiveis):
    """Encontra o nome correto de uma coluna em um dataframe a partir de uma lista de possibilidades."""
    for nome in nomes_possiveis:
        if nome in df.columns:
            return nome
    return None

# --- CONFIGURAÇÃO DA PÁGINA E CSS ---
st.set_page_config(layout="wide", page_title="Análise São João")
visualization.aplicar_css_local("style/style.css")

st.title("🔥 Análise de Resultados - Madrugada Junina")
st.markdown("Análise dedicada ao faturamento da loja no período da madrugada **(das 00:00 às 04:59)** durante a campanha de São João.")
st.markdown("---")

# --- CARREGAMENTO DOS DADOS ---
df_validos, _ = data_handler.ler_dados_do_gsheets()

if df_validos.empty:
    st.error("Não foi possível carregar os dados. Verifique a página 'Atualizar Relatório' ou sua Planilha Google.")
    st.stop()

# --- PRÉ-PROCESSAMENTO E FILTROS ---
try:
    df_validos['Data'] = pd.to_datetime(df_validos['Data'], errors='coerce').dt.date
    df_validos['Hora'] = pd.to_numeric(df_validos['Hora'], errors='coerce')
    df_validos.dropna(subset=['Data', 'Hora'], inplace=True)

    # 1. Filtra o período da madrugada (00:00 às 04:59)
    df_madrugada = df_validos[df_validos['Hora'].between(0, 4)].copy()

    # 2. Define o período junino fixo
    data_inicial_junino = date(2025, 5, 28)
    data_final_junino = date(2025, 6, 30)
    
    df_periodo_junino = df_madrugada[
        (df_madrugada['Data'] >= data_inicial_junino) &
        (df_madrugada['Data'] <= data_final_junino)
    ]

    # 3. Filtro por forma de pagamento (o único filtro interativo)
    with st.expander("💳 Filtrar por Forma de Pagamento", expanded=True):
        coluna_pagamento = encontrar_nome_coluna(df_periodo_junino, ['Forma de pagamento', 'Pagamento', 'Forma Pagamento'])

        if coluna_pagamento:
            formas_pagamento = sorted(df_periodo_junino[coluna_pagamento].dropna().unique())
            pagamentos_selecionados = st.multiselect(
                "Selecione as formas de pagamento",
                options=formas_pagamento,
                default=formas_pagamento,
                key="sj_pagamentos"
            )
            df_filtrado = df_periodo_junino[df_periodo_junino[coluna_pagamento].isin(pagamentos_selecionados)]
        else:
            st.warning("Coluna 'Forma de pagamento' não encontrada no relatório.")
            df_filtrado = df_periodo_junino # Usa todos os dados do período se a coluna não for encontrada

    st.markdown(f"Analisando dados de **{data_inicial_junino.strftime('%d/%m/%Y')}** a **{data_final_junino.strftime('%d/%m/%Y')}**.")

    # --- EXIBIÇÃO DO DASHBOARD ---
    sao_joao_handler.display_kpis(df_filtrado)
    st.markdown("---")

    col_graf1, col_graf2 = st.columns(2)
    with col_graf1:
        sao_joao_handler.display_daily_revenue_chart(df_filtrado)
        st.markdown("<br>", unsafe_allow_html=True)
        sao_joao_handler.display_hourly_performance_chart(df_filtrado)
    with col2:
        sao_joao_handler.display_payment_method_pie_chart(df_filtrado, coluna_pagamento)

except Exception as e:
    st.error(f"Ocorreu um erro ao processar os dados para esta página. Verifique se as colunas necessárias existem no seu relatório. Erro: {e}")
