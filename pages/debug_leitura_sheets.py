import streamlit as st
import pandas as pd
import os
import gspread
from gspread_dataframe import get_as_dataframe
from dotenv import load_dotenv
from io import StringIO

st.set_page_config(page_title="Debug de Leitura", page_icon="🔬")
st.title("🔬 Ferramenta de Diagnóstico de Leitura da Planilha")
st.warning("Esta página é para uso técnico. Seu objetivo é descobrir o formato exato em que as datas estão sendo lidas da Planilha Google no ambiente da nuvem.")

# Função de autenticação isolada para este teste
def get_google_sheets_client():
    load_dotenv()
    if "google_credentials" in st.secrets:
        creds_dict = st.secrets.get("google_credentials")
        return gspread.service_account_from_dict(creds_dict)
    else:
        credentials_file = "google_credentials.json"
        if os.path.exists(credentials_file):
            return gspread.service_account(filename=credentials_file)
    st.error("Falha na autenticação com o Google.")
    return None

# Função de leitura isolada para este teste
def carregar_dados_brutos_para_debug():
    gc = get_google_sheets_client()
    if gc is None: return None
    
    sheet_name = st.secrets.get("GOOGLE_SHEET_NAME") or os.getenv("GOOGLE_SHEET_NAME")
    if not sheet_name:
        st.error("GOOGLE_SHEET_NAME não configurado.")
        return None
    
    try:
        spreadsheet = gc.open(sheet_name)
        worksheet = spreadsheet.get_worksheet(0) # Pega a primeira aba
        df = get_as_dataframe(worksheet, evaluate_formulas=False, header=0)
        df.dropna(how='all', axis=1, inplace=True)
        return df
    except Exception as e:
        st.error(f"ERRO ao ler a Planilha Google: {e}")
        return None

if st.button("▶️ Iniciar Teste de Leitura da Planilha"):
    
    with st.spinner("Conectando e lendo a planilha..."):
        df_raw = carregar_dados_brutos_para_debug()

    if df_raw is not None and not df_raw.empty:
        st.success("Dados lidos com sucesso da Planilha!")
        st.divider()

        st.subheader("Amostra da Coluna 'Data da venda' (Valores Crus)")
        st.write("Abaixo estão os valores exatos, como texto, lidos da planilha antes de qualquer tratamento:")
        
        # Mostra os valores crus como uma lista para evitar formatação automática do Streamlit
        st.code(df_raw['Data da venda'].head(10).to_list())
        
        st.divider()

        st.subheader("Informações Técnicas do DataFrame (`.info()`):")
        st.write("Isto nos mostra como o `pandas` interpretou o tipo de cada coluna ao ler da planilha.")
        
        # Captura o resultado do df.info() para exibir na tela
        buffer = StringIO()
        df_raw.info(buf=buffer)
        s = buffer.getvalue()
        st.text(s)

    else:
        st.error("Não foi possível carregar dados da planilha ou a planilha está vazia.")
