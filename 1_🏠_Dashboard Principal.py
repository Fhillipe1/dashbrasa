# 1_🏠_Dashboard_Principal.py

import streamlit as st
import pandas as pd
from modules import data_handler, visualization
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    layout="wide", 
    page_title="Dashboard de Vendas La Brasa",
    page_icon="https://site.labrasaburger.com.br/wp-content/uploads/2021/09/logo.png"
)

# Aplica o CSS customizado
visualization.aplicar_css_local("style/style.css")

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

    # Repetir o processo para df_cancelados se necessário no futuro
    # ...

    return df_validos, df_cancelados

df_validos, df_cancelados = carregar_dados()

# --- TÍTULO PRINCIPAL ---
st.title("🔥 Dashboard de Vendas La Brasa")
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
            canais_disponiveis = df_validos['Canal de venda'].unique()
            canais_selecionados = st.multiselect("Canal de Venda", options=canais_disponiveis, default=canais_disponiveis)

    # Aplicação dos filtros no DataFrame
    df_filtrado = df_validos[
        (df_validos['Data'] >= data_inicial) &
        (df_validos['Data'] <= data_final) &
        (df_validos['Canal de venda'].isin(canais_selecionados))
    ]

    # --- ESTRUTURA DE ABAS ---
    tab_resumo, tab_delivery, tab_cancelados = st.tabs(["Resumo Geral", "Análise de Delivery", "Análise de Cancelados"])

    with tab_resumo:
        st.header("Visão Geral do Período Filtrado")
        
        # Cards de Resumo Geral
        col1, col2, col3 = st.columns(3)
        with col1:
            faturamento_sem_taxas = df_filtrado['Total'].sum() - df_filtrado['Total taxa de serviço'].sum()
            st.metric(label="Faturamento (sem taxas)", value=visualization.formatar_moeda(faturamento_sem_taxas))
        with col2:
            total_taxas = df_filtrado['Total taxa de serviço'].sum()
            st.metric(label="Total em Taxas", value=visualization.formatar_moeda(total_taxas))
        with col3:
            total_geral = df_filtrado['Total'].sum()
            st.metric(label="Faturamento Geral", value=visualization.formatar_moeda(total_geral))
        
        st.markdown("<br>", unsafe_allow_html=True)

        # Cards Diários
        visualization.criar_cards_dias_semana(df_filtrado)

        st.markdown("<br>", unsafe_allow_html=True)

        # Gráfico de Tendência
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
