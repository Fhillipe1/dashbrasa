# modules/deepseek_integration.py
from openai import OpenAI
import streamlit as st
from typing import Dict, Any

class DeepSeekAPI:
    @staticmethod
    def ask(question: str, context: str, historical_data: Dict[str, Any] = None) -> str:
        """
        Versão oficial usando o SDK compatível com OpenAI
        """
        try:
            # Configuração do cliente
            client = OpenAI(
                api_key=st.secrets["DEEPSEEK_API_KEY"],
                base_url="https://api.deepseek.com"
            )
            
            # Prepara o contexto do sistema
            system_content = f"""
            Você é o ORÁCULO ANALÍTICO da La Brasa Burger, especialista em:
            - Análise de dados de hamburgueria
            - Identificação de padrões de vendas
            - Sugestões baseadas em dados
            
            CONTEXTO ATUAL:
            {context}
            
            INSTRUÇÕES:
            - Seja direto e analítico
            - Use emojis relevantes
            - Formate números como R$ 1.234,56
            - Destaque insights importantes
            """
            
            # Chamada à API
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": system_content},
                    {"role": "user", "content": question}
                ],
                temperature=0.3,
                stream=False
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"⚠️ Erro ao consultar o oráculo: {str(e)}"
