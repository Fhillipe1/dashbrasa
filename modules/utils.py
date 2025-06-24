import streamlit as st
import pandas as pd
import os
from datetime import datetime
import unicodedata

# Colocamos o @st.cache_data aqui para que o cache funcione em todo o app
# Versão CORRIGIDA
@st.cache_data
def carregar_dados_brutos():
    """Carrega o relatório .xlsx mais recente, tratando a coluna de data como texto."""
    caminho_relatorios = 'relatorios_saipos'
    if not os.path.exists(caminho_relatorios): return None
    
    arquivos_xlsx = [f for f in os.listdir(caminho_relatorios) if f.endswith('.xlsx')]
    if not arquivos_xlsx: return None
    
    caminho_completo = os.path.join(caminho_relatorios, max(arquivos_xlsx, 
                                     key=lambda f: os.path.getmtime(os.path.join(caminho_relatorios, f))))
    try:
        # --- MUDANÇA CRÍTICA AQUI ---
        # Forçamos a leitura da coluna 'Data da venda' como texto (string)
        # para evitar a conversão automática de fuso horário do pandas.
        df = pd.read_excel(
            caminho_completo,
            dtype={'Data da venda': str} 
        )
        return df
    except Exception as e:
        st.error(f"Erro ao ler o arquivo de relatório: {e}")
        return None

def tratar_dados(df):
    """Aplica todas as transformações, incluindo a correção explícita de fuso horário."""
    if df is None: return None, None
    if 'Pedido' in df.columns: df['Pedido'] = df['Pedido'].astype(str)
    if 'CEP' in df.columns: df['CEP'] = df['CEP'].astype(str).str.replace(r'\D', '', regex=True).str.zfill(8)
    
    def padronizar_texto(texto):
        if not isinstance(texto, str): return texto
        texto = ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
        return texto.strip().upper()

    if 'Bairro' in df.columns: df['Bairro'] = df['Bairro'].astype(str).apply(padronizar_texto)
    df_cancelados = df[df['Esta cancelado'] == 'S'].copy()
    df_validos = df[df['Esta cancelado'] == 'N'].copy()
    
    # --- LÓGICA DE DATA/HORA ATUALIZADA E ROBUSTA ---
    # 1. Converte para datetime "ingênuo", como antes
    df_validos['Data da venda'] = pd.to_datetime(df_validos['Data da venda'], dayfirst=True, errors='coerce')
    df_validos.dropna(subset=['Data da venda'], inplace=True)
    
    # 2. --- CORREÇÃO FINAL E DEFINITIVA ---
    # Subtrai 3 horas para corrigir a conversão automática do servidor (UTC -> BRT)
    df_validos['Data da venda'] = df_validos['Data da venda'] - pd.Timedelta(hours=3)
    
    # 3. Define o fuso horário correto de Aracaju
    fuso_aracaju = pytz.timezone('America/Maceio')
    df_validos['Data da venda'] = df_validos['Data da venda'].dt.tz_localize(fuso_aracaju, ambiguous='infer')
    
    # 4. Pega a hora de "agora" no mesmo fuso horário para uma comparação justa
    hoje = datetime.now(fuso_aracaju)
    df_validos = df_validos[df_validos['Data da venda'] <= hoje]

    # 5. Extrai a data e a hora (agora corretas)
    df_validos['Data'] = df_validos['Data da venda'].dt.date
    df_validos['Hora'] = df_validos['Data da venda'].dt.hour
    
    day_map = {0: '1. Segunda', 1: '2. Terça', 2: '3. Quarta', 3: '4. Quinta', 4: '5. Sexta', 5: '6. Sábado', 6: '7. Domingo'}
    df_validos['Dia da Semana'] = df_validos['Data da venda'].dt.weekday.map(day_map)
    
    # O resto da função continua igual
    cols_numericas = ['Itens', 'Total taxa de serviço', 'Total', 'Entrega', 'Acréscimo', 'Desconto']
    for col in cols_numericas:
        if col in df_validos.columns:
            df_validos[col] = pd.to_numeric(df_validos[col], errors='coerce').fillna(0)

    delivery_channels_padronizados = ['IFOOD', 'SITE DELIVERY (SAIPOS)', 'BRENDI']
    df_validos['Tipo de Canal'] = df_validos['Canal de venda'].astype(str).apply(padronizar_texto).apply(
        lambda x: 'Delivery' if x in delivery_channels_padronizados else 'Salão/Telefone'
    )
    return df_validos, df_cancelados
