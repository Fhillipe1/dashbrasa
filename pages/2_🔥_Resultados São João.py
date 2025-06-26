# pages/2_🔥_Resultados São João.py

import streamlit as st
import pandas as pd
from modules import data_handler, sao_joao_handler, visualization
from datetime import date

# --- CONFIGURAÇÃO DA PÁGINA E CSS ---
st.set_page_config(layout="wide", page_title="Análise São João")
visualization.aplicar_css_local("style/style.css")

st.title("🔥 Análise de Resultados - Madrugada")
st.markdown("Análise dedicada ao faturamento da loja no período da madrugada (das 00:00 às 04:59).")
st.markdown("---")

# --- CARREGAMENTO DOS DADOS ---
df_validos, _ = data_handler.ler_dados_do_gsheets()

if df_validos.empty:
    st.error("Não foi possível carregar os dados. Verifique a página 'Atualizar Relatório' ou sua Planilha Google.")
    st.stop()

# --- PRÉ-PROCESSAMENTO ---
df_validos['Data'] = pd.to_datetime(df_validos['Data'], errors='coerce').dt.date
df_validos['Hora'] = pd.to_numeric(df_validos['Hora'], errors='coerce')
df_validos.dropna(subset=['Data', 'Hora'], inplace=True)

df_madrugada = df_validos[df_validos['Hora'].between(0, 4)].copy()

# --- FILTROS ---
with st.expander("📅 Aplicar Filtros", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        data_min = df_madrugada['Data'].min() if not df_madrugada.empty else date.today()
        data_max = df_madrugada['Data'].max() if not df_madrugada.empty else date.today()
        data_inicial = st.date_input("Data Inicial", value=data_min, min_value=data_min, max_value=data_max, key="sj_data_inicial")
    with col2:
        data_final = st.date_input("Data Final", value=data_max, min_value=data_min, max_value=data_max, key="sj_data_final")

    coluna_pagamento = data_handler.encontrar_nome_coluna(df_madrugada, ['Forma de pagamento', 'Pagamento', 'Forma Pagamento'])

    if coluna_pagamento:
        formas_pagamento = sorted(df_madrugada[coluna_pagamento].dropna().unique())
        pagamentos_selecionados = st.multiselect("Forma de Pagamento", options=formas_pagamento, default=formas_pagamento, key="sj_pagamentos")
        df_filtrado = df_madrugada[(df_madrugada['Data'] >= data_inicial) & (df_madrugada['Data'] <= data_final) & (df_madrugada[coluna_pagamento].isin(pagamentos_selecionados))]
    else:
        st.warning("Coluna 'Forma de pagamento' não encontrada no relatório para o filtro.")
        df_filtrado = df_madrugada[(df_madrugada['Data'] >= data_inicial) & (df_madrugada['Data'] <= data_final)]

# --- EXIBIÇÃO DO DASHBOARD ---
sao_joao_handler.display_kpis(df_filtrado)
st.markdown("---")

col_graf1, col_graf2 = st.columns(2)
with col_graf1:
    sao_joao_handler.display_daily_revenue_chart(df_filtrado)
with col_graf2:
    sao_joao_handler.display_payment_method_pie_chart(df_filtrado, coluna_pagamento)

st.markdown("<br>", unsafe_allow_html=True)
sao_joao_handler.display_hourly_performance_chart(df_filtrado)
