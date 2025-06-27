# modules/deepseek_integration.py
import requests
import json
from typing import Dict, Any

class DeepSeekAPI:
    BASE_URL = "https://api.deepseek.com/v1"  # Exemplo (verifique a URL real na documentação)
    
    @staticmethod
    def ask(question: str, context: str, historical_data: Dict[str, Any] = None) -> str:
        """
        Envia uma pergunta para a API do DeepSeek com contexto dos dados.
        
        Args:
            question: Pergunta do usuário (ex: "Qual dia tem maior faturamento?")
            context: Texto resumindo os dados (ex: "Faturamento total: R$ X...")
            historical_data: Dados brutos em formato dicionário (opcional para análises complexas).
        
        Returns:
            Resposta do oráculo (str).
        """
        headers = {
            "Authorization": f"Bearer {st.secrets['DEEPSEEK_API_KEY']}",  # Adicione sua chave nos segredos do Streamlit
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "deepseek-chat",  # Verifique o modelo correto na documentação
            "messages": [
                {
                    "role": "system",
                    "content": f"""
                    Você é um analista de dados especialista em restaurantes. 
                    Use os dados abaixo para responder de forma precisa e direta.
                    Dados: {context}
                    """
                },
                {
                    "role": "user",
                    "content": question
                }
            ],
            "temperature": 0.3  # Controla a criatividade (baixo = mais factual)
        }
        
        try:
            response = requests.post(
                f"{DeepSeekAPI.BASE_URL}/chat/completions",
                headers=headers,
                data=json.dumps(payload)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            return f"Erro ao acessar o oráculo: {str(e)}"
