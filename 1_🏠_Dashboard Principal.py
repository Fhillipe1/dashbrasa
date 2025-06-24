import streamlit as st
import pandas as pd
import os
import plotly.express as px
import plotly.graph_objects as go
import pydeck as pdk
from datetime import datetime
import unicodedata
import pytz
import gspread
from gspread_dataframe import get_as_dataframe

# Configuração da página
st.set_page_config(page_title="Dashboard de Vendas La Brasa", page_icon="https://site.labrasaburger.com.br/wp-content/uploads/2021/09/logo.png", layout="wide")

def format_currency(value):
    """Formata um número para o padrão de moeda brasileiro (R$ 1.234,56)."""
    if pd.isna(value):
        return "R$ 0,00"
    s = f'{value:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
    return f"R$ {s}"

@st.cache_data
def carregar_dados_da_planilha():
    """Lê todos os dados da Planilha Google e retorna como um DataFrame."""
    try:
        # Tenta autenticar via Streamlit Secrets (para quando estiver na nuvem)
        if "google_credentials" in st.secrets:
            creds_dict = st.secrets.get("google_credentials")
            gc = gspread.service_account_from_dict(creds_dict)
        else:
            # Se não, usa o arquivo local
            credentials_file = "google_credentials.json"
            if not os.path.exists(credentials_file):
                st.error(f"ERRO: Arquivo de credenciais '{credentials_file}' não encontrado.")
                return None
            gc = gspread.service_account(filename=credentials_file)

        sheet_name = st.secrets.get("GOOGLE_SHEET_NAME") or os.getenv("GOOGLE_SHEET_NAME")
        if not sheet_name:
            st.error("ERRO: GOOGLE_SHEET_NAME não configurado.")
            return None
            
        print(f"Lendo dados da Planilha Google: '{sheet_name}'...")
        spreadsheet = gc.open(sheet_name)
        # Lê a aba 'Vendas Validas'
        worksheet = spreadsheet.worksheet('Relatorio_Vendas_Saipos')
        df = get_as_dataframe(worksheet, evaluate_formulas=False, header=0)
        df.dropna(how='all', axis=1, inplace=True)
        print(f"Sucesso! {len(df)} linhas lidas da planilha.")
        return df

    except Exception as e:
        st.error(f"ERRO ao ler a Planilha Google: {e}")
        return None


@st.cache_data
def carregar_base_ceps():
    """Carrega a base de dados de CEPs e garante que as coordenadas sejam numéricas."""
    cache_file = 'cep_cache.csv'
    if os.path.exists(cache_file):
        df = pd.read_csv(cache_file, dtype=str)
        if 'CEP' in df.columns and 'cep' not in df.columns: df.rename(columns={'CEP': 'cep'}, inplace=True)
        df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
        df['lon'] = pd.to_numeric(df['lon'], errors='coerce')
        df.dropna(subset=['lat', 'lon'], inplace=True)
        return df
    return None

def padronizar_texto(texto):
    """Função para limpar e padronizar texto."""
    if not isinstance(texto, str): return texto
    texto = ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
    return texto.strip().upper()

def tratar_dados(df):
    """Aplica todas as transformações necessárias no DataFrame lido da planilha."""
    if df is None or df.empty: return None, None
    
    # Como os dados já foram tratados antes de salvar, esta função agora é mais simples.
    # Ela principalmente garante os tipos de dados corretos para o Streamlit.
    df_validos = df.copy()

    # Garante que as colunas de data sejam do tipo datetime
    df_validos['Data da venda'] = pd.to_datetime(df_validos['Data da venda'], errors='coerce')
    df_validos['Data'] = pd.to_datetime(df_validos['Data']).dt.date

    # Simula um dataframe de cancelados vazio, pois a lógica de separação já foi feita antes
    df_cancelados = pd.DataFrame() 

    return df_validos, df_cancelados

