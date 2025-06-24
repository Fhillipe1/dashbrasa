import streamlit as st
import pandas as pd
from datetime import datetime
import unicodedata
import pytz

# Importa a nova função de leitura do nosso outro módulo
from modules.sheets_handler import read_data_from_sheet

def carregar_dados_brutos():
    """
    Função principal para carregar os dados. 
    Agora ela lê DIRETAMENTE da Planilha Google.
    """
    return read_data_from_sheet()

def padronizar_texto(texto):
    """Função para limpar e padronizar texto."""
    if not isinstance(texto, str): return texto
    texto = ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
    return texto.strip().upper()

def tratar_dados(df):
    """Aplica todas as transformações e limpezas necessárias no DataFrame."""
    # (Esta função continua exatamente a mesma, sem nenhuma alteração)
    if df is None: return None, None
    if 'Pedido' in df.columns: df['Pedido'] = df['Pedido'].astype(str)
    if 'CEP' in df.columns: df['CEP'] = df['CEP'].astype(str).str.replace(r'\D', '', regex=True).str.zfill(8)
    if 'Bairro' in df.columns: df['Bairro'] = df['Bairro'].astype(str).apply(padronizar_texto)
    df_cancelados = df[df['Esta cancelado'] == 'S'].copy()
    df_validos = df[df['Esta cancelado'] == 'N'].copy()
    df_validos['Data da venda'] = pd.to_datetime(df_validos['Data da venda'], dayfirst=True, errors='coerce')
    df_validos.dropna(subset=['Data da venda'], inplace=True)
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
    df_validos['Tipo de Canal'] = df_validos['Canal de venda'].astype(str).apply(padronizar_texto).apply(lambda x: 'Delivery' if x in delivery_channels_padronizados else 'Salão/Telefone')
    return df_validos, df_cancelados
