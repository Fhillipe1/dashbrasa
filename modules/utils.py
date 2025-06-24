import pandas as pd
from datetime import datetime
import unicodedata
import pytz

def format_currency(value):
    if pd.isna(value): return "R$ 0,00"
    s = f'{value:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
    return f"R$ {s}"

def padronizar_texto(texto):
    if not isinstance(texto, str): return texto
    texto = ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
    return texto.strip().upper()

def tratar_dados(df):
    """Esta função agora é a única responsável por limpar e preparar os dados brutos da Saipos."""
    if df is None: return None, None
    
    df.columns = [str(col) for col in df.columns]
    if 'Pedido' in df.columns: df['Pedido'] = df['Pedido'].astype(str)
    if 'CEP' in df.columns: df['CEP'] = df['CEP'].astype(str).str.replace(r'\D', '', regex=True).str.zfill(8)
    if 'Bairro' in df.columns: df['Bairro'] = df['Bairro'].astype(str).apply(padronizar_texto)
    
    df_cancelados = df[df['Esta cancelado'] == 'S'].copy()
    df_validos = df[df['Esta cancelado'] == 'N'].copy()
    
    # Corrige a data para ambos os dataframes
    for temp_df in [df_validos, df_cancelados]:
        if not temp_df.empty:
            temp_df['Data da venda'] = pd.to_datetime(temp_df['Data da venda'], dayfirst=True, errors='coerce')
            temp_df.dropna(subset=['Data da venda'], inplace=True)
            temp_df['Data da venda'] = temp_df['Data da venda'] - pd.Timedelta(hours=3)
            fuso_aracaju = pytz.timezone('America/Maceio')
            temp_df['Data da venda'] = temp_df['Data da venda'].dt.tz_localize(fuso_aracaju, ambiguous='infer')

    # Cria colunas adicionais apenas para os dados válidos
    if not df_validos.empty:
        hoje = datetime.now(pytz.timezone('America/Maceio'))
        df_validos = df_validos[df_validos['Data da venda'] <= hoje].copy()
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
