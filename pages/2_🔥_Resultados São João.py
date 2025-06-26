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

    # --- LÓGICA DE FILTRAGEM SIMPLIFICADA ---

    # 1. Define as datas da campanha
    DATA_INICIAL_CAMPANHA = date(2025, 5, 28)
    DATA_FINAL_CAMPANHA = date(2025, 6, 30)
    
    # 2. Cria os widgets de filtro com os limites da campanha
    with st.expander("📅 Aplicar Filtros", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            data_inicial_selecionada = st.date_input(
                "Data Inicial", 
                value=DATA_INICIAL_CAMPANHA, 
                min_value=DATA_INICIAL_CAMPANHA, 
                max_value=DATA_FINAL_CAMPANHA,
                key="sj_data_inicial"
            )
        with col2:
            data_final_selecionada = st.date_input(
                "Data Final", 
                value=DATA_FINAL_CAMPANHA, 
                min_value=DATA_INICIAL_CAMPANHA, 
                max_value=DATA_FINAL_CAMPANHA,
                key="sj_data_final"
            )

        coluna_pagamento = encontrar_nome_coluna(df_validos, ['Forma de pagamento', 'Pagamento', 'Forma Pagamento'])
        
        pagamentos_selecionados = []
        if coluna_pagamento:
            formas_pagamento = sorted(df_validos[coluna_pagamento].dropna().unique())
            pagamentos_selecionados = st.multiselect(
                "Filtrar por Forma de Pagamento",
                options=formas_pagamento,
                default=formas_pagamento,
                key="sj_pagamentos"
            )
        else:
            st.warning("Coluna 'Forma de pagamento' não encontrada para o filtro.")
    
    # 3. Aplica todos os filtros de uma só vez
    df_filtrado = df_validos[
        (df_validos['Data'] >= data_inicial_selecionada) &
        (df_validos['Data'] <= data_final_selecionada) &
        (df_validos['Hora'].between(0, 4)) &
        (df_validos[coluna_pagamento].isin(pagamentos_selecionados) if coluna_pagamento and pagamentos_selecionados else True)
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
