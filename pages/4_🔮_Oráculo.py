# pages/4_🔮_Oráculo.py
import streamlit as st
from modules.data_handler import ler_dados_do_gsheets
from modules.gemini_integration import BusinessOracle

# Configuração
oracle = BusinessOracle()
df, _ = ler_dados_do_gsheets()

# Interface
st.title("🍔 Oráculo La Brasa Burger")
st.caption("Analista virtual - Pergunte sobre vendas, canais e desempenho")

# Chat principal
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Olá! Sou o analista da La Brasa Burger. "
                                      "Posso ajudar com:" 
                                      "\n\n• Comparativos entre canais (iFood/Balcon/Brendi)"
                                      "\n• Análise por dia/horário"
                                      "\n• Sugestões para aumentar vendas"}
    ]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# Input do usuário
if prompt := st.chat_input("Ex: 'Como comparam as vendas no iFood vs Brendi?'"):
    modo_tecnico = "[DEBUG]" in prompt.upper()
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.spinner("Processando..."):
        resposta = oracle.responder(df, prompt, modo_tecnico)
        st.session_state.messages.append({"role": "assistant", "content": resposta})
    
    st.rerun()
