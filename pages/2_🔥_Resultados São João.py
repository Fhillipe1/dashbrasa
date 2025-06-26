# pages/2_🔥_Resultados São João.py

import streamlit as st
import pandas as pd
from modules import data_handler, sao_joao_handler, visualization
from datetime import date

# --- FUNÇÃO DETETIVE LOCAL ---
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

# --- PRÉ-PROCESSAMENTO ---
try:
    df_validos['Data'] = pd.to_datetime(df_validos['Data'], errors='coerce').dt.date
    df_validos['Hora'] = pd.to_numeric(df_validos['Hora'], errors='coerce')
    df_validos.dropna(subset=['Data', 'Hora'], inplace=True)

    df_madrugada = df_validos[df_validos['Hora'].between(0, 4)].copy()

    # Define o período junino fixo
    DATA_INICIAL_CAMPANHA = date(2025, 5, 28)
    DATA_FINAL_CAMPANHA = date(2025, 6, 30)
    
    # Filtra os dados apenas para o período da campanha, para definir os limites dos filtros
    df_periodo_junino = df_madrugada[
        (df_madrugada['Data'] >= DATA_INICIAL_CAMPANHA) &
        (df_madrugada['Data'] <= DATA_FINAL_CAMPANHA)
    ]

    if df_periodo_junino.empty:
        st.info("Não foram encontrados pedidos no período da campanha junina (28/05 a 30/06) no horário da madrugada.")
        st.stop()

    # --- FILTROS INTERATIVOS ---
    with st.expander("📅 Aplicar Filtros", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            # CORREÇÃO: Os valores min e max do seletor são travados no período da campanha
            data_inicial = st.date_input(
                "Data Inicial", 
                value=df_periodo_junino['Data'].min(), 
                min_value=df_periodo_junino['Data'].min(), 
                max_value=df_periodo_junino['Data'].max(),
                key="sj_data_inicial"
            )
        with col2:
            data_final = st.date_input(
                "Data Final", 
                value=df_periodo_junino['Data'].max(), 
                min_value=df_periodo_junino['Data'].min(), 
                max_value=df_periodo_junino['Data'].max(),
                key="sj_data_final"
            )

        coluna_pagamento = encontrar_nome_coluna(df_periodo_junino, ['Forma de pagamento', 'Pagamento', 'Forma Pagamento'])

        if coluna_pagamento:
            formas_pagamento = sorted(df_periodo_junino[coluna_pagamento].dropna().unique())
            pagamentos_selecionados = st.multiselect(
                "Filtrar por Forma de Pagamento",
                options=formas_pagamento,
                default=formas_pagamento,
                key="sj_pagamentos"
            )
            # Aplica todos os filtros
            df_filtrado = df_periodo_junino[
                (df_periodo_junino['Data'] >= data_inicial) &
                (df_periodo_junino['Data'] <= data_final) &
                (df_periodo_junino[coluna_pagamento].isin(pagamentos_selecionados))
            ]
        else:
            st.warning("Coluna 'Forma de pagamento' não encontrada para o filtro.")
            df_filtrado = df_periodo_junino[
                (df_periodo_junino['Data'] >= data_inicial) &
                (df_periodo_junino['Data'] <= data_final)
            ]

    # --- EXIBIÇÃO DO DASHBOARD ---
    sao_joao_handler.display_kpis(df_filtrado)
    st.markdown("---")

    col_graf1, col_graf2 = st.columns(2)
    with col_graf1:
        sao_joao_handler.display_daily_revenue_chart(df_filtrado)
        st.markdown("<br>", unsafe_allow_html=True)
        sao_joao_handler.display_hourly_performance_chart(df_filtrado)
    with col_graf2:
        sao_joao_handler.display_payment_method_pie_chart(df_filtrado, coluna_pagamento)

except Exception as e:
    st.error(f"Ocorreu um erro ao processar os dados para esta página. Verifique se as colunas necessárias existem no seu relatório. Erro: {e}")
