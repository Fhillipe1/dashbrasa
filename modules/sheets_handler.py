import gspread
from gspread_dataframe import get_as_dataframe, set_with_dataframe
import pandas as pd
import numpy as np
import os
import streamlit as st
import json

def update_sheet_with_new_data(df_new_data):
    """
    Atualiza uma Planilha Google com novos dados de um DataFrame, evitando duplicatas
    e incluindo o cabeçalho na primeira carga. Autentica de forma flexível 
    para funcionar tanto localmente quanto no Streamlit Cloud.
    """
    try:
        # --- LÓGICA DE AUTENTICAÇÃO ATUALIZADA (LOCAL E NUVEM) ---
        
        # Tenta autenticar via Streamlit Secrets (para quando estiver na nuvem)
        if 'google_credentials' in st.secrets:
            print("Autenticando via Streamlit Secrets (Modo Nuvem)...")
            creds_dict = st.secrets["google_credentials"]
            gc = gspread.service_account_from_dict(creds_dict)
            sheet_name = st.secrets.get("GOOGLE_SHEET_NAME")
        else:
            # Se não encontrar os segredos, volta para o método local (usando o arquivo .json)
            print("Autenticando via arquivo local google_credentials.json (Modo Local)...")
            credentials_file = os.getenv("GOOGLE_CREDENTIALS_FILE", "google_credentials.json")
            if not os.path.exists(credentials_file):
                st.error(f"ERRO: Arquivo de credenciais '{credentials_file}' não encontrado para execução local.")
                return -1
            gc = gspread.service_account(filename=credentials_file)
            sheet_name = os.getenv("GOOGLE_SHEET_NAME")

        if not sheet_name:
            st.error("ERRO: O nome da planilha (GOOGLE_SHEET_NAME) não foi encontrado nos seus segredos ou no arquivo .env.")
            return -1

        # --- O RESTO DA FUNÇÃO CONTINUA IGUAL ---

        spreadsheet = gc.open(sheet_name)
        worksheet = spreadsheet.get_worksheet(0)
        print(f"Conectado com sucesso à planilha '{sheet_name}'.")

        df_existing = get_as_dataframe(worksheet, evaluate_formulas=False, header=0)
        # Remove colunas vazias que o gspread pode criar
        df_existing.dropna(how='all', axis=1, inplace=True)
        print(f"Encontradas {len(df_existing)} linhas existentes na planilha.")

        # Limpa os valores NaN do novo dataframe para evitar erros na API
        df_new_data_cleaned = df_new_data.astype(object).replace(np.nan, '')

        if df_existing.empty:
            print("Planilha está vazia. Escrevendo cabeçalho e todos os dados...")
            set_with_dataframe(worksheet, df_new_data_cleaned)
            num_new_rows = len(df_new_data_cleaned)
            print(f"{num_new_rows} linhas adicionadas com sucesso.")
        else:
            # Garante que os nomes das colunas de ambos os dataframes sejam os mesmos para a comparação
            df_existing.columns = df_new_data_cleaned.columns
            
            df_existing_str = df_existing.astype(str)
            df_new_data_str = df_new_data_cleaned.astype(str)
            
            # Identifica as linhas que não estão no df_existing
            df_to_add_str = df_new_data_str.loc[~df_new_data_str.isin(df_existing_str.to_dict(orient='list')).all(axis=1)]

            # Pega os dados originais correspondentes aos índices das novas linhas
            df_to_add = df_new_data_cleaned.iloc[df_to_add_str.index]
            
            num_new_rows = len(df_to_add)
            if num_new_rows > 0:
                print(f"Adicionando {num_new_rows} novas linhas à planilha...")
                worksheet.append_rows(df_to_add.values.tolist(), value_input_option='USER_ENTERED')
                print("Planilha atualizada com sucesso.")
            else:
                print("Nenhuma linha nova para adicionar. A planilha já está atualizada.")

        return num_new_rows

    except gspread.exceptions.SpreadsheetNotFound:
        st.error(f"ERRO: Planilha com o nome '{sheet_name}' não encontrada. Verifique o nome e se você a compartilhou com o e-mail do robô.")
        return -1
    except Exception as e:
        st.error(f"ERRO ao interagir com o Google Sheets: {e}")
        return -1