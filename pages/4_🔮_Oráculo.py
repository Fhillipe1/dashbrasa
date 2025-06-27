# pages/3_🔮_Oráculo.py
import streamlit as st
import pandas as pd
from modules import oraculo_handler, visualization

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(layout="wide", page_title="Oráculo La Brasa")
visualization.aplicar_css_local("style/oraculo_style.css")

st.title("🔮 Oráculo La Brasa")
st.markdown("Converse com nosso analista de dados virtual. As respostas são baseadas nos filtros aplicados no Dashboard Principal.")
st.markdown("---")

# --- LÓGICA DO CHAT ---

# Inicializa o modelo de IA e o histórico do chat na sessão
if 'modelo_ia' not in st.session_state:
    st.session_state.modelo_ia = oraculo_handler.configurar_ia()
if "oraculo_messages" not in st.session_state:
    st.session_state.oraculo_messages = []

# Verifica se os dados já foram filtrados na página principal
if 'df_filtrado_global' not in st.session_state:
    st.warning("Por favor, visite o 'Dashboard Principal' e aplique os filtros de data para que eu possa analisar os dados.", icon="⚠️")
    st.stop()

# Botão para iniciar a análise e carregar o contexto
if not st.session_state.oraculo_messages:
    if st.button("Analisar Dados com o Oráculo", type="primary", use_container_width=True):
        with st.spinner("O Oráculo está estudando os dados..."):
            df_filtrado = st.session_state.get('df_filtrado_global', pd.DataFrame())
            df_cancelados = st.session_state.get('df_cancelados_filtrado_global', pd.DataFrame())
            
            contexto_dados = oraculo_handler.gerar_contexto_dados(df_filtrado, df_cancelados)
            
            prompt_inicial = f"""
            Contexto para análise:
            {contexto_dados}
            ---
            Pronto! Já analisei os dados do período selecionado. O que você gostaria de saber?
            """
            st.session_state.oraculo_messages.append({"role": "assistant", "content": prompt_inicial})
            st.rerun()

# Exibe as mensagens do histórico, se houver
for message in st.session_state.oraculo_messages:
    avatar = "🔮" if message["role"] == "assistant" else "👤"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# Só exibe a caixa de input DEPOIS que a análise foi iniciada
if st.session_state.oraculo_messages:
    if prompt := st.chat_input("Qual a sua pergunta sobre os dados?"):
        # Adiciona a mensagem do usuário
        st.session_state.oraculo_messages.append({"role": "user", "content": prompt})
        
        # Gera e adiciona a resposta da IA
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)

        with st.chat_message("assistant", avatar="🔮"):
            with st.spinner("Processando..."):
                resposta = oraculo_handler.obter_resposta_ia(
                    st.session_state.modelo_ia, 
                    st.session_state.oraculo_messages
                )
                st.markdown(resposta)
        
        st.session_state.oraculo_messages.append({"role": "assistant", "content": resposta})
