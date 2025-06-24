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
from dotenv import load_dotenv

# Carrega variáveis de ambiente (para senhas e nomes de arquivos)
load_dotenv()

# Configuração da página
st.set_page_config(page_title="Dashboard de Vendas La Brasa", page_icon="https://site.labrasaburger.com.br/wp-content/uploads/2021/09/logo.png", layout="wide")

# --- Funções Auxiliares ---

def format_currency(value):
    """Formata um número para o padrão de moeda brasileiro (R$ 1.234,56)."""
    if pd.isna(value):
        return "R$ 0,00"
    s = f'{value:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
    return f"R$ {s}"

@st.cache_data
def carregar_dados_das_planilhas():
    """Lê os dados diretamente da Planilha Google, nossa única fonte da verdade."""
    print("Iniciando carregamento de dados da Planilha Google...")
    df_validos = pd.DataFrame()
    df_cancelados = pd.DataFrame()
    try:
        # Lógica de autenticação que funciona tanto na nuvem (st.secrets) quanto localmente
        if "google_credentials" in st.secrets:
            creds_dict = st.secrets.get("google_credentials")
            gc = gspread.service_account_from_dict(creds_dict)
        else:
            credentials_file = "google_credentials.json"
            if not os.path.exists(credentials_file):
                st.error(f"ERRO: Arquivo de credenciais '{credentials_file}' não encontrado.")
                return None, None
            gc = gspread.service_account(filename=credentials_file)

        sheet_name = st.secrets.get("GOOGLE_SHEET_NAME") or os.getenv("GOOGLE_SHEET_NAME")
        if not sheet_name:
            st.error("ERRO: GOOGLE_SHEET_NAME não configurado.")
            return None, None
        
        spreadsheet = gc.open(sheet_name)
        worksheets = spreadsheet.worksheets()
        
        # Lê a primeira aba (índice 0) para Vendas Válidas
        if len(worksheets) > 0:
            worksheet_validos = worksheets[0]
            df_validos = get_as_dataframe(worksheet_validos, evaluate_formulas=False, header=0)
            df_validos.dropna(how='all', axis=1, inplace=True)
            print(f"Lidas {len(df_validos)} linhas da aba '{worksheet_validos.title}'.")
        
        # Lê a segunda aba (índice 1) para Vendas Canceladas, se existir
        if len(worksheets) > 1:
            worksheet_cancelados = worksheets[1]
            df_cancelados = get_as_dataframe(worksheet_cancelados, evaluate_formulas=False, header=0)
            df_cancelados.dropna(how='all', axis=1, inplace=True)
            print(f"Lidas {len(df_cancelados)} linhas da aba '{worksheet_cancelados.title}'.")
            
        return df_validos, df_cancelados
    except Exception as e:
        st.error(f"ERRO ao carregar dados da Planilha Google: {e}")
        return None, None

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

def tratar_dados(df_validos, df_cancelados):
    """Aplica as transformações de tipo de dado e fuso horário nos dados lidos da planilha."""
    if df_validos is None or df_validos.empty:
        return pd.DataFrame(), pd.DataFrame() if df_cancelados is None else df_cancelados

    df_validos = df_validos.copy()

    # Garante que colunas de data e numéricas lidas da planilha (que podem vir como texto) sejam convertidas
    df_validos['Data da venda'] = pd.to_datetime(df_validos['Data da venda'], errors='coerce')
    df_validos.dropna(subset=['Data da venda'], inplace=True)

    fuso_aracaju = pytz.timezone('America/Maceio')
    if df_validos['Data da venda'].dt.tz is None:
        df_validos['Data da venda'] = df_validos['Data da venda'].dt.tz_localize('UTC').dt.tz_convert(fuso_aracaju)
    else:
        df_validos['Data da venda'] = df_validos['Data da venda'].dt.tz_convert(fuso_aracaju)
    
    df_validos['Data'] = df_validos['Data da venda'].dt.date
    df_validos['Hora'] = df_validos['Data da venda'].dt.hour
    
    day_map = {0: '1. Segunda', 1: '2. Terça', 2: '3. Quarta', 3: '4. Quinta', 4: '5. Sexta', 5: '6. Sábado', 6: '7. Domingo'}
    df_validos['Dia da Semana'] = pd.to_datetime(df_validos['Data']).dt.weekday.map(day_map)
    
    cols_numericas = ['Itens', 'Total taxa de serviço', 'Total', 'Entrega', 'Acréscimo', 'Desconto']
    for col in cols_numericas:
        if col in df_validos.columns:
            df_validos[col] = pd.to_numeric(df_validos[col], errors='coerce').fillna(0)

    delivery_channels_padronizados = ['IFOOD', 'SITE DELIVERY (SAIPOS)', 'BRENDI']
    if 'Canal de venda' in df_validos.columns:
        df_validos['Tipo de Canal'] = df_validos['Canal de venda'].astype(str).apply(padronizar_texto).apply(lambda x: 'Delivery' if x in delivery_channels_padronizados else 'Salão/Telefone')
    
    if 'Bairro' in df_validos.columns:
        df_validos['Bairro'] = df_validos['Bairro'].astype(str).apply(padronizar_texto)

    return df_validos, df_cancelados

