# modules/gemini_integration.py
import google.generativeai as genai
import streamlit as st
from typing import Dict, Any

class GeminiOracle:
    @staticmethod
    def ask(question: str, context: str) -> str:
        try:
            # Configuração robusta
            genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
            
            # Modelo atualizado (usar 'gemini-1.5-flash' ou 'gemini-1.0-pro')
            model = genai.GenerativeModel('gemini-1.5-flash')  # Modelo mais rápido e gratuito
            
            prompt = f"""Você é um analista especialista em hamburguerias. 
            Contexto: {context}
            
            Responda de forma direta e analítica, usando:
            - Emojis relevantes 🍔📈
            - Formato monetário (R$ 1.234,56)
            - Destaques em negrito
            
            Pergunta: {question}"""
            
            # Configuração otimizada
            response = model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.3,
                    "max_output_tokens": 1000
                }
            )
            
            return response.text
            
        except Exception as e:
            st.error(f"Erro Gemini: {str(e)}")
            return "⚠️ Sistema temporariamente indisponível. Tente novamente mais tarde."
