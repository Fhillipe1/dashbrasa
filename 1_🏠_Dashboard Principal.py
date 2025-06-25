# 1_🏠_Dashboard_Principal.py

import streamlit as st
import pandas as pd
from modules import data_handler, visualization
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA E CSS ---
LOGO_URL = "https://site.labrasaburger.com.br/wp-content/uploads/2021/09/logo.png"
st.set_page_config(
    layout="wide", 
    page_title="Dashboard de Vendas La Brasa",
    page_icon=LOGO_URL
)
visualization.aplicar_css_local("style/style.css")


# --- BARRA LATERAL (SIDEBAR) ---
st.sidebar.image(LOGO_URL, width=200)
st.sidebar.title("Navegação")

# --- CARREGAMENTO DOS DADOS ---
@st.cache_data(ttl=300)
def carregar_dados():
    df_validos, df_cancelados = data_handler.ler_dados_do_gsheets()
    
    if not df_validos.empty:
        cols_numericas = ['Itens', 'Total taxa de serviço', 'Total', 'Entrega', 'Acréscimo', 'Desconto', 'Hora', 'Ano', 'Mês']
        for col in cols_numericas:
            if col in df_validos.columns:
                df_validos[col] = pd.to_numeric(df_validos[col], errors='coerce').fillna(0)
        
        if 'Data' in df_validos.columns:
            df_validos['Data'] = pd.to_datetime(df_validos['Data'], errors='coerce').dt.date
    return df_validos, df_cancelados

df_validos, df_cancelados = carregar_dados()


# --- CABEÇALHO COM LOGO E TÍTULO ---
col_logo, col_titulo = st.columns([0.1, 0.9])
with col_logo:
    st.image(LOGO_URL, width=100)
with col_titulo:
    st.title("Dashboard de Vendas")
st.markdown("---")


# --- FILTROS NO CORPO DA PÁGINA ---
if not df_validos.empty:
    with st.expander("📅 Aplicar Filtros", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            data_min = df_validos['Data'].min()
            data_max = df_validos['Data'].max()
            data_inicial = st.date_input("Data Inicial", value=data_min, min_value=data_min, max_value=data_max)
            data_final = st.date_input("Data Final", value=data_max, min_value=data_min, max_value=data_max)
        
        with col2:
            lista_canais = df_validos['Canal de venda'].dropna().unique()
            canais_disponiveis = sorted([str(canal) for canal in lista_canais])
            canais_selecionados = st.multiselect("Canal de Venda", options=canais_disponiveis, default=canais_disponiveis)

    df_filtrado = df_validos[
        (df_validos['Data'] >= data_inicial) &
        (df_validos['Data'] <= data_final) &
        (df_validos['Canal de venda'].isin(canais_selecionados))
    ]

    # --- ESTRUTURA DE ABAS ---
    tab_resumo, tab_delivery, tab_cancelados = st.tabs(["Resumo Geral", "Análise de Delivery", "Análise de Cancelados"])

    with tab_resumo:
        st.markdown("### <i class='bi bi-bar-chart-line-fill'></i> Visão Geral do Período Filtrado", unsafe_allow_html=True)
        
        visualization.criar_cards_resumo(df_filtrado)
        
        st.markdown("<br>", unsafe_allow_html=True)

        visualization.criar_cards_dias_semana(df_filtrado)

        st.markdown("<br>", unsafe_allow_html=True)
        
        visualization.criar_grafico_tendencia(df_filtrado)

    with tab_delivery:
        st.header("Análise de Entregas")
        st.info("Em breve: KPIs de entrega, mapa de calor por bairro e muito mais!")

    with tab_cancelados:
        st.header("Análise de Pedidos Cancelados")
        st.info("Em breve: Principais motivos, valores e horários de cancelamento.")
        if not df_cancelados.empty:
            st.dataframe(df_cancelados)
        else:
            st.write("Nenhum pedido cancelado no período.")
else:
    st.error("Não foi possível carregar os dados. Verifique a página 'Atualizar Relatório' ou a sua Planilha Google.")