def create_gradient_line_chart(df_data):
    """Cria um gráfico de linha com cores de gradiente para subidas e descidas."""
    df_data = df_data.copy()
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
col_logo, col_title = st.columns([1, 25])
with col_logo:
    st.image("https://site.labrasaburger.com.br/wp-content/uploads/2021/09/logo.png", width=50)
with col_title:
    st.title("Dashboard de Vendas La Brasa")

with st.spinner("Conectando à Planilha Google e processando dados..."):
    df_validos_raw, df_cancelados_raw = carregar_dados_das_planilhas()
    df_validos, df_cancelados = tratar_dados(df_validos_raw, df_cancelados_raw)
    df_ceps_database = carregar_base_ceps()

if df_validos is None or df_validos.empty:
    st.error("Não foi possível carregar ou tratar os dados da Planilha Google. Verifique se a planilha tem dados ou execute a atualização.")
    st.stop()

# --- Corpo Principal do Dashboard ---
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

with abas[0]:
    st.subheader("Resumo do Período Selecionado")
    col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
    faturamento_total = df_filtrado['Total'].sum()
    with col_kpi1: st.metric(label="📈 FATURAMENTO TOTAL", value=format_currency(faturamento_total))
    with col_kpi2: st.metric(label="Total de Pedidos Válidos", value=df_filtrado['Pedido'].nunique())
    with col_kpi3: 
        if df_filtrado['Pedido'].nunique() > 0:
            st.metric(label="Ticket Médio", value=format_currency(faturamento_total / df_filtrado['Pedido'].nunique()))
    
    st.divider()

    st.subheader("Evolução do Faturamento Diário")
    faturamento_diario = df_filtrado.groupby('Data')['Total'].sum().reset_index()
    if not faturamento_diario.empty and len(faturamento_diario) > 1:
        fig_faturamento = create_gradient_line_chart(faturamento_diario)
        st.plotly_chart(fig_faturamento, use_container_width=True)

with abas[1]:
    st.header("Análise de Delivery")
    df_delivery_filtrado = df_filtrado[df_filtrado['Tipo de Canal'] == 'Delivery']
    if not df_delivery_filtrado.empty:
        st.markdown("##### Mapa de Calor de Pedidos por CEP")
        if df_ceps_database is not None:
            pedidos_por_cep = df_delivery_filtrado['CEP'].dropna().value_counts().reset_index()
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
                st.warning("Nenhum CEP do relatório foi encontrado no seu cache. Rode `python build_cep_cache.py` para atualizar.")
        else:
            st.warning("`cep_cache.csv` não encontrado. Rode `python build_cep_cache.py` para gerar o mapa.")
    else:
        st.info("Nenhum pedido de delivery no período selecionado.")

with abas[2]:
    st.subheader("Análise de Pedidos Cancelados")
    if df_cancelados is not None and not df_cancelados.empty:
        st.dataframe(df_cancelados)
    else:
        st.info("Nenhum pedido cancelado no período.")
