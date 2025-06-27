# test_api.py
from openai import OpenAI

client = OpenAI(
    api_key="sk-38267f4fd078404ab88439a3d092e44a",  # Teste com a chave diretamente primeiro
    base_url="https://api.deepseek.com"
)

try:
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": "Teste de conexão"}]
    )
    print("✅ Conexão bem-sucedida!")
    print("Resposta:", response.choices[0].message.content)
except Exception as e:
    print("❌ Erro na conexão:", str(e))
