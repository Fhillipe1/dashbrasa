import streamlit as st
import gspread
from gspread_dataframe import get_as_dataframe, set_with_dataframe
import pandas as pd
import numpy as np
import os
import json

def get_google_sheets_client():
    """Autentica no Google Sheets de forma flexível (local vs. nuvem) e retorna o cliente."""
    if "google_credentials" in st.secrets:
        creds_dict = st.secrets.get("google_credentials")
        gc = gspread.service_account_from_dict(creds_dict)
    else:
        credentials_file = "google_credentials.json"
        if not os.path.exists(credentials_file):
            st.error(f"ERRO: Arquivo de credenciais '{credentials_file}' não encontrado.")
            return None
        gc = gspread.service_account(filename=credentials_file)
    return gc

def read_data_from_sheet():
    """Lê todos os dados da planilha principal e retorna como um DataFrame."""
    try:
        gc = get_google_sheets_client()
        if gc is None: return None

        sheet_name = st.secrets.get("GOOGLE_SHEET_NAME") or os.getenv("GOOGLE_SHEET_NAME")
        if not sheet_name:
            st.error("ERRO: GOOGLE_SHEET_NAME não configurado.")
            return None

        print(f"Lendo dados da Planilha Google: '{sheet_name}'...")
        spreadsheet = gc.open(sheet_name)
        worksheet = spreadsheet.get_worksheet(0)
        df = get_as_dataframe(worksheet, evaluate_formulas=False, header=0)
        df.dropna(how='all', axis=1, inplace=True) # Remove colunas vazias
        print(f"Sucesso! {len(df)} linhas lidas da planilha.")
        return df

    except gspread.exceptions.SpreadsheetNotFound:
        st.error(f"ERRO: Planilha '{sheet_name}' não encontrada. Verifique o nome e o compartilhamento.")
        return None
    except Exception as e:
        st.error(f"ERRO ao ler a Planilha Google: {e}")
        return None

def update_sheet_with_new_data(df_new_data):
    """Atualiza a planilha com novos dados, evitando duplicatas."""
    try:
        gc = get_google_sheets_client()
        if gc is None: return -1

        sheet_name = st.secrets.get("GOOGLE_SHEET_NAME") or os.getenv("GOOGLE_SHEET_NAME")
        if not sheet_name: return -1
        
        spreadsheet = gc.open(sheet_name)
        worksheet = spreadsheet.get_worksheet(0)
        df_existing = get_as_dataframe(worksheet, evaluate_formulas=False, header=0)
        df_existing.dropna(how='all', axis=1, inplace=True)
        
        df_new_data_cleaned = df_new_data.astype(object).replace(np.nan, '')

        if df_existing.empty:
            set_with_dataframe(worksheet, df_new_data_cleaned)
            num_new_rows = len(df_new_data_cleaned)
        else:
            df_existing.columns = df_new_data_cleaned.columns
            df_existing_str = df_existing.astype(str)
            df_new_data_str = df_new_data_cleaned.astype(str)
            
            combined = pd.concat([df_existing_str, df_new_data_str], ignore_index=True)
            unique_rows = combined.drop_duplicates(keep='first')
            
            num_new_rows = len(unique_rows) - len(df_existing_str)
            
            if num_new_rows > 0:
                df_to_add = df_new_data_cleaned.loc[unique_rows.tail(num_new_rows).index]
                worksheet.append_rows(df_to_add.values.tolist(), value_input_option='USER_ENTERED')
        
        print(f"{num_new_rows} novas linhas adicionadas à planilha.")
        return num_new_rows

    except Exception as e:
        print(f"ERRO ao atualizar a Planilha Google: {e}")
        return -1
