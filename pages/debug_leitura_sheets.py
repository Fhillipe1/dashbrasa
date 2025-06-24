import streamlit as st
import pandas as pd
import os
import gspread
from gspread_dataframe import get_as_dataframe
from dotenv import load_dotenv
from io import StringIO
import pytz

st.set_page_config(page_title="Debug de Dados", page_icon="🔬")
st.title("🔬 Ferramenta de Diagnóstico de Dados da Planilha")
st.info("Use esta página para inspecionar os dados brutos lidos da Planilha Google, incluindo a análise de datas e a verificação de linhas duplicadas.")

# Função de autenticação isolada para este teste
@st.cache_data
def carregar_dados_brutos_para_debug():
    """Lê os dados da primeira aba da Planilha Google para diagnóstico."""
    load_dotenv()
    df_validos = pd.DataFrame()
    try:
        if "google_credentials" in st.secrets:
            creds_dict = st.secrets.get("google_credentials")
            gc = gspread.service_account_from_dict(creds_dict)
        else:
            credentials_file = "google_credentials.json"
            if not os.path.exists(credentials_file):
                st.error(f"ERRO: Arquivo de credenciais '{credentials_file}' não encontrado.")
                return None
            gc = gspread.service_account(filename=credentials_file)

        sheet_name = st.secrets.get("GOOGLE_SHEET_NAME") or os.getenv("GOOGLE_SHEET_NAME")
        if not sheet_name:
            st.error("ERRO: GOOGLE_SHEET_NAME não configurado.")
            return None
        
        spreadsheet = gc.open(sheet_name)
        worksheet = spreadsheet.get_worksheet(0) # Pega a primeira aba
        df_validos = get_as_dataframe(worksheet, evaluate_formulas=False, header=0)
        df_validos.dropna(how='all', axis=1, inplace=True)
        return df_validos
    except Exception as e:
        st.error(f"ERRO ao ler a Planilha Google: {e}")
        return None

if st.button("▶️ Iniciar Inspeção Completa"):
    
    with st.spinner("Conectando e lendo a planilha..."):
        df_raw = carregar_dados_brutos_para_debug()

    if df_raw is not None and not df_raw.empty:
        st.success("Dados lidos com sucesso da Planilha!")
        
        # --- Seção de Análise de Duplicatas ---
        st.divider()
        st.subheader("Análise de Duplicatas")
        
        duplicates = df_raw[df_raw.duplicated(keep=False)]
        num_duplicates = len(duplicates)
        
        st.metric("Número de Linhas Duplicadas Encontradas", num_duplicates)
        
        if num_duplicates > 0:
            st.warning("As seguintes linhas aparecem mais de uma vez na sua planilha:")
            # Ordena para que seja fácil comparar as linhas duplicadas
            st.dataframe(duplicates.sort_values(by=list(duplicates.columns)))
        else:
            st.success("Nenhuma linha duplicada encontrada na planilha.")

        # --- Seção de Análise de Datas ---
        st.divider()
        st.subheader("Análise da Coluna 'Data da venda'")

        st.markdown("#### ETAPA 1: Dados Brutos da Planilha")
        st.write("Estes são os valores exatos, como texto, lidos da planilha:")
        st.code(df_raw['Data da venda'].head(10).to_list())
        
        st.markdown("#### ETAPA 2: Conversão para Datetime (Naive)")
        df_raw['data_convertida'] = pd.to_datetime(df_raw['Data da venda'], dayfirst=True, errors='coerce')
        st.write("Os mesmos valores após `pd.to_datetime(..., dayfirst=True)`:")
        st.code(df_raw['data_convertida'].head(10).to_list())

        st.markdown("#### ETAPA 3: Correção de Fuso Horário (UTC -> Aracaju)")
        fuso_aracaju = pytz.timezone('America/Maceio')
        # Primeiro, garantimos que a data é tratada como UTC, depois convertemos
        df_raw['data_corrigida'] = df_raw['data_convertida'].dt.tz_localize('UTC').dt.tz_convert(fuso_aracaju)
        st.write("Valores finais após a conversão de fuso horário:")
        st.code(df_raw['data_corrigida'].head(10).to_list())
        
        st.success("Compare os horários da ETAPA 1 com a ETAPA 3. A ETAPA 3 deve mostrar o horário local correto.")

    else:
        st.error("Não foi possível carregar dados da planilha ou a planilha está vazia.")
