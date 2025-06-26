# pages/2_🔥_Resultados São João.py

import streamlit as st
from modules import sao_joao_handler, visualization
from datetime import date

# --- CONFIGURAÇÃO DA PÁGINA E CSS DEDICADO ---
st.set_page_config(layout="wide", page_title="Análise São João")
visualization.aplicar_css_local("style/sao_joao_style.css")

# --- TÍTULO ---
st.markdown("<h1 class='main-title-sj'>Análise de Resultados</h1>", unsafe_allow_html=True)
st.markdown("<h2 class='subtitle-sj'>Madrugada Junina</h2>", unsafe_allow_html=True)

# --- CARREGAMENTO E FILTRAGEM INICIAL ---
df_madrugada_completo = sao_joao_handler.carregar_dados_sao_joao()

if df_madrugada_completo.empty:
    st.warning("Nenhum pedido encontrado no horário da madrugada (00h-05h) na sua base de dados.")
    st.stop()

# --- FILTRO INTERATIVO DE DATA ---
with st.expander("📅 Filtrar por Data (Período Junino)", expanded=True):
    # Datas da campanha para limitar o seletor
    DATA_INICIAL_CAMPANHA = date(2025, 5, 28)
    DATA_FINAL_CAMPANHA = date(2025, 6, 30)

    data_min_disponivel = max(df_madrugada_completo['Data'].min(), DATA_INICIAL_CAMPANHA)
    data_max_disponivel = min(df_madrugada_completo['Data'].max(), DATA_FINAL_CAMPANHA)

    col1, col2 = st.columns(2)
    with col1:
        data_inicial = st.date_input("Data Inicial", value=data_min_disponivel, min_value=data_min_disponivel, max_value=data_max_disponivel)
    with col2:
        data_final = st.date_input("Data Final", value=data_max_disponivel, min_value=data_inicial, max_value=data_max_disponivel)

# Aplica o filtro de data selecionado pelo usuário
df_filtrado = df_madrugada_completo[
    (df_madrugada_completo['Data'] >= data_inicial) &
    (df_madrugada_completo['Data'] <= data_final)
]

st.markdown("---")

# --- EXIBIÇÃO DO DASHBOARD ---
sao_joao_handler.display_kpis(df_filtrado)
st.markdown("---")

col_graf1, col_graf2 = st.columns(2)
with col_graf1:
    with st.container():
         st.markdown('<div class="card-chart">', unsafe_allow_html=True)
         sao_joao_handler.display_daily_revenue_chart(df_filtrado)
         st.markdown('</div>', unsafe_allow_html=True)

with col_graf2:
    with st.container():
         st.markdown('<div class="card-chart">', unsafe_allow_html=True)
         sao_joao_handler.display_hourly_performance_chart(df_filtrado)
         st.markdown('</div>', unsafe_allow_html=True)
