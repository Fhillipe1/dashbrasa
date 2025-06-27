# modules/gemini_integration.py
import google.generativeai as genai
import streamlit as st
from typing import Dict, Any

class GeminiOracle:
    @staticmethod
    def ask(question: str, context: str, historical_data: Dict[str, Any] = None) -> str:
        try:
            # Configure sua API Key (armazene em secrets.toml)
            genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
            
            model = genai.GenerativeModel('gemini-pro')
            
            prompt = f"""
            Você é o ORÁCULO ANALÍTICO da La Brasa Burger, especialista em:
            - Análise de dados de hamburgueria
            - Identificação de padrões de vendas
            - Sugestões baseadas em dados

            CONTEXTO ATUAL:
            {context}

            INSTRUÇÕES:
            - Seja direto e analítico
            - Use emojis relevantes 🍔📊
            - Formate números como R$ 1.234,56
            - Destaque insights importantes

            PERGUNTA:
            {question}
            """
            
            response = model.generate_content(prompt)
            return response.text
            
        except Exception as e:
            return f"⚠️ Erro: {str(e)}"
