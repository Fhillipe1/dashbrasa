# pages/4_🔮_Oráculo.py
import streamlit as st
import pandas as pd
from modules import oraculo_handler, visualization, data_handler

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(layout="wide", page_title="Oráculo La Brasa")
visualization.aplicar_css_local("style/oraculo_style.css")

st.title("🔮 Oráculo La Brasa")
st.markdown("Converse com nosso analista de dados virtual. Ele tem acesso a **toda a sua base de dados** para responder perguntas, fazer comparações e gerar insights.")
st.markdown("---")

# --- LÓGICA DO CHAT ---
def enviar_prompt(prompt):
    """Função para lidar com o envio de um prompt."""
    st.session_state.oraculo_messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="🔮"):
        with st.spinner("O Oráculo está consultando os dados e formulando uma resposta..."):
            # Gera o contexto com base nos dados completos
            contexto_dados = oraculo_handler.gerar_contexto_dados(
                st.session_state.df_validos,
                st.session_state.df_cancelados
            )
            
            # Prepara o histórico para a API
            historico_relevante = st.session_state.oraculo_messages.copy()

            resposta = oraculo_handler.obter_resposta_ia(
                st.session_state.modelo_ia, 
                prompt, 
                historico_relevante, 
                contexto_dados
            )
            st.markdown(resposta)
    
    st.session_state.oraculo_messages.append({"role": "assistant", "content": resposta})

# --- INICIALIZAÇÃO E EXIBIÇÃO DO CHAT ---
# Carrega o modelo de IA e os dados na primeira execução e guarda na sessão
if 'modelo_ia' not in st.session_state:
    st.session_state.modelo_ia = oraculo_handler.configurar_ia()
if 'df_validos' not in st.session_state or 'df_cancelados' not in st.session_state:
    with st.spinner("Carregando base de dados para o Oráculo..."):
        st.session_state.df_validos, st.session_state.df_cancelados = data_handler.ler_dados_do_gsheets()

if "oraculo_messages" not in st.session_state:
    st.session_state.oraculo_messages = []

# Exibe as mensagens do histórico
for message in st.session_state.oraculo_messages:
    avatar = "🔮" if message["role"] == "assistant" else "👤"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# Se o histórico estiver vazio, exibe a mensagem de boas-vindas e sugestões
if not st.session_state.oraculo_messages:
    with st.chat_message("assistant", avatar="🔮"):
        st.markdown("Olá! Eu sou o Oráculo. Minha base de conhecimento com todos os seus dados de vendas e cancelamentos foi carregada. Sobre o que você gostaria de saber?")
        
    st.markdown("##### Sugestões de Perguntas:")
    col1, col2, col3 = st.columns(3)
    if col1.button("Qual canal de venda gera mais faturamento?", key="sugestao1"):
        enviar_prompt("Qual canal de venda gera mais faturamento?")
    if col2.button("Qual o ticket médio do iFood em comparação com o do Site Delivery?", key="sugestao2"):
        enviar_prompt("Qual o ticket médio do iFood em comparação com o do Site Delivery?")
    if col3.button("Qual o principal motivo de cancelamento?", key="sugestao3"):
        enviar_prompt("Qual o principal motivo de cancelamento?")

# Pega o input do usuário na caixa de texto
if prompt := st.chat_input("Qual a sua pergunta sobre os dados?"):
    enviar_prompt(prompt)
