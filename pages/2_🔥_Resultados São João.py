# pages/2_🔥_Resultados São João.py

import streamlit as st
import pandas as pd
from modules import data_handler, sao_joao_handler, visualization
from datetime import datetime, date

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(layout="wide", page_title="Análise São João")
visualization.aplicar_css_local("style/style.css")

st.title("🔥 Análise de Resultados - Madrugada de São João")
st.markdown("---")

# --- CARREGAMENTO DOS DADOS ---
# A função carregar_dados já está em cache, então esta chamada é super rápida
df_validos, df_cancelados = data_handler.ler_dados_do_gsheets()

if df_validos.empty:
    st.error("Não foi possível carregar os dados. Verifique a página 'Atualizar Relatório' ou a sua Planilha Google.")
    st.stop()

# --- PRÉ-PROCESSAMENTO E FILTROS ---

# Converte colunas para os tipos corretos
df_validos['Data'] = pd.to_datetime(df_validos['Data'], errors='coerce').dt.date
df_validos['Hora'] = pd.to_numeric(df_validos['Hora'], errors='coerce')
df_validos = df_validos.dropna(subset=['Data', 'Hora']) # Garante que não há datas/horas nulas

# Filtra o período da madrugada (00:00 às 04:59)
df_madrugada = df_validos[df_validos['Hora'].between(0, 4)].copy()

st.sidebar.header("Filtros da Madrugada")

# Filtros da barra lateral
data_min = df_madrugada['Data'].min() if not df_madrugada.empty else date.today()
data_max = df_madrugada['Data'].max() if not df_madrugada.empty else date.today()

data_inicial = st.sidebar.date_input("Data Inicial", value=data_min, min_value=data_min, max_value=data_max)
data_final = st.sidebar.date_input("Data Final", value=data_max, min_value=data_min, max_value=data_max)

# Filtro por forma de pagamento
if 'Forma de pagamento' in df_madrugada.columns:
    formas_pagamento = df_madrugada['Forma de pagamento'].dropna().unique()
    pagamentos_selecionados = st.sidebar.multiselect(
        "Forma de Pagamento",
        options=formas_pagamento,
        default=formas_pagamento
    )
    # Aplica todos os filtros
    df_filtrado = df_madrugada[
        (df_madrugada['Data'] >= data_inicial) &
        (df_madrugada['Data'] <= data_final) &
        (df_madrugada['Forma de pagamento'].isin(pagamentos_selecionados))
    ]
else:
    df_filtrado = df_madrugada[
        (df_madrugada['Data'] >= data_inicial) &
        (df_madrugada['Data'] <= data_final)
    ]

# --- EXIBIÇÃO DO DASHBOARD ---

# KPIs
sao_joao_handler.display_kpis(df_filtrado)
st.markdown("---")

# Gráficos em duas colunas
col1, col2 = st.columns(2)
with col1:
    sao_joao_handler.display_daily_revenue_chart(df_filtrado)
    st.markdown("<br>", unsafe_allow_html=True)
    sao_joao_handler.display_hourly_performance_chart(df_filtrado)
with col2:
    sao_joao_handler.display_payment_method_pie_chart(df_filtrado)
