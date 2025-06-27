import streamlit as st
from modules.data_handler import ler_dados_do_gsheets
from modules.gemini_integration import OracleLaBrasa

# Configuração
st.set_page_config(page_title="Oráculo La Brasa", layout="wide")

@st.cache_resource
def carregar_sistema():
    sistema = OracleLaBrasa()
    dados, _ = ler_dados_do_gsheets()
    return sistema, dados

oraculo, df = carregar_sistema()

# Interface
st.title("🍔 Oráculo La Brasa Burger")
st.caption("Sistema Inteligente de Análise Comercial")

# Histórico de conversa
if "mensagens" not in st.session_state:
    st.session_state.mensagens = [
        {"role": "assistant", "content": "Olá! Sou seu analista virtual. Posso ajudar com:"},
        {"role": "assistant", "content": "- Comparativo entre iFood e nosso site\n- Análise por dia/horário\n- Sugestões para aumentar vendas"}
    ]

for msg in st.session_state.mensagens:
    st.chat_message(msg["role"]).write(msg["content"])

# Input do usuário
if prompt := st.chat_input("Ex: 'Como comparam iFood e Brendi?'"):
    st.session_state.mensagens.append({"role": "user", "content": prompt})
    
    with st.spinner("Processando..."):
        resposta = oraculo.responder(df, prompt)
        st.session_state.mensagens.append({"role": "assistant", "content": resposta})
    
    st.rerun()

# Status (opcional)
with st.expander("🔍 Status do Sistema", expanded=False):
    if oraculo.model:
        st.success("✅ Análise avançada disponível")
    else:
        st.warning("⚠️ Modo básico (sem IA)")