def create_gradient_line_chart(df_data):
    """Cria um gráfico de linha com cores de gradiente para subidas e descidas."""
    df_data['Data'] = pd.to_datetime(df_data['Data'])
    df_data = df_data.sort_values(by='Data')
    df_data['diff'] = df_data['Total'].diff().fillna(0)
    fig = go.Figure()
    color_subida = '#5D9C59'; color_descida = '#DF2E38'
    for i in range(1, len(df_data)):
        fig.add_trace(go.Scatter(
            x=list(df_data['Data'])[i-1:i+1], y=list(df_data['Total'])[i-1:i+1], mode='lines',
            line=dict(color=color_subida if df_data['diff'].iloc[i] >= 0 else color_descida, width=3),
            hoverinfo='none'
        ))
    fig.add_trace(go.Scatter(
        x=df_data['Data'], y=df_data['Total'], mode='markers',
        marker=dict(color='#FFFFFF', size=5, line=dict(width=1, color='DarkSlateGrey')),
        hovertemplate='<b>Data:</b> %{x|%d/%m/%Y}<br><b>Faturamento:</b> R$ %{y:,.2f}<extra></extra>'
    ))
    fig.update_layout(showlegend=False, height=350, yaxis_title="Faturamento (R$)", xaxis_title=None, margin=dict(l=20, r=20, t=20, b=20))
    return fig
    
# --- Início da Interface do Streamlit ---
st.title("🔥 Dashboard de Vendas La Brasa")

with st.spinner("Conectando à Planilha Google e processando dados..."):
    df_bruto_sheets = carregar_dados_da_planilha()
    df_validos, df_cancelados = tratar_dados(df_bruto_sheets)
    df_ceps_database = carregar_base_ceps()

if df_validos is None:
    st.error("Não foi possível carregar os dados da Planilha Google. Verifique os logs ou execute a atualização na página de 'Atualizar Relatório'.")
    st.stop()

# --- Corpo Principal do Dashboard ---
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

st.subheader("Resumo do Período Selecionado")
col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
with col_kpi1: st.metric(label="💰 Faturamento Total", value=format_currency(df_filtrado['Total'].sum()))
with col_kpi2: st.metric(label="➕ Total em Taxas", value=format_currency(df_filtrado['Total taxa de serviço'].sum()))
with col_kpi3: st.metric(label="Total de Pedidos", value=df_filtrado['Pedido'].nunique())
    
st.divider()

st.subheader("Evolução do Faturamento no Período")
faturamento_diario = df_filtrado.groupby('Data')['Total'].sum().reset_index()
if not faturamento_diario.empty and len(faturamento_diario) > 1:
    st.plotly_chart(create_gradient_line_chart(faturamento_diario), use_container_width=True)

st.divider()
    
st.header("Análise Geográfica de Delivery 🗺️")
if df_ceps_database is not None:
    df_delivery = df_filtrado[df_filtrado['Tipo de Canal'] == 'Delivery'].dropna(subset=['CEP'])
    if not df_delivery.empty:
        pedidos_por_cep = df_delivery['CEP'].value_counts().reset_index()
        pedidos_por_cep.columns = ['CEP', 'num_pedidos']
        map_data = pd.merge(pedidos_por_cep, df_ceps_database, left_on='CEP', right_on='cep', how='inner')
        if not map_data.empty:
            map_data.rename(columns={'latitude': 'lat', 'longitude': 'lon'}, inplace=True, errors='ignore')
            st.pydeck_chart(pdk.Deck(
                map_style=None,
                initial_view_state=pdk.ViewState(latitude=map_data['lat'].mean(), longitude=map_data['lon'].mean(), zoom=11, pitch=0),
                layers=[pdk.Layer('HeatmapLayer', data=map_data, get_position='[lon, lat]', get_weight='num_pedidos', opacity=0.8, radius_pixels=40)],
                tooltip={"text": "CEP: {cep}\nPedidos: {num_pedidos}"}))
    else:
        st.info("Nenhum pedido de delivery no período selecionado.")
else:
    st.warning("`cep_cache.csv` não encontrado. Rode `python build_cep_cache.py` para gerar o mapa.")
