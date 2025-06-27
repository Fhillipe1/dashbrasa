import streamlit as st
from modules.gemini_integration import BusinessOracle

def main():
    st.title("🍔 Oráculo La Brasa Burger")
    oracle = BusinessOracle()
    
    if prompt := st.chat_input("Faça sua pergunta..."):
        resposta = oracle.responder(None, prompt)  # None apenas para teste
        st.write(resposta)

if __name__ == "__main__":
    main()
