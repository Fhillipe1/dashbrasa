# modules/gemini_integration.py
import google.generativeai as genai
import streamlit as st
from typing import Dict, Any
import pandas as pd

class AdvancedOracle:
    def __init__(self):
        self._configure_model()
        self.chat_session = None
        self.df_context = None
    
    def _configure_model(self):
        try:
            genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
            self.model = genai.GenerativeModel(
                'gemini-1.5-flash',
                system_instruction="Você é o ORÁCULO DA LA BRASA BURGER. Siga estas regras:\n"
                                "1. Analise relatórios com profundidade\n"
                                "2. Sugira ações baseadas em dados\n"
                                "3. Formate respostas com:\n"
                                "   - 📊 Análise objetiva\n"
                                "   - 💡 Sugestões práticas\n"
                                "   - 🚨 Alertas quando relevante")
        except Exception as e:
            st.error(f"Erro na configuração: {str(e)}")

    def load_data(self, df: pd.DataFrame):
        """Carrega dados e inicia o chat automaticamente"""
        self.df_context = df
        context = self._generate_context()
        
        try:
            self.chat_session = self.model.start_chat(history=[])
            self.chat_session.send_message(context)
            return True
        except Exception as e:
            st.error(f"Erro ao iniciar chat: {str(e)}")
            return False

    def _generate_context(self) -> str:
        """Gera contexto analítico dos dados"""
        if self.df_context is None:
            return "Dados não carregados"
            
        return f"""
        🍔 DADOS LA BRASA BURGER (Última atualização):
        - Período: {self.df_context['Data'].min()} a {self.df_context['Data'].max()}
        - Faturamento Total: R$ {self.df_context['Total'].sum():,.2f}
        - Ticket Médio: R$ {self.df_context['Total'].mean():,.2f}
        - Top Canais: {self.df_context['Canal de venda'].value_counts().head(3).to_dict()}
        - Horário Pico: {self.df_context['Hora'].mode()[0]}h
        """

    def ask(self, question: str) -> str:
        """Processa perguntas com tratamento robusto de erros"""
        if not self.chat_session:
            return "🔁 Recarregando contexto... Tente novamente em 5 segundos."
        
        try:
            response = self.chat_session.send_message(
                f"PERGUNTA DO USUÁRIO: {question}\n"
                "INSTRUÇÕES:\n"
                "1. Considere o histórico completo\n"
                "2. Cruze dados quando possível\n"
                "3. Responda em português brasileiro",
                stream=False
            )
            return response.text
            
        except Exception as e:
            return f"⚠️ Erro temporário. Detalhes: {str(e)}"
