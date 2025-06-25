# 1_🏠_Dashboard_Principal.py

import streamlit as st
import pandas as pd
from modules import data_handler
from datetime import datetime, timedelta

# Configuração da página
st.set_page_config(layout="wide", page_title="Dashboard de Vendas")

st.title("🏠 Dashboard Principal")

# Usamos o cache para não precisar ler a planilha a cada interação do usuário
@st.cache_data(ttl=300) # ttl = Time To Live, em segundos. Os dados ficam em cache por 5 minutos.
def carregar_dados():
    df_validos, df_cancelados = data_handler.ler_dados_do_gsheets()
    
    # --- CONVERSÕES DE TIPO IMPORTANTES ---
    # Converte colunas para os tipos corretos após a leitura
    if not df_validos.empty:
        # Colunas numéricas
        cols_numericas = ['Itens', 'Total taxa de serviço', 'Total', 'Entrega', 'Acréscimo', 'Desconto', 'Hora', 'Ano', 'Mês']
        for col in cols_numericas:
            if col in df_validos.columns:
                df_validos[col] = pd.to_numeric(df_validos[col], errors='coerce').fillna(0)
        
        # Colunas de data
        if 'Data' in df_validos.columns:
            df_validos['Data'] = pd.to_datetime(df_validos['Data'], errors='coerce').dt.date

    return df_validos, df_cancelados

df_validos, df_cancelados = carregar_dados()

# --- BARRA LATERAL DE FILTROS ---
st.sidebar.header("Filtros")

if not df_validos.empty and 'Data' in df_validos.columns:
    # Filtro de Data
    data_min = df_validos['Data'].min()
    data_max = df_validos['Data'].max()
    
    data_inicial = st.sidebar.date_input(
        "Data Inicial",
        value=data_min,
        min_value=data_min,
        max_value=data_max
    )
    
    data_final = st.sidebar.date_input(
        "Data Final",
        value=data_max,
        min_value=data_min,
        max_value=data_max
    )

    # Filtro de Canal de Venda
    canais_disponiveis = df_validos['Canal de venda'].unique()
    canais_selecionados = st.sidebar.multiselect(
        "Canal de Venda",
        options=canais_disponiveis,
        default=canais_disponiveis
    )

    # Aplicação dos filtros no DataFrame
    df_filtrado = df_validos[
        (df_validos['Data'] >= data_inicial) &
        (df_validos['Data'] <= data_final) &
        (df_validos['Canal de venda'].isin(canais_selecionados))
    ]
    
    st.markdown("---")
    st.subheader("Dados Filtrados (Apenas para verificação)")
    st.info(f"Exibindo {len(df_filtrado)} registros de um total de {len(df_validos)}.")
    st.dataframe(df_filtrado)

else:
    st.warning("Não há dados válidos para exibir ou a coluna 'Data' não foi encontrada. Por favor, atualize o relatório na página 'Atualizar Relatório'.")
