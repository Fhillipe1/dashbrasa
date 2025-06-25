# pages/3_🔄_Atualizar Relatório.py

import streamlit as st
import pandas as pd
from modules import data_handler, cep_handler

st.set_page_config(layout="wide", page_title="Atualizar Relatório de Vendas")

st.title("🔄 Atualizar Relatório de Vendas")

st.markdown("""
### Passo 1: Faça o upload do relatório
Baixe o relatório de "Vendas por Período" do sistema Saipos e faça o upload do arquivo `.xlsx` aqui.
""")

uploaded_file = st.file_uploader(
    "Selecione o arquivo .xlsx do relatório Saipos",
    type=['xlsx']
)

# Usamos o st.session_state para "lembrar" dos dados entre as interações
if 'dados_tratados' not in st.session_state:
    st.session_state.dados_tratados = None

if uploaded_file is not None:
    if st.button("Processar Arquivo"):
        with st.spinner("Lendo e tratando os dados do relatório..."):
            df_bruto = pd.read_excel(uploaded_file)
            df_validos, df_cancelados = data_handler.tratar_dados_saipos(df_bruto)
            
            if not df_validos.empty:
                st.session_state.dados_tratados = {
                    "validos": df_validos,
                    "cancelados": df_cancelados
                }
                st.success("Dados processados com sucesso! Verifique a prévia abaixo.")
            else:
                st.error("Nenhum dado válido foi encontrado no relatório. Verifique o arquivo.")
                st.session_state.dados_tratados = None

if st.session_state.dados_tratados is not None:
    st.markdown("---")
    st.subheader("Passo 2: Pré-visualização dos Dados Válidos")
    st.info(f"Encontradas **{len(st.session_state.dados_tratados['validos'])}** vendas válidas e **{len(st.session_state.dados_tratados['cancelados'])}** vendas canceladas.")
    st.markdown("Abaixo estão as primeiras 50 linhas dos dados que serão adicionados à planilha. Confira se as colunas e valores parecem corretos.")
    
    st.dataframe(st.session_state.dados_tratados['validos'].head(50))
    
    st.markdown("---")
    st.subheader("Passo 3: Salvar na Planilha")
    st.warning("Ao clicar no botão abaixo, os dados novos serão adicionados à planilha Google Sheets. Linhas duplicadas não serão salvas.", icon="⚠️")
    
    if st.button("✅ Salvar Dados na Planilha", type="primary"):
        with st.spinner("Atualizando cache de CEPs..."):
            cep_handler.atualizar_cache_cep(st.session_state.dados_tratados['validos'])
        
        with st.spinner("Conectando ao Google Sheets e salvando os novos dados..."):
            data_handler.carregar_dados_para_gsheets(
                st.session_state.dados_tratados['validos'],
                st.session_state.dados_tratados['cancelados']
            )
        
        st.success("Planilha atualizada com sucesso!")
        st.balloons()
        
        # Limpa o estado da sessão para permitir um novo upload
        st.session_state.dados_tratados = None
