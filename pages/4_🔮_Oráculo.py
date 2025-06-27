import streamlit as st
from modules.data_handler import ler_dados_do_gsheets
from modules.gemini_integration import AdvancedOracle

# Configuração inicial
oracle = AdvancedOracle()
df_validos, _ = ler_dados_do_gsheets()

# Inicialização do Chat
if "oracle_initialized" not in st.session_state:
    oracle.start_chat(df_validos)
    st.session_state.oracle_initialized = True
    st.session_state.messages = [
        {"role": "assistant", "content": "🍔 Olá! Sou o Oráculo Analítico da La Brasa Burger. "
                                      "Pergunte-me sobre:\n"
                                      "- Comparativo entre canais de venda\n"
                                      "- Análise por período/horário\n"
                                      "- Sugestões para aumentar faturamento"}
    ]

# Interface do Chat
st.title("🧠 Oráculo Inteligente - La Brasa Burger")
st.caption("Analista de dados com memória contextual")

# Histórico de mensagens
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# Input do usuário
if prompt := st.chat_input("Ex: 'Como melhorar as vendas no Ifood?'"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    
    with st.spinner("Analisando profundamente..."):
        response = oracle.ask(prompt)
    
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.chat_message("assistant").write(response)

# Botão para análise automática
if st.button("🔍 Gerar Insights Automáticos"):
    analysis = oracle.ask("Gere 3 insights importantes baseados nos dados atuais, "
                         "com sugestões acionáveis formatadas em tópicos.")
    st.session_state.messages.append({"role": "assistant", "content": analysis})
    st.rerun()
