import streamlit as st
import gspread
from gspread_dataframe import get_as_dataframe, set_with_dataframe
import pandas as pd
import numpy as np
import os

def get_google_sheets_client():
    """Autentica e retorna o cliente do Google Sheets."""
    if "google_credentials" in st.secrets:
        return gspread.service_account_from_dict(st.secrets.get("google_credentials"))
    else:
        credentials_file = "google_credentials.json"
        if os.path.exists(credentials_file):
            return gspread.service_account(filename=credentials_file)
    st.error("Credenciais do Google não encontradas.")
    return None

def update_target_sheet(gc, sheet_name, worksheet_name, df_new):
    """Função genérica para atualizar uma aba específica, evitando duplicatas."""
    spreadsheet = gc.open(sheet_name)
    try:
        worksheet = spreadsheet.worksheet(worksheet_name)
    except gspread.exceptions.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title=worksheet_name, rows="1", cols="1")

    df_existing = get_as_dataframe(worksheet, evaluate_formulas=False, header=0)
    df_existing.dropna(how='all', axis=1, inplace=True)
    
    df_new_cleaned = df_new.astype(object).replace(np.nan, '')

    if df_existing.empty:
        print(f"Planilha '{worksheet_name}' vazia. Escrevendo todos os {len(df_new_cleaned)} dados.")
        set_with_dataframe(worksheet, df_new_cleaned)
        return len(df_new_cleaned)
    else:
        # Lógica para não duplicar
        df_existing.columns = df_new_cleaned.columns
        df_combined = pd.concat([df_existing.astype(str), df_new_cleaned.astype(str)]).drop_duplicates(keep=False)
        num_new_rows = len(df_combined)

        if num_new_rows > 0:
            print(f"Adicionando {num_new_rows} novas linhas à planilha '{worksheet_name}'...")
            worksheet.append_rows(df_combined.values.tolist(), value_input_option='USER_ENTERED')
        else:
            print(f"Nenhuma linha nova para adicionar em '{worksheet_name}'.")
        return num_new_rows

def sync_with_google_sheets(df_validos, df_cancelados):
    """Orquestra a atualização das abas de vendas válidas e canceladas."""
    gc = get_google_sheets_client()
    if gc is None: return -1, -1

    sheet_name = st.secrets.get("GOOGLE_SHEET_NAME") or os.getenv("GOOGLE_SHEET_NAME")
    if not sheet_name:
        st.error("Nome da planilha (GOOGLE_SHEET_NAME) não encontrado.")
        return -1, -1

    print("--- Sincronizando Vendas Válidas ---")
    validos_added = update_target_sheet(gc, sheet_name, 'Vendas Validas', df_validos)
    
    print("--- Sincronizando Vendas Canceladas ---")
    cancelados_added = update_target_sheet(gc, sheet_name, 'Cancelados', df_cancelados)

    return validos_added, cancelados_added
