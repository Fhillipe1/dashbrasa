# pages/3_🔮_Oráculo.py
import streamlit as st
from modules import oraculo_handler, visualization

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(layout="wide", page_title="Oráculo La Brasa")
visualization.aplicar_css_local("style/oraculo_style.css")

st.title("🔮 Oráculo La Brasa")
st.markdown("Converse com nosso analista de dados virtual. Faça perguntas e obtenha insights!")
st.markdown("---")

# --- INICIALIZAÇÃO DO CHAT ---

# Configura a IA (usando cache para não reconfigurar a cada interação)
modelo_ia = oraculo_handler.configurar_ia()

# Inicializa o histórico de mensagens na sessão se ainda não existir
if "messages" not in st.session_state:
    st.session_state.messages = []

# Exibe as mensagens do histórico
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- LÓGICA DO CHAT ---

# Pega o input do usuário
if prompt := st.chat_input("Qual a sua pergunta?"):
    # Adiciona a mensagem do usuário ao histórico e exibe na tela
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Gera e exibe a resposta da IA
    with st.chat_message("assistant"):
        with st.spinner("O Oráculo está pensando..."):
            # Passa o prompt e o histórico para a IA
            historico_relevante = st.session_state.messages.copy()
            resposta = oraculo_handler.obter_resposta_ia(modelo_ia, prompt, historico_relevante)
            st.markdown(resposta)
    
    # Adiciona a resposta da IA ao histórico
    st.session_state.messages.append({"role": "assistant", "content": resposta})
