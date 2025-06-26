# modules/data_handler.py
import streamlit as st
import pandas as pd
import gspread
from gspread_dataframe import set_with_dataframe, get_as_dataframe
import numpy as np
import unicodedata
import pytz
from datetime import datetime
import textwrap

# --- FUNÇÕES DE AUTENTICAÇÃO E CONEXÃO ---

def _get_google_sheets_client():
    try:
        return gspread.service_account_from_dict(st.secrets["google_credentials"])
    except Exception as e:
        print(f"Erro ao autenticar com o Google Sheets: {e}")
        return None

# --- FUNÇÕES DE DADOS ---

def tratar_dados_saipos(df_bruto):
    if df_bruto is None or df_bruto.empty:
        return pd.DataFrame(), pd.DataFrame()
    df = df_bruto.copy()
    df.columns = [str(col).strip() for col in df.columns]
    if 'Pedido' not in df.columns:
        st.error("ERRO CRÍTICO: Coluna 'Pedido' não encontrada no relatório.")
        return pd.DataFrame(), pd.DataFrame()
    df['Pedido'] = df['Pedido'].astype(str)
    if 'CEP' in df.columns:
        df['CEP'] = df['CEP'].astype(str).str.replace(r'\D', '', regex=True).str.zfill(8)
    if 'Bairro' in df.columns:
        df['Bairro'] = df['Bairro'].apply(_padronizar_texto)
    df_cancelados = df[df['Esta cancelado'] == 'S'].copy()
    df_validos = df[df['Esta cancelado'] == 'N'].copy()
    fuso_horario = pytz.timezone('America/Maceio')
    day_map = {0: '1. Segunda', 1: '2. Terça', 2: '3. Quarta', 3: '4. Quinta', 4: '5. Sexta', 5: '6. Sábado', 6: '7. Domingo'}
    for temp_df in [df_validos, df_cancelados]:
        if not temp_df.empty and 'Data da venda' in temp_df.columns:
            temp_df['Data da venda'] = pd.to_datetime(temp_df['Data da venda'], dayfirst=True, errors='coerce')
            temp_df.dropna(subset=['Data da venda'], inplace=True)
            if temp_df['Data da venda'].dt.tz is None:
                temp_df['Data da venda'] = temp_df['Data da venda'].dt.tz_localize(fuso_horario)
            else:
                temp_df['Data da venda'] = temp_df['Data da venda'].dt.tz_convert(fuso_horario)
            temp_df['Data'] = temp_df['Data da venda'].dt.date
            temp_df['Hora'] = temp_df['Data da venda'].dt.hour
            temp_df['Ano'] = temp_df['Data da venda'].dt.year
            temp_df['Mês'] = temp_df['Data da venda'].dt.month
            temp_df['Dia da Semana'] = temp_df['Data da venda'].dt.weekday.map(day_map)
    if not df_validos.empty:
        cols_numericas = ['Itens', 'Total taxa de serviço', 'Total', 'Entrega', 'Acréscimo', 'Desconto']
        for col in cols_numericas:
            if col in df_validos.columns:
                df_validos[col] = pd.to_numeric(df_validos[col], errors='coerce').fillna(0)
        delivery_channels = ['IFOOD', 'SITE DELIVERY (SAIPOS)', 'BRENDI']
        if 'Canal de venda' in df_validos.columns:
            df_validos['Canal de venda Padronizado'] = df_validos['Canal de venda'].apply(_padronizar_texto)
            df_validos['Tipo de Canal'] = np.where(df_validos['Canal de venda Padronizado'].isin(delivery_channels), 'Delivery', 'Salão/Telefone')
    for temp_df in [df_validos, df_cancelados]:
        # Converte as colunas de data/hora para texto para salvar na planilha
        if 'Data da venda' in temp_df.columns:
            # Primeiro, garante que é datetime para poder usar .dt
            temp_df['Data da venda'] = pd.to_datetime(temp_df['Data da venda'], errors='coerce')
            temp_df['Data da venda'] = temp_df['Data da venda'].dt.strftime('%Y-%m-%d %H:%M:%S')
        if 'Data' in temp_df.columns:
            temp_df['Data'] = temp_df['Data'].astype(str)
    return df_validos, df_cancelados

def _padronizar_texto(texto):
    if not isinstance(texto, str): return texto
    return ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn').strip().upper()

def carregar_dados_para_gsheets(df_novos_validos, df_novos_cancelados):
    gc = _get_google_sheets_client()
    if gc is None: return
    sheet_name = st.secrets.get("GOOGLE_SHEET_NAME")
    if not sheet_name: return
    try:
        spreadsheet = gc.open(sheet_name)
        # Usa a nova função simplificada para ambas as abas
        _atualizar_aba_robusta(spreadsheet, "Página1", df_novos_validos)
        _atualizar_aba_robusta(spreadsheet, "Cancelados", df_novos_cancelados)
        st.success("Planilhas atualizadas com sucesso!")
    except Exception as e:
        st.error(f"Ocorreu um erro ao carregar os dados para o Google Sheets: {e}")

# --- FUNÇÃO DE ATUALIZAÇÃO SIMPLIFICADA ---
def _atualizar_aba_robusta(spreadsheet, nome_aba, df_novos):
    """
    Limpa completamente uma aba e insere os novos dados do relatório.
    Esta é a forma mais segura de evitar duplicatas.
    """
    st.write(f"Atualizando a aba '{nome_aba}'...")
    try:
        worksheet = spreadsheet.worksheet(nome_aba)
        st.write(f"Limpando dados antigos da aba '{nome_aba}'...")
        worksheet.clear() 
    except gspread.WorksheetNotFound:
        st.write(f"Aba '{nome_aba}' não encontrada. Criando uma nova...")
        worksheet = spreadsheet.add_worksheet(title=nome_aba, rows="1", cols=len(df_novos.columns) if not df_novos.empty else 20)
    
    st.write(f"Inserindo {len(df_novos)} linhas na aba '{nome_aba}'...")
    # Converte tudo para string para máxima compatibilidade com o Google Sheets
    set_with_dataframe(worksheet, df_novos.astype(str), include_index=False, resize=True)
    st.success(f"Aba '{nome_aba}' sincronizada!")

def ler_dados_do_gsheets():
    """Lê os dados do Google Sheets. Retorna dataframes vazios em caso de erro."""
    try:
        gc = _get_google_sheets_client()
        if gc is None: print("Falha na conexão com o Google Sheets."); return pd.DataFrame(), pd.DataFrame()
        sheet_name = st.secrets.get("GOOGLE_SHEET_NAME");
        if not sheet_name: print("Nome da planilha não configurado nos segredos."); return pd.DataFrame(), pd.DataFrame()
        spreadsheet = gc.open(sheet_name)
        df_validos = get_as_dataframe(spreadsheet.worksheet("Página1"), evaluate_formulas=False).dropna(how='all')
        df_cancelados = get_as_dataframe(spreadsheet.worksheet("Cancelados"), evaluate_formulas=False).dropna(how='all')
        return df_validos, df_cancelados
    except Exception as e:
        print(f"Ocorreu um erro ao ler os dados do Google Sheets: {e}")
        return pd.DataFrame(), pd.DataFrame()
