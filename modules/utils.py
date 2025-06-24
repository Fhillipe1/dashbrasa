import streamlit as st
import pandas as pd
import os
import plotly.graph_objects as go
from datetime import datetime
import unicodedata
import pytz

# Esta função de formatação é uma utilidade geral
def format_currency(value):
    """Formata um número para o padrão de moeda brasileiro (R$ 1.234,56)."""
    if pd.isna(value):
        return "R$ 0,00"
    s = f'{value:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
    return f"R$ {s}"

# As funções de carregamento de dados ficam aqui
@st.cache_data
def carregar_dados_brutos():
    """Carrega o relatório .xlsx mais recente, lendo a data como texto."""
    caminho_relatorios = 'relatorios_saipos'
    if not os.path.exists(caminho_relatorios): return None
    arquivos_xlsx = [f for f in os.listdir(caminho_relatorios) if f.endswith('.xlsx')]
    if not arquivos_xlsx: return None
    caminho_completo = os.path.join(caminho_relatorios, max(arquivos_xlsx, key=lambda f: os.path.getmtime(os.path.join(caminho_relatorios, f))))
    try:
        return pd.read_excel(caminho_completo, dtype={'Data da venda': str})
    except Exception as e:
        st.error(f"Erro ao ler o arquivo de relatório: {e}")
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
    """Aplica todas as transformações, incluindo a correção de fuso horário e o formato de data correto."""
    if df is None: return None, None
    
    df.columns = [str(col) for col in df.columns]

    if 'Pedido' in df.columns: df['Pedido'] = df['Pedido'].astype(str)
    if 'CEP' in df.columns: df['CEP'] = df['CEP'].astype(str).str.replace(r'\D', '', regex=True).str.zfill(8)
    if 'Bairro' in df.columns: df['Bairro'] = df['Bairro'].astype(str).apply(padronizar_texto)
    
    df_cancelados = df[df['Esta cancelado'] == 'S'].copy()
    df_validos = df[df['Esta cancelado'] == 'N'].copy()
    
    # --- CORREÇÃO DE DATA/HORA APLICADA AQUI ---
    df_validos['Data da venda'] = pd.to_datetime(df_validos['Data da venda'], dayfirst=True, errors='coerce')
    df_validos.dropna(subset=['Data da venda'], inplace=True)
    
    df_validos['Data da venda'] = df_validos['Data da venda'] - pd.Timedelta(hours=3)
    
    fuso_aracaju = pytz.timezone('America/Maceio')
    df_validos['Data da venda'] = df_validos['Data da venda'].dt.tz_localize(fuso_aracaju, ambiguous='infer')
    
    hoje = datetime.now(fuso_aracaju)
    df_validos = df_validos[df_validos['Data da venda'] <= hoje]

    df_validos['Data'] = df_validos['Data da venda'].dt.date
    df_validos['Hora'] = df_validos['Data da venda'].dt.hour
    
    day_map = {0: '1. Segunda', 1: '2. Terça', 2: '3. Quarta', 3: '4. Quinta', 4: '5. Sexta', 5: '6. Sábado', 6: '7. Domingo'}
    df_validos['Dia da Semana'] = df_validos['Data da venda'].dt.weekday.map(day_map)
    
    cols_numericas = ['Itens', 'Total taxa de serviço', 'Total', 'Entrega', 'Acréscimo', 'Desconto']
    for col in cols_numericas:
        if col in df_validos.columns:
            df_validos[col] = pd.to_numeric(df_validos[col], errors='coerce').fillna(0)

    delivery_channels_padronizados = ['IFOOD', 'SITE DELIVERY (SAIPOS)', 'BRENDI']
    df_validos['Tipo de Canal'] = df_validos['Canal de venda'].astype(str).apply(padronizar_texto).apply(
        lambda x: 'Delivery' if x in delivery_channels_padronizados else 'Salão/Telefone'
    )
    return df_validos, df_cancelados

def create_gradient_line_chart(df_data):
    """Cria um gráfico de linha com cores de gradiente."""
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
