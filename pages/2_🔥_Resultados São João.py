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
df_madrugada = sao_joao_handler.carregar_dados_sao_joao()

if df_madrugada.empty:
    st.warning("Nenhum pedido encontrado no período da madrugada (00h-05h) na sua base de dados.")
    st.stop()

# --- FILTRO INTERATIVO DE DATA ---
data_min_disponivel = df_madrugada['Data'].min()
data_max_disponivel = df_madrugada['Data'].max()

st.markdown("### Filtre o Período de Análise")
col1, col2 = st.columns(2)
with col1:
    data_inicial = st.date_input("Data Inicial", value=data_min_disponivel, min_value=data_min_disponivel, max_value=data_max_disponivel)
with col2:
    data_final = st.date_input("Data Final", value=data_max_disponivel, min_value=data_inicial, max_value=data_max_disponivel)

df_filtrado = df_madrugada[
    (df_madrugada['Data'] >= data_inicial) &
    (df_madrugada['Data'] <= data_final)
]

st.markdown("---")

# --- EXIBIÇÃO DO DASHBOARD ---
sao_joao_handler.display_kpis(df_filtrado)

st.markdown("---")

col_graf1, col_graf2 = st.columns(2)
with col_graf1:
    with st.container(border=False):
         st.markdown('<div class="card-chart">', unsafe_allow_html=True)
         sao_joao_handler.display_daily_revenue_chart(df_filtrado)
         st.markdown('</div>', unsafe_allow_html=True)
with col_graf2:
    with st.container(border=False):
         st.markdown('<div class="card-chart">', unsafe_allow_html=True)
         sao_joao_handler.display_hourly_performance_chart(df_filtrado)
         st.markdown('</div>', unsafe_allow_html=True)
