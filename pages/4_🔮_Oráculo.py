# pages/4_🔮_Oráculo.py
import streamlit as st
from modules.data_handler import ler_dados_do_gsheets
from modules.gemini_integration import SmartOracle

# Configuração
st.set_page_config(layout="wide")

@st.cache_resource
def load_oracle():
    oracle = SmartOracle()
    df, _ = ler_dados_do_gsheets()
    return oracle, df

oracle, df_validos = load_oracle()

# Interface
st.title("🍔 Oráculo La Brasa Burger - Análise Profissional")
col1, col2 = st.columns([3, 1])

with col1:
    # Chat principal
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Olá! Analiso seus dados de vendas. "
                                          "Exemplos de perguntas:\n\n"
                                          "1. Qual dia tem maior faturamento?\n"
                                          "2. Compare ifood vs balcão\n"
                                          "3. Sugestões para aumentar vendas"}
        ]

    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    if prompt := st.chat_input("Sua pergunta..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.spinner("Analisando dados complexos..."):
            response = oracle.ask_question(df_validos, prompt)
            st.session_state.messages.append({"role": "assistant", "content": response})
        
        st.rerun()

with col2:
    # Painel de dados rápidos
    st.metric("Total Pedidos", len(df_validos))
    st.metric("Faturamento", f"R$ {df_validos['Total'].sum():,.2f}")
    
    if st.button("🔄 Atualizar Dados"):
        df_validos, _ = ler_dados_do_gsheets()
        st.success("Dados atualizados!")
