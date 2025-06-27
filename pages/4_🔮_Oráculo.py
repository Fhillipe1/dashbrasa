# pages/4_🔮_Oráculo.py
import streamlit as st
from modules.data_handler import ler_dados_do_gsheets
from modules.gemini_integration import SmartOracle

# Configuração inicial
df_validos, df_cancelados = ler_dados_do_gsheets()
oracle = SmartOracle()

# Interface
st.title("🧠 Oráculo Inteligente 3.0")
st.caption("Analista de dados com compreensão profunda dos seus relatórios")

# Chat
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "🍔 Olá! Sou o Oráculo da La Brasa Burger. "
                                      "Pergunte-me sobre vendas por dia da semana, "
                                      "comparativos entre canais ou sugestões para aumentar o faturamento!"}
    ]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# Input do usuário
if prompt := st.chat_input("Ex: 'Qual dia tem maior faturamento semanal?'"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    
    with st.spinner("Analisando dados profundamente..."):
        response = oracle.ask_question(df_validos, prompt)
    
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.rerun()

# Seção de análise automática
with st.expander("📊 Análise Automática dos Dados"):
    st.write("Dados brutos para referência:")
    st.dataframe(df_validos[['Data', 'Dia da Semana', 'Total', 'Canal de venda']].head(3))
