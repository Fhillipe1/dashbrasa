# 1_🏠_Dashboard_Principal.py

import streamlit as st
import pandas as pd
from modules import data_handler, visualization
from datetime import datetime
import os

# --- CONFIGURAÇÃO DA PÁGINA E CSS ---
LOGO_URL = "https://site.labrasaburger.com.br/wp-content/uploads/2021/09/logo.png"
st.set_page_config(layout="wide", page_title="Dashboard de Vendas La Brasa", page_icon=LOGO_URL)
visualization.aplicar_css_local("style/style.css")


# --- BARRA LATERAL (SIDEBAR) ---
st.sidebar.image(LOGO_URL, width=200)
st.sidebar.title("Navegação")

# --- CARREGAMENTO DOS DADOS ---
@st.cache_data(ttl=300)
def carregar_dados():
    df_validos, df_cancelados = data_handler.ler_dados_do_gsheets()
    
    # Tratamento para df_validos
    if not df_validos.empty:
        cols_numericas = ['Itens', 'Total taxa de serviço', 'Total', 'Entrega', 'Acréscimo', 'Desconto', 'Hora', 'Ano', 'Mês']
        for col in cols_numericas:
            if col in df_validos.columns:
                df_validos[col] = pd.to_numeric(df_validos[col], errors='coerce').fillna(0)
        if 'Data' in df_validos.columns:
            df_validos['Data'] = pd.to_datetime(df_validos['Data'], errors='coerce').dt.date
            
    # Tratamento para df_cancelados
    if not df_cancelados.empty:
        if 'Data da venda' in df_cancelados.columns:
             df_cancelados['Data'] = pd.to_datetime(df_cancelados['Data da venda']).dt.date

    return df_validos, df_cancelados

@st.cache_data(ttl=600)
def carregar_cache_cep():
    cache_path = 'data/cep_cache.csv'
    if os.path.exists(cache_path):
        return pd.read_csv(cache_path, dtype={'cep': str})
    return pd.DataFrame(columns=['cep', 'lat', 'lon'])

df_validos, df_cancelados = carregar_dados()
df_cache_cep = carregar_cache_cep()

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
    
    # Filtra também os cancelados pelo mesmo período de data
    df_cancelados_filtrado = df_cancelados[
        (df_cancelados['Data'] >= data_inicial) &
        (df_cancelados['Data'] <= data_final)
    ]


    # --- ESTRUTURA DE ABAS ---
    tab_resumo, tab_delivery, tab_cancelados_aba = st.tabs(["Resumo Geral", "Análise de Delivery", "Análise de Cancelados"])

    with tab_resumo:
        st.markdown("### <i class='bi bi-bar-chart-line-fill'></i> Visão Geral do Período Filtrado", unsafe_allow_html=True)
        visualization.criar_cards_resumo(df_filtrado)
        st.markdown("<br>", unsafe_allow_html=True)
        visualization.criar_cards_dias_semana(df_filtrado)
        st.markdown("<br>", unsafe_allow_html=True)
        col_graf_1, col_graf_2 = st.columns(2)
        with col_graf_1:
            visualization.criar_grafico_tendencia(df_filtrado)
        with col_graf_2:
            visualization.criar_grafico_barras_horarios(df_filtrado)

    with tab_delivery:
        st.markdown("### <i class='bi bi-bicycle'></i> Análise de Entregas", unsafe_allow_html=True)
        df_delivery_filtrado = df_filtrado[df_filtrado['Tipo de Canal'] == 'Delivery']
        df_delivery_total = df_validos[df_validos['Tipo de Canal'] == 'Delivery']
        if df_delivery_filtrado.empty:
            st.info("Nenhum pedido de delivery encontrado para o período e filtros selecionados.")
        else:
            visualization.criar_cards_delivery_resumo(df_delivery_filtrado, df_delivery_total)
            st.markdown("---")
            visualization.criar_top_bairros_delivery(df_delivery_filtrado, df_delivery_total)
            st.markdown("---")
            visualization.criar_mapa_de_calor(df_delivery_filtrado, df_cache_cep)

    with tab_cancelados_aba:
        st.markdown("### <i class='bi bi-x-circle'></i> Análise de Pedidos Cancelados", unsafe_allow_html=True)
        if df_cancelados_filtrado.empty:
            st.info("Nenhum pedido cancelado encontrado para o período selecionado.")
        else:
            # Chama as novas funções de visualização para cancelados
            visualization.criar_cards_cancelamento_resumo(df_cancelados_filtrado, df_filtrado)
            st.markdown("---")
            visualization.criar_grafico_motivos_cancelamento(df_cancelados_filtrado)
else:
    st.error("Não foi possível carregar os dados. Verifique a página 'Atualizar Relatório' ou a sua Planilha Google.")
