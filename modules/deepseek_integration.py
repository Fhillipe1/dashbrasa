# modules/deepseek_integration.py
import requests
import json
import streamlit as st
from typing import Dict, Any

class DeepSeekAPI:
    BASE_URL = "https://api.deepseek.com/v1"  # URL da API (verifique a documentação oficial)
    
    @staticmethod
    def ask(question: str, context: str, historical_data: Dict[str, Any] = None) -> str:
        """
        Envia uma pergunta para a API do DeepSeek.
        
        Args:
            question (str): Pergunta do usuário (ex: "Qual dia tem maior faturamento?")
            context (str): Contexto dos dados em formato texto
            historical_data (dict): Dados brutos em formato de dicionário (opcional)
        
        Returns:
            str: Resposta da API ou mensagem de erro
        """
        # Configuração da requisição
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
                    Você é um analista de dados especializado em restaurantes.
                    Use o contexto abaixo para responder de forma precisa:
                    {context}
                    """
                },
                {
                    "role": "user",
                    "content": question
                }
            ],
            "temperature": 0.3
        }
        
        try:
            # Chamada à API - CORREÇÃO AQUI: parênteses corretamente fechados
            response = requests.post(
                f"{DeepSeekAPI.BASE_URL}/chat/completions",
                headers=headers,
                data=json.dumps(payload)
            )  # Este parêntese estava faltando
            
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
            
        except requests.exceptions.RequestException as e:
            return f"Erro na API: {str(e)}"
        except KeyError:
            return "Erro ao processar a resposta da API."
