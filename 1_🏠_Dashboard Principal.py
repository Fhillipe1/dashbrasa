import streamlit as st
import pandas as pd
import os
import plotly.express as px
import plotly.graph_objects as go
import pydeck as pdk
from datetime import datetime
import unicodedata
import pytz
from modules.utils import tratar_dados, carregar_base_ceps, create_gradient_line_chart, format_currency
from modules.sheets_handler import read_data_from_sheet

# --- Funções de Carregamento de Dados ---
@st.cache_data
def carregar_dados_das_planilhas():
    """Função central que agora lê os dados diretamente da Planilha Google."""
    return read_data_from_sheet()


# Configuração da página
st.set_page_config(page_title="Dashboard de Vendas La Brasa", page_icon="https://site.labrasaburger.com.br/wp-content/uploads/2021/09/logo.png", layout="wide")

with st.spinner("Conectando à Planilha Google e processando dados..."):
    # Chama a função que lê da planilha
    df_bruto = carregar_dados_das_planilhas()
    # Trata os dados lidos
    df_validos, df_cancelados = tratar_dados(df_bruto)
    # Carrega a base de CEPs local
    df_ceps_database = carregar_base_ceps()

if df_bruto is None:
    st.error("Não foi possível carregar os dados da Planilha Google. Verifique os logs ou execute a atualização na página de 'Atualizar Relatório'.")
    st.stop()

if df_validos is not None:
    st.success("Dados processados com sucesso!")

    with st.expander("📅 Aplicar Filtros no Dashboard", expanded=True):
        col_filtro1, col_filtro2 = st.columns(2)
        with col_filtro1:
            data_min = df_validos['Data'].min(); data_max = df_validos['Data'].max()
            data_selecionada = st.date_input("Selecione o Período", value=(data_min, data_max), min_value=data_min, max_value=data_max)
        with col_filtro2:
            opcoes_canal = sorted(list(df_validos['Canal de venda'].fillna('Não especificado').unique()))
            canal_selecionado = st.multiselect("Selecione o Canal de Venda", options=opcoes_canal, default=opcoes_canal)
    
    if len(data_selecionada) != 2: st.stop()
    
    start_date, end_date = data_selecionada
    df_filtrado = df_validos[(df_validos['Data'] >= start_date) & (df_validos['Data'] <= end_date) & (df_validos['Canal de venda'].fillna('Não especificado').isin(canal_selecionado))]
    st.session_state['df_filtrado'] = df_filtrado
    
    abas = st.tabs(["📊 Resumo Geral", "🛵 Delivery", "❌ Cancelamentos"])

    # Aba 1: Resumo Geral
    with abas[0]:
        st.subheader("Resumo do Período Selecionado")
        col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
        total_itens = df_filtrado['Itens'].sum(); total_taxas = df_filtrado['Total taxa de serviço'].sum(); faturamento_total = df_filtrado['Total'].sum()
        with col_kpi1: st.metric(label="💰 Total em Itens", value=format_currency(total_itens))
        with col_kpi2: st.metric(label="➕ Total em Taxas", value=format_currency(total_taxas))
        with col_kpi3: st.metric(label="📈 FATURAMENTO TOTAL", value=format_currency(faturamento_total))
        
        st.divider()

        st.subheader("Evolução do Faturamento Diário")
        faturamento_diario = df_filtrado.groupby(pd.to_datetime(df_filtrado['Data']))['Total'].sum().reset_index()
        if not faturamento_diario.empty and len(faturamento_diario) > 1:
            st.plotly_chart(create_gradient_line_chart(faturamento_diario), use_container_width=True)

    # Aba 2: Delivery
    with abas[1]:
        st.header("Análise de Delivery 🛵")
        df_delivery_filtrado = df_filtrado[df_filtrado['Tipo de Canal'] == 'Delivery']
        if not df_delivery_filtrado.empty:
            st.markdown("##### Mapa de Calor de Pedidos por CEP")
            if df_ceps_database is not None:
                pedidos_por_cep = df_delivery_filtrado['CEP'].dropna().value_counts().reset_index()
                pedidos_por_cep.columns = ['CEP', 'num_pedidos']
                map_data = pd.merge(left=pedidos_por_cep, right=df_ceps_database, left_on='CEP', right_on='cep', how='inner')
                if not map_data.empty:
                    map_data.rename(columns={'latitude': 'lat', 'longitude': 'lon'}, inplace=True, errors='ignore')
                    st.pydeck_chart(pdk.Deck(map_style=None, initial_view_state=pdk.ViewState(latitude=map_data['lat'].mean(), longitude=map_data['lon'].mean(), zoom=11, pitch=0),
                        layers=[pdk.Layer('HeatmapLayer', data=map_data, get_position='[lon, lat]', get_weight='num_pedidos', opacity=0.8, radius_pixels=60)],
                        tooltip={"text": "CEP: {cep}\nPedidos: {num_pedidos}"}))
                else: st.warning("Nenhum CEP do relatório foi encontrado no seu cache. Rode `build_cep_cache.py` para atualizar.")
        else:
            st.info("Nenhum pedido de delivery encontrado no período selecionado.")

    # Aba 3: Cancelamentos
    with abas[2]:
        st.subheader("Análise de Pedidos Cancelados")
        if not df_cancelados.empty:
            total_cancelado = df_cancelados['Total'].sum()
            st.metric(label="Total de Pedidos Cancelados", value=len(df_cancelados))
            st.metric(label="Prejuízo com Cancelamentos", value=format_currency(total_cancelado))
            st.dataframe(df_cancelados)
        else:
            st.info("Nenhum pedido cancelado no período selecionado.")
else:
    st.warning("Não foi possível carregar os dados.")
