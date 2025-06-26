# pages/2_🔥_Resultados São João.py
import streamlit as st
import pandas as pd
from modules import data_handler, sao_joao_handler, visualization
from datetime import date

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(layout="wide", page_title="Análise São João")
visualization.aplicar_css_local("style/sao_joao_style.css") # Carrega o CSS novo

# --- CARREGAMENTO DOS DADOS ---
df_validos, _ = data_handler.ler_dados_do_gsheets()

if df_validos.empty:
    st.error("Não foi possível carregar os dados. Verifique a página 'Atualizar Relatório' ou sua Planilha Google.")
    st.stop()

# --- PRÉ-PROCESSAMENTO ---
df_validos['Data'] = pd.to_datetime(df_validos['Data'], errors='coerce').dt.date
df_validos['Hora'] = pd.to_numeric(df_validos['Hora'], errors='coerce')
df_validos.dropna(subset=['Data', 'Hora'], inplace=True)

# --- TÍTULO ---
st.markdown("<h1 class='main-title-sj'>Análise de Resultados</h1>", unsafe_allow_html=True)
st.markdown("<h2 class='subtitle-sj'>Madrugada Junina</h2>", unsafe_allow_html=True)

# --- FILTROS ---
# Define o período da campanha
DATA_INICIAL_CAMPANHA = date(2025, 5, 28)
DATA_FINAL_CAMPANHA = date(2025, 6, 30)

# Filtra o dataframe para o período da campanha ANTES de mostrar os filtros
df_periodo_junino = df_validos[
    (df_validos['Data'] >= DATA_INICIAL_CAMPANHA) &
    (df_validos['Data'] <= DATA_FINAL_CAMPANHA) &
    (df_validos['Hora'].between(0, 4))
].copy()

if df_periodo_junino.empty:
    st.warning("Nenhum pedido encontrado no período da campanha junina (28/05 a 30/06) no horário da madrugada.")
    st.stop()

# Filtro interativo de data, limitado ao período da campanha
data_inicial = st.sidebar.date_input("Data Inicial", value=df_periodo_junino['Data'].min(), min_value=df_periodo_junino['Data'].min(), max_value=df_periodo_junino['Data'].max())
data_final = st.sidebar.date_input("Data Final", value=df_periodo_junino['Data'].max(), min_value=data_inicial, max_value=df_periodo_junino['Data'].max())

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
with col_graf2:
    coluna_pagamento = data_handler.encontrar_nome_coluna(df_filtrado, ['Forma de pagamento', 'Pagamento'])
    sao_joao_handler.display_payment_method_pie_chart(df_filtrado, coluna_pagamento)

st.markdown("<br>", unsafe_allow_html=True)
sao_joao_handler.display_hourly_performance_chart(df_filtrado)
