import streamlit as st
from modules.data_handler import ler_dados_do_gsheets
from modules.gemini_integration import BusinessOracle

# Configuração inicial
st.set_page_config(layout="wide", page_title="Oráculo La Brasa Burger")

@st.cache_resource
def inicializar_oraculo():
    oracle = BusinessOracle()
    df, _ = ler_dados_do_gsheets()
    return oracle, df

oracle, df = inicializar_oraculo()

# Interface
st.title("🍔 Oráculo La Brasa Burger - Análise Inteligente")
st.caption("Sistema especializado em análise de dados de hamburgueria")

# Chat principal
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Olá! Sou o analista virtual da La Brasa Burger. "
                                      "Posso ajudar com:\n\n"
                                      "- Comparativos entre canais (iFood/Brendi/Balcão)\n"
                                      "- Análise por período e horário\n"
                                      "- Sugestões baseadas em dados"}
    ]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# Input do usuário
if prompt := st.chat_input("Ex: 'Qual canal tem maior ticket médio?'"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    
    with st.spinner("Analisando dados..."):
        resposta = oracle.responder(df, prompt)
        st.session_state.messages.append({"role": "assistant", "content": resposta})
    
    st.rerun()

# Seção de status (opcional)
with st.expander("ℹ️ Status do Sistema", expanded=False):
    if oracle.model:
        st.success("Sistema operacional")
    else:
        st.error("Sistema parcialmente indisponível - recursos limitados")
