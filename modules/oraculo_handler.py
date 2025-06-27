# modules/oraculo_handler.py
import streamlit as st
import pandas as pd
import google.generativeai as genai
from . import visualization as viz

@st.cache_resource
def configurar_ia():
    """Configura a API do Gemini com a chave dos segredos."""
    try:
        api_key = st.secrets.get("GEMINI_API_KEY")
        if not api_key:
            st.error("Chave da API do Gemini não encontrada.")
            return None
        genai.configure(api_key=api_key)
        
        system_instruction = (
            "Você é o Oráculo, um analista de dados especialista na hamburgueria La Brasa Burger de Aracaju. "
            "Sua missão é responder às perguntas de forma clara, amigável e baseada nos dados fornecidos no contexto. "
            "Use os dados das tabelas markdown fornecidas para fazer comparações, cálculos e gerar insights. "
            "Seja sempre profissional, direto ao ponto e use emojis de forma sutil. "
            "Nunca invente dados. Se a informação não estiver no contexto, diga que você não tem acesso àquela informação específica."
        )
        
        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash',
            system_instruction=system_instruction
        )
        return model
    except Exception as e:
        st.error(f"Ocorreu um erro ao configurar a IA: {e}")
        return None

def gerar_contexto_dados(df_validos, df_cancelados):
    """Gera um resumo detalhado em tabelas markdown para usar como contexto para a IA."""
    if df_validos.empty:
        return "Não há dados de vendas para analisar."

    # Resumo Geral
    faturamento_total = df_validos['Total'].sum()
    pedidos_totais = len(df_validos)
    ticket_medio = faturamento_total / pedidos_totais if pedidos_totais > 0 else 0
    
    resumo_geral_md = f"""
- Faturamento Total (Geral): {viz.formatar_moeda(faturamento_total)}
- Número Total de Pedidos (Geral): {pedidos_totais}
- Ticket Médio (Geral): {viz.formatar_moeda(ticket_medio)}
"""
    # Análise por Canal
    df_canal = df_validos.groupby('Canal de venda').agg(Faturamento=('Total', 'sum'), Pedidos=('Pedido', 'count')).reset_index()
    df_canal['Ticket_Medio'] = df_canal.apply(lambda r: r['Faturamento']/r['Pedidos'] if r['Pedidos']>0 else 0, axis=1)
    df_canal = df_canal.sort_values(by="Faturamento", ascending=False)
    vendas_canal_md = df_canal.to_markdown(index=False)

    # Análise de Cancelamentos
    pedidos_cancelados = len(df_cancelados)
    valor_cancelado = df_cancelados['Total'].sum()
    cancelados_md = f"- Total de Pedidos Cancelados: {pedidos_cancelados}\n- Prejuízo com Cancelamentos: {viz.formatar_moeda(valor_cancelado)}"

    contexto_completo = f"""
Aqui estão os dados de vendas da La Brasa Burger para sua análise:

### Resumo Geral
{resumo_geral_md}

### Vendas por Canal de Venda
{vendas_canal_md}

### Resumo de Cancelamentos
{cancelados_md}
"""
    return contexto_completo

def obter_resposta_ia(modelo, prompt_usuario, historico_chat, contexto_dados):
    """Envia o prompt, o contexto e o histórico para a IA e retorna a resposta."""
    if modelo is None:
        return "Desculpe, a IA não está configurada."

    try:
        historico_para_api = [
            {'role': 'user' if m['role'] == 'user' else 'model', 'parts': [m['content']]}
            for m in historico_chat
        ]
        
        prompt_com_contexto = f"""
        Use os seguintes dados como única fonte de verdade para sua análise:
        ---
        {contexto_dados}
        ---
        
        Com base ESTREITAMENTE no contexto acima, responda a seguinte pergunta do usuário de forma analítica:
        Pergunta: "{prompt_usuario}"
        """

        conversa = modelo.start_chat(history=historico_para_api)
        response = conversa.send_message(prompt_com_contexto)
        
        return response.text
    except Exception as e:
        print(f"Erro ao obter resposta da IA: {e}")
        return f"Ocorreu um erro ao comunicar com a API: {str(e)}"
