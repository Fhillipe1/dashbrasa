# pages/5_🔬_Debug_de_Dados.py

import streamlit as st
from modules import data_handler, cep_handler
import os

st.set_page_config(layout="wide", page_title="Página de Depuração")

st.title("🔬 Página de Depuração e Testes")
st.markdown("""
Esta página serve para executar e testar todo o fluxo de ETL (Extração, Transformação e Carga).
- **Extração**: O robô Selenium acessa a Saipos e baixa o relatório.
- **Transformação**: Os dados do relatório são limpos, padronizados e enriquecidos.
- **Carga**: Os dados tratados são salvos no Google Sheets, e o cache de CEPs é atualizado.

Clique no botão abaixo para iniciar o processo.
""")

DOWNLOAD_PATH = os.path.join(os.getcwd(), 'relatorios_temp')

if st.button("▶️ Iniciar Extração e Teste Completo"):
    try:
        with st.spinner("ETAPA 1/4: Extraindo dados da Saipos... Isso pode levar alguns minutos."):
            df_bruto = data_handler.extrair_dados_saipos(DOWNLOAD_PATH)

        if df_bruto is not None and not df_bruto.empty:
            st.success("✅ ETAPA 1/4: Extração concluída com sucesso!")
            with st.expander("Visualizar Dados Brutos (Primeiras 5 linhas)"):
                st.dataframe(df_bruto.head())

            with st.spinner("ETAPA 2/4: Tratando e padronizando os dados..."):
                df_validos, df_cancelados = data_handler.tratar_dados_saipos(df_bruto)
            
            st.success("✅ ETAPA 2/4: Tratamento de dados concluído!")
            with st.expander("Visualizar Dados Válidos Tratados (Primeiras 5 linhas)"):
                st.dataframe(df_validos.head())
            with st.expander("Visualizar Dados Cancelados (Primeiras 5 linhas)"):
                st.dataframe(df_cancelados.head())

            with st.spinner("ETAPA 3/4: Atualizando cache de CEPs..."):
                cep_handler.atualizar_cache_cep(df_validos)
            
            st.success("✅ ETAPA 3/4: Cache de CEPs verificado e/ou atualizado!")

            with st.spinner("ETAPA 4/4: Carregando dados para o Google Sheets..."):
                data_handler.carregar_dados_para_gsheets(df_validos, df_cancelados)
            
            st.success("✅ ETAPA 4/4: Carga para o Google Sheets finalizada!")

            st.balloons()
            st.header("🎉 Processo finalizado com sucesso!")

        else:
            st.error("A extração de dados falhou e não retornou um DataFrame. O processo foi interrompido.")

    except Exception as e:
        st.error(f"Ocorreu um erro inesperado no fluxo principal: {e}")
