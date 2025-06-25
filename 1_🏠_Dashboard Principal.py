# 1_🏠_Dashboard_Principal.py

import streamlit as st
import pandas as pd
from modules import data_handler, visualization
from datetime import datetime

# Configuração da página
st.set_page_config(layout="wide", page_title="Dashboard de Vendas")

st.title("🏠 Dashboard Principal")

# Usamos o cache para não precisar ler a planilha a cada interação do usuário
@st.cache_data(ttl=300) # ttl = Time To Live, em segundos. Os dados ficam em cache por 5 minutos.
def carregar_dados():
    df_validos, df_cancelados = data_handler.ler_dados_do_gsheets()
    
    if df_validos.empty:
        return pd.DataFrame(), pd.DataFrame()

    # --- CONVERSÕES DE TIPO IMPORTANTES ---
    cols_numericas = ['Itens', 'Total taxa de serviço', 'Total', 'Entrega', 'Acréscimo', 'Desconto', 'Hora', 'Ano', 'Mês']
    for col in cols_numericas:
        if col in df_validos.columns:
            df_validos[col] = pd.to_numeric(df_validos[col], errors='coerce').fillna(0)
    
    if 'Data' in df_validos.columns:
        df_validos['Data'] = pd.to_datetime(df_validos['Data'], errors='coerce').dt.date

    return df_validos, df_cancelados

df_validos, df_cancelados = carregar_dados()

# --- BARRA LATERAL DE FILTROS ---
st.sidebar.header("Filtros")

if not df_validos.empty:
    data_min = df_validos['Data'].min()
    data_max = df_validos['Data'].max()
    
    data_inicial = st.sidebar.date_input("Data Inicial", value=data_min, min_value=data_min, max_value=data_max)
    data_final = st.sidebar.date_input("Data Final", value=data_max, min_value=data_min, max_value=data_max)

    canais_disponiveis = df_validos['Canal de venda'].unique()
    canais_selecionados = st.sidebar.multiselect("Canal de Venda", options=canais_disponiveis, default=canais_disponiveis)

    # Aplicação dos filtros no DataFrame
    df_filtrado = df_validos[
        (df_validos['Data'] >= data_inicial) &
        (df_validos['Data'] <= data_final) &
        (df_validos['Canal de venda'].isin(canais_selecionados))
    ]

    # --- INÍCIO DA CRIAÇÃO DOS CARDS ---
    st.markdown("---")
    
    # Cálculos para os cards
    # Assumimos que 'Total' é o valor final pago pelo cliente.
    # Faturamento sem taxas = Total - Taxa de serviço.
    faturamento_sem_taxas = df_filtrado['Total'].sum() - df_filtrado['Total taxa de serviço'].sum()
    total_taxas = df_filtrado['Total taxa de serviço'].sum()
    total_geral = df_filtrado['Total'].sum()

    # Exibição dos cards
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label="Faturamento (sem taxas)",
            value=visualization.formatar_moeda(faturamento_sem_taxas)
        )
    
    with col2:
        st.metric(
            label="Total em Taxas",
            value=visualization.formatar_moeda(total_taxas)
        )
        
    with col3:
        st.metric(
            label="Faturamento Geral",
            value=visualization.formatar_moeda(total_geral)
        )

    st.markdown("---")
    # A tabela de verificação pode ser removida ou comentada depois
    st.subheader("Dados Filtrados (Apenas para verificação)")
    st.dataframe(df_filtrado)

else:
    st.warning("Não há dados válidos para exibir. Por favor, atualize o relatório na página 'Atualizar Relatório'.")
