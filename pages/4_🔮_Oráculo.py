# pages/4_🔮_Oráculo.py
import streamlit as st
from modules.data_handler import ler_dados_do_gsheets
from modules.gemini_integration import GeminiOracle  # Mudamos a importação

def show_oraculo():
    st.title("🔮 Oráculo La Brasa Burger (Gemini)")
    
    # Carrega dados
    df_validos, df_cancelados = ler_dados_do_gsheets()
    
    # Contexto analítico
    context = f"""
    🍔 DADOS RECENTES:
    - Período: {df_validos['Data'].min()} a {df_validos['Data'].max()}
    - Faturamento: R$ {df_validos['Total'].sum():,.2f}
    - Ticket Médio: R$ {df_validos['Total'].mean():,.2f}
    - Top Canal: {df_validos['Canal de venda'].mode()[0]}
    """
    
    # Chat interativo
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])
    
    if prompt := st.chat_input("Pergunte sobre vendas, cancelamentos..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)
        
        with st.spinner("Analisando..."):
            resposta = GeminiOracle.ask(prompt, context)
        
        st.session_state.messages.append({"role": "assistant", "content": resposta})
        st.chat_message("assistant").write(resposta)

show_oraculo()
