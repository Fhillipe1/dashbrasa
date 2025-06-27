import streamlit as st
from modules.data_handler import ler_dados_do_gsheets
from modules.gemini_integration import AdvancedOracle

# Configuração Inicial
oracle = AdvancedOracle()
df_validos, _ = ler_dados_do_gsheets()

# Inicialização Automática
if "oracle" not in st.session_state:
    st.session_state.oracle = AdvancedOracle()
    success = st.session_state.oracle.load_data(df_validos)
    
    if not success:
        st.error("Falha ao inicializar o Oráculo. Verifique sua conexão.")
        st.stop()

# Interface do Chat
st.title("🤖 Oráculo La Brasa Burger 2.0")
st.caption("Analista de Dados com Memória Contextual")

# Histórico de Mensagens
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "🍔 Olá! Sou seu analista virtual. "
                                      "Pergunte sobre vendas, cancelamentos ou otimizações!"}
    ]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# Input do Usuário
if prompt := st.chat_input("Ex: 'Quais produtos venderam menos no último mês?'"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    
    with st.spinner("Analisando dados profundamente..."):
        response = st.session_state.oracle.ask(prompt)
    
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.rerun()

# Botão de Recarregar Dados
if st.button("🔄 Atualizar Dados do Relatório"):
    df_validos, _ = ler_dados_do_gsheets()
    if st.session_state.oracle.load_data(df_validos):
        st.success("Dados atualizados com sucesso!")
    else:
        st.error("Erro ao carregar novos dados")
    st.rerun()
