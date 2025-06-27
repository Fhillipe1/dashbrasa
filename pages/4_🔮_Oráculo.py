# pages/4_🔮_Oráculo.py
import streamlit as st
from modules.data_handler import ler_dados_do_gsheets
from modules.gemini_integration import AdvancedOracle

# Configuração inicial
if "oracle" not in st.session_state:
    st.session_state.oracle = AdvancedOracle()
    df_validos, _ = ler_dados_do_gsheets()
    
    if not st.session_state.oracle.start_chat(df_validos):
        st.error("Falha crítica ao iniciar o Oráculo")
        st.stop()

    st.session_state.messages = [
        {"role": "assistant", "content": "🍔 Olá! Sou o Oráculo da La Brasa Burger. "
                                      "Pergunte-me sobre vendas, estoque ou otimizações!"}
    ]

# Interface principal
st.title("🤖 Oráculo Inteligente")
st.caption("Analista de Dados com Contexto Completo")

# Mostrar histórico
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# Input do usuário
if prompt := st.chat_input("Ex: 'Quais dias temos menos vendas?'"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    
    with st.spinner("Processando análise..."):
        response = st.session_state.oracle.ask(prompt)
        st.session_state.messages.append({"role": "assistant", "content": response})
    
    st.rerun()

# Botão de recarregar
if st.button("🔄 Recarregar Dados"):
    df_validos, _ = ler_dados_do_gsheets()
    if st.session_state.oracle.start_chat(df_validos):
        st.success("Dados atualizados!")
    else:
        st.error("Erro ao recarregar")
    st.rerun()
