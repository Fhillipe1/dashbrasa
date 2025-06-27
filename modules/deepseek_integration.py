# modules/deepseek_integration.py
import requests
import json
import streamlit as st
from typing import Dict, Any

class DeepSeekAPI:
    BASE_URL = "https://api.deepseek.com/v1"  # Verifique se esta é a URL correta
    
    @staticmethod
    def ask(question: str, context: str, historical_data: Dict[str, Any] = None) -> str:
        """
        Versão melhorada com tratamento de erros robusto
        """
        try:
            headers = {
                "Authorization": f"Bearer {st.secrets['DEEPSEEK_API_KEY']}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "deepseek-chat",
                "messages": [
                    {
                        "role": "system",
                        "content": f"""
                        Você é o ORÁCULO DA LA BRASA BURGER, um analista especialista em:
                        - Análise de vendas de hamburgueria
                        - Identificação de padrões de consumo
                        - Sugestões para aumentar faturamento
                        
                        Dados atuais:
                        {context}
                        """
                    },
                    {"role": "user", "content": question}
                ],
                "temperature": 0.3
            }
            
            response = requests.post(
                f"{DeepSeekAPI.BASE_URL}/chat/completions",
                headers=headers,
                json=payload,  # Mudamos para json= em vez de data=
                timeout=10
            )
            
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
            
        except requests.exceptions.HTTPError as e:
            st.error(f"Erro de autenticação. Verifique sua chave API nos segredos.")
            return "🔒 Erro de acesso à API. Por favor, verifique as configurações."
        except Exception as e:
            return f"⚠️ Erro temporário: {str(e)}"
