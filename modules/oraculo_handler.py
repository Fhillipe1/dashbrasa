# modules/oraculo_handler.py
import streamlit as st
import google.generativeai as genai

@st.cache_resource
def configurar_ia():
    """Configura a API do Gemini com a chave dos segredos."""
    try:
        api_key = st.secrets.get("GEMINI_API_KEY")
        if not api_key:
            st.error("Chave da API do Gemini não encontrada. Por favor, configure-a nos segredos do Streamlit.")
            return None
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        return model
    except Exception as e:
        st.error(f"Ocorreu um erro ao configurar a IA: {e}")
        return None

def obter_resposta_ia(modelo, prompt_usuario, historico_chat):
    """Envia o prompt e o histórico para a IA e retorna a resposta."""
    if modelo is None:
        return "Desculpe, não consegui me conectar à inteligência artificial. Verifique as configurações."

    try:
        # Constrói o histórico para a IA, formatando corretamente
        mensagens_para_api = []
        for mensagem in historico_chat:
            role = 'user' if mensagem['role'] == 'user' else 'model'
            mensagens_para_api.append({'role': role, 'parts': [mensagem['content']]})
        
        # Adiciona a nova pergunta do usuário
        mensagens_para_api.append({'role': 'user', 'parts': [prompt_usuario]})

        # Remove a última mensagem para gerar a resposta a partir dela
        conversa = modelo.start_chat(history=mensagens_para_api[:-1])
        response = conversa.send_message(prompt_usuario)
        
        return response.text
    except Exception as e:
        print(f"Erro ao obter resposta da IA: {e}")
        return f"Ocorreu um erro ao processar sua pergunta: {e}"
