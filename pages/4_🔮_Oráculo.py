# pages/3_🔮_Oráculo.py
import streamlit as st
from modules import oraculo_handler, visualization

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(layout="wide", page_title="Oráculo La Brasa")
visualization.aplicar_css_local("style/oraculo_style.css")

st.title("🔮 Oráculo La Brasa")
st.markdown("Converse com nosso analista de dados virtual. As respostas são baseadas nos filtros aplicados no Dashboard Principal.")
st.markdown("---")

# --- LÓGICA DO CHAT ---
def enviar_prompt(prompt):
    """Função para lidar com o envio de um prompt, seja por input ou por botão."""
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="🔮"):
        with st.spinner("O Oráculo está consultando os dados..."):
            # Pega os dados da sessão e gera o contexto
            contexto_dados = oraculo_handler.gerar_contexto_dados(
                st.session_state.get('df_filtrado_global', pd.DataFrame()),
                st.session_state.get('df_cancelados_filtrado_global', pd.DataFrame())
            )
            
            historico_formatado = [
                {'role': 'user' if m['role'] == 'user' else 'model', 'parts': [m['content']]}
                for m in st.session_state.messages
            ]
            resposta = oraculo_handler.obter_resposta_ia(modelo_ia, prompt, historico_formatado, contexto_dados)
            st.markdown(resposta)
    
    st.session_state.messages.append({"role": "assistant", "content": resposta})

# --- INICIALIZAÇÃO E EXIBIÇÃO DO CHAT ---
modelo_ia = oraculo_handler.configurar_ia()

if "messages" not in st.session_state:
    st.session_state.messages = []

# Verifica se os dados já foram filtrados na página principal
if 'df_filtrado_global' not in st.session_state:
    st.warning("Por favor, visite o 'Dashboard Principal' e aplique os filtros de data para que eu possa analisar os dados.", icon="⚠️")
    st.stop()

# Exibe as mensagens do histórico
for message in st.session_state.messages:
    avatar = "🔮" if message["role"] == "assistant" else "👤"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

if not st.session_state.messages:
    with st.chat_message("assistant", avatar="🔮"):
        st.markdown("Olá! Eu sou o Oráculo. Os filtros do Dashboard Principal foram aplicados. Sobre o que você gostaria de saber?")
        
    st.markdown("##### Sugestões de Perguntas:")
    col1, col2, col3 = st.columns(3)
    if col1.button("Faça um resumo da performance de vendas."):
        enviar_prompt("Faça um resumo da performance de vendas.")
    if col2.button("Qual o ticket médio do período?"):
        enviar_prompt("Qual o ticket médio do período?")
    if col3.button("Houve muitos cancelamentos?"):
        enviar_prompt("Houve muitos cancelamentos?")

if prompt := st.chat_input("Qual a sua pergunta sobre os dados?"):
    enviar_prompt(prompt)
