import sys
import os
import streamlit as st

# Garante que a raiz do projeto seja reconhecida pelo Python
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Importa a função DEPOIS de ajustar o path
from modules.data_extractor import run_extraction
from dotenv import load_dotenv

# Carrega as variáveis de ambiente
load_dotenv(dotenv_path=os.path.join(project_root, '.env'))

st.title("🔄 Atualizar Relatório de Vendas")
st.markdown("""
Esta página aciona o robô para baixar o relatório de vendas mais recente.
""")

# Lógica de autorização em etapas com st.session_state
if 'authorization_granted' not in st.session_state:
    st.session_state.authorization_granted = False

if not st.session_state.authorization_granted:
    if st.button("🔒 Autorizar Atualização"):
        st.session_state.authorization_granted = True
        st.rerun()

if st.session_state.authorization_granted:
    st.info("Para continuar, por favor, insira a senha de acesso.")
    
    senha_correta = os.getenv("APP_PASSWORD")
    senha_digitada = st.text_input("Senha:", type="password", key="password_input")

    if senha_digitada:
        if senha_digitada == senha_correta:
            st.success("Acesso liberado!", icon="✅")
            
            if st.button("▶️ Iniciar Extração de Dados", type="primary"):
                with st.spinner('Iniciando o robô... O navegador será controlado automaticamente. Por favor, aguarde.'):
                    novo_df = run_extraction()

                if novo_df is not None:
                    st.success("Relatório atualizado com sucesso!")
                    st.balloons()
                    st.dataframe(novo_df)
                else:
                    st.error("Ocorreu um erro durante a extração. Verifique o console do terminal para mais detalhes.")
        else:
            if senha_digitada:
                st.error("Senha incorreta. Tente novamente.", icon="❌")