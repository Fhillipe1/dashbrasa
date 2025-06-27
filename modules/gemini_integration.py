# modules/gemini_integration.py
import google.generativeai as genai
import streamlit as st
import pandas as pd

class AdvancedOracle:
    def __init__(self):
        self.model = None
        self.chat_session = None
        self._initialize_model()
    
    def _initialize_model(self):
        """Configura o modelo Gemini de forma segura"""
        try:
            genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            st.success("Modelo Gemini inicializado com sucesso!")
        except Exception as e:
            st.error(f"Erro na inicialização: {str(e)}")
            self.model = None

    def start_chat(self, df: pd.DataFrame) -> bool:
        """Inicia o chat com contexto dos dados"""
        if self.model is None:
            st.warning("Modelo não inicializado")
            return False
            
        try:
            context = self._generate_context(df)
            self.chat_session = self.model.start_chat(history=[])
            self.chat_session.send_message(context)
            return True
        except Exception as e:
            st.error(f"Erro ao iniciar chat: {str(e)}")
            return False

    def _generate_context(self, df: pd.DataFrame) -> str:
        """Gera o contexto inicial baseado nos dados"""
        return f"""
        🍔 CONTEXTO LA BRASA BURGER:
        - Período: {df['Data'].min()} a {df['Data'].max()}
        - Total de Pedidos: {len(df)}
        - Faturamento: R$ {df['Total'].sum():,.2f}
        - Ticket Médio: R$ {df['Total'].mean():,.2f}
        - Principais Canais: {df['Canal de venda'].value_counts().head(3).to_dict()}
        """

    def ask(self, question: str) -> str:
        """Processa perguntas com tratamento robusto de erros"""
        if not self.chat_session:
            return "⚠️ Chat não inicializado. Recarregue a página."
            
        try:
            response = self.chat_session.send_message(
                f"Responda como analista especializado:\n{question}",
                stream=False
            )
            return response.text
        except Exception as e:
            return f"🔴 Erro ao processar: {str(e)}"
