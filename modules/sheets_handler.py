import streamlit as st
import gspread
from gspread_dataframe import get_as_dataframe, set_with_dataframe
import pandas as pd
import numpy as np
import os

def update_sheet_with_new_data(df_new_data):
    """
    Atualiza uma Planilha Google com novos dados, usando st.secrets para a nuvem
    e o arquivo .json para execução local.
    """
    try:
        sheet_name = st.secrets.get("GOOGLE_SHEET_NAME") or os.getenv("GOOGLE_SHEET_NAME")
        
        # --- LÓGICA DE AUTENTICAÇÃO ATUALIZADA ---
        # Tenta autenticar via Streamlit Secrets (para quando estiver na nuvem)
        if "google_credentials" in st.secrets:
            print("Autenticando via Streamlit Secrets (Modo Nuvem)...")
            creds_dict = st.secrets.get("google_credentials")
            gc = gspread.service_account_from_dict(creds_dict)
        else:
            # Se não encontrar os segredos, volta para o método local
            print("Autenticando via arquivo local (Modo Local)...")
            credentials_file = "google_credentials.json"
            if not os.path.exists(credentials_file):
                st.error(f"ERRO: Arquivo de credenciais '{credentials_file}' não encontrado.")
                return -1
            gc = gspread.service_account(filename=credentials_file)

        if not sheet_name:
            st.error("ERRO: Nome da planilha (GOOGLE_SHEET_NAME) não encontrado.")
            return -1

        spreadsheet = gc.open(sheet_name)
        worksheet = spreadsheet.get_worksheet(0)
        print(f"Conectado com sucesso à planilha '{sheet_name}'.")

        df_existing = get_as_dataframe(worksheet, evaluate_formulas=False, header=0)
        df_existing.dropna(how='all', axis=1, inplace=True)
        print(f"Encontradas {len(df_existing)} linhas existentes na planilha.")
        
        df_new_data_cleaned = df_new_data.astype(object).replace(np.nan, '')

        if df_existing.empty:
            print("Planilha está vazia. Escrevendo cabeçalho e todos os dados...")
            set_with_dataframe(worksheet, df_new_data_cleaned)
            num_new_rows = len(df_new_data_cleaned)
            print(f"{num_new_rows} linhas adicionadas com sucesso.")
        else:
            df_existing.columns = df_new_data_cleaned.columns.copy()
            df_existing_str = df_existing.astype(str)
            df_new_data_str = df_new_data_cleaned.astype(str)
            
            # Combina os dataframes em um só para encontrar duplicatas
            combined = pd.concat([df_existing_str, df_new_data_str], ignore_index=True)
            # Mantém apenas a primeira ocorrência de cada linha única
            unique_rows = combined.drop_duplicates(keep='first')
            
            # O número de novas linhas é a diferença de tamanho
            num_new_rows = len(unique_rows) - len(df_existing_str)
            
            if num_new_rows > 0:
                print(f"Adicionando {num_new_rows} novas linhas à planilha...")
                # Pega apenas as últimas N linhas, que são as novas
                df_to_add = unique_rows.tail(num_new_rows)
                worksheet.append_rows(df_to_add.values.tolist(), value_input_option='USER_ENTERED')
                print("Planilha atualizada com sucesso.")
            else:
                print("Nenhuma linha nova para adicionar. A planilha já está atualizada.")

        return num_new_rows

    except gspread.exceptions.SpreadsheetNotFound:
        st.error(f"ERRO: Planilha '{sheet_name}' não encontrada. Verifique o nome e se foi compartilhada com o e-mail do robô.")
        return -1
    except Exception as e:
        st.error(f"ERRO ao interagir com o Google Sheets: {e}")
        return -1
