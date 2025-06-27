# modules/gemini_integration.py
import google.generativeai as genai
import streamlit as st
from typing import Dict, Any
import pandas as pd

class AdvancedOracle:
    def __init__(self):
        self._configure_model()
        self.chat_session = None
    
    def _configure_model(self):
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        self.model = genai.GenerativeModel(
            'gemini-1.5-flash',
            system_instruction="Você é o ORÁCULO DA LA BRASA BURGER, um analista especializado em:" 
                              "1. Interpretação de relatórios de vendas\n"
                              "2. Identificação de padrões ocultos\n"
                              "3. Sugestões baseadas em dados\n\n"
                              "FORMATO DE RESPOSTA:\n"
                              "- Análise objetiva\n"
                              "- Dados numéricos com contexto\n"
                              "- Emojis relevantes\n"
                              "- Sugestões acionáveis")
    
    def start_chat(self, df_context: pd.DataFrame):
        """Prepara o contexto inicial do chat"""
        context = f"""
        📊 RELATÓRIO ATUALIZADO (Últimos {len(df_context)} pedidos):
        - Período: {df_context['Data'].min()} a {df_context['Data'].max()}
        - Faturamento Total: R$ {df_context['Total'].sum():,.2f}
        - Ticket Médio: R$ {df_context['Total'].mean():,.2f}
        - Top 3 Canais: {df_context['Canal de venda'].value_counts().head(3).to_dict()}
        - Horário Pico: {df_context['Hora'].mode()[0]}h
        """
        self.chat_session = self.model.start_chat(history=[])
        self.chat_session.send_message(context)
        return context
    
    def ask(self, question: str) -> str:
        """Processa perguntas com memória contextual"""
        if not self.chat_session:
            return "⚠️ Inicie o chat primeiro com start_chat()"
        
        try:
            response = self.chat_session.send_message(
                f"PERGUNTA: {question}\n"
                "INSTRUÇÕES:\n"
                "1. Seja extremamente analítico\n"
                "2. Cruze dados quando possível\n"
                "3. Sugira ações específicas",
                stream=True
            )
            return "".join(chunk.text for chunk in response)
        except Exception as e:
            return f"⚠️ Erro: {str(e)}"
