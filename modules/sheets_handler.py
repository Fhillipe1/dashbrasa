import streamlit as st
import gspread
from gspread_dataframe import get_as_dataframe, set_with_dataframe
import pandas as pd
import numpy as np
import os

def get_google_sheets_client():
    """Autentica no Google Sheets de forma flexível (local vs. nuvem) e retorna o cliente."""
    try:
        if "google_credentials" in st.secrets:
            creds_dict = st.secrets.get("google_credentials")
            gc = gspread.service_account_from_dict(creds_dict)
            return gc
        else:
            credentials_file = "google_credentials.json"
            if os.path.exists(credentials_file):
                gc = gspread.service_account(filename=credentials_file)
                return gc
            else:
                st.error(f"ERRO: Arquivo de credenciais '{credentials_file}' não encontrado.")
                return None
    except Exception as e:
        st.error(f"Falha na autenticação com o Google Sheets: {e}")
        return None

def read_data_from_sheets():
    """Lê os dados das abas 'Vendas Validas' e 'Cancelados' da Planilha Google."""
    gc = get_google_sheets_client()
    if gc is None: return None, None
    
    sheet_name = st.secrets.get("GOOGLE_SHEET_NAME") or os.getenv("GOOGLE_SHEET_NAME")
    if not sheet_name:
        st.error("ERRO: GOOGLE_SHEET_NAME não configurado.")
        return None, None
    
    try:
        spreadsheet = gc.open(sheet_name)
        
        print("Lendo a aba 'Vendas Validas'...")
        worksheet_validos = spreadsheet.get_worksheet(0)
        df_validos = get_as_dataframe(worksheet_validos, evaluate_formulas=False, header=0)
        df_validos.dropna(how='all', axis=1, inplace=True)
        
        print("Lendo a aba 'Cancelados'...")
        worksheet_cancelados = spreadsheet.get_worksheet(1)
        df_cancelados = get_as_dataframe(worksheet_cancelados, evaluate_formulas=False, header=0)
        df_cancelados.dropna(how='all', axis=1, inplace=True)
        
        print("Leitura da Planilha Google concluída.")
        return df_validos, df_cancelados
    except Exception as e:
        st.error(f"ERRO ao ler dados da Planilha Google: {e}")
        return None, None

def update_target_sheet(spreadsheet, worksheet_index, df_new):
    """Função genérica para atualizar uma aba específica pelo seu índice."""
    worksheet = spreadsheet.get_worksheet(worksheet_index)
    worksheet_name = worksheet.title
    
    df_existing = get_as_dataframe(worksheet, evaluate_formulas=False, header=0)
    df_existing.dropna(how='all', axis=1, inplace=True)
    df_new_cleaned = df_new.astype(object).replace(np.nan, '')

    if df_existing.empty:
        print(f"Aba '{worksheet_name}' vazia. Escrevendo cabeçalho e {len(df_new_cleaned)} linhas.")
        set_with_dataframe(worksheet, df_new_cleaned)
        return len(df_new_cleaned)
    else:
        df_existing.columns = df_new_cleaned.columns
        df_combined = pd.concat([df_existing.astype(str), df_new_cleaned.astype(str)]).drop_duplicates(keep=False)
        num_new_rows = len(df_combined)

        if num_new_rows > 0:
            print(f"Adicionando {num_new_rows} novas linhas à aba '{worksheet_name}'...")
            worksheet.append_rows(df_combined.values.tolist(), value_input_option='USER_ENTERED')
        else:
            print(f"Nenhuma linha nova para adicionar em '{worksheet_name}'.")
        return num_new_rows

def sync_with_google_sheets(df_validos, df_cancelados):
    """Orquestra a atualização das abas de vendas válidas e canceladas."""
    gc = get_google_sheets_client()
    if gc is None: return -1, -1

    sheet_name = st.secrets.get("GOOGLE_SHEET_NAME") or os.getenv("GOOGLE_SHEET_NAME")
    if not sheet_name: return -1, -1
    
    try:
        spreadsheet = gc.open(sheet_name)
        validos_added = update_target_sheet(spreadsheet, 0, df_validos) # 1ª Aba
        cancelados_added = update_target_sheet(spreadsheet, 1, df_cancelados) # 2ª Aba
        return validos_added, cancelados_added
    except Exception as e:
        print(f"ERRO ao sincronizar com o Google Sheets: {e}")
        return -1, -1
