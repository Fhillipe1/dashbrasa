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
            st.error("Chave da API do Gemini não encontrada. Por favor, configure-a nos segredos do Streamlit.")
            return None
        genai.configure(api_key=api_key)
        
        system_instruction = (
            "Você é o Oráculo, um analista de dados especialista na hamburgueria La Brasa Burger de Aracaju. "
            "Sua missão é responder às perguntas de forma clara, amigável e baseada nos dados fornecidos no contexto. "
            "Seja sempre profissional, direto ao ponto e use emojis de forma sutil para tornar a conversa mais agradável. "
            "Nunca invente dados. Se a informação não estiver no contexto fornecido, diga que você não tem acesso àquela informação específica."
        )
        
        model = genai.GenerativeModel(
            model_name='gemini-1.5-pro-latest',
            system_instruction=system_instruction
        )
        return model
    except Exception as e:
        st.error(f"Ocorreu um erro ao configurar a IA: {e}")
        return None

def gerar_contexto_dados(df_filtrado, df_cancelados_filtrado):
    """Gera um resumo em texto dos dataframes para usar como contexto para a IA."""
    if df_filtrado.empty:
        return "Não há dados de vendas para o período selecionado."

    faturamento_total = df_filtrado['Total'].sum()
    pedidos_totais = len(df_filtrado)
    ticket_medio = faturamento_total / pedidos_totais if pedidos_totais > 0 else 0
    canal_summary = df_filtrado.groupby('Canal de venda')['Total'].sum().sort_values(ascending=False)
    canal_principal = canal_summary.index[0] if not canal_summary.empty else "N/A"
    pedidos_cancelados = len(df_cancelados_filtrado)
    valor_cancelado = df_cancelados_filtrado['Total'].sum()
    
    contexto = f"""
    Resumo dos Dados de Vendas da La Brasa Burger:
    - Faturamento Total no Período: {viz.formatar_moeda(faturamento_total)}
    - Número Total de Pedidos: {pedidos_totais}
    - Ticket Médio: {viz.formatar_moeda(ticket_medio)}
    - Principal Canal de Venda em Faturamento: {canal_principal}
    - Total de Pedidos Cancelados no Período: {pedidos_cancelados}
    - Valor Perdido com Cancelamentos: {viz.formatar_moeda(valor_cancelado)}
    """
    return contexto

# --- FUNÇÃO CORRIGIDA ---
def obter_resposta_ia(modelo, prompt_usuario, historico_chat, contexto_dados):
    """Envia o prompt, o contexto e o histórico para a IA e retorna a resposta."""
    if modelo is None:
        return "Desculpe, a IA não está configurada."

    try:
        # Formata o histórico para a API, mas SEM a última pergunta do usuário
        historico_para_api = [
            {'role': 'user' if m['role'] == 'user' else 'model', 'parts': [m['content']]}
            for m in historico_chat[:-1] # Pega todos, exceto o último item
        ]
        
        # Constrói o prompt final com o contexto e a pergunta ATUAL do usuário
        prompt_com_contexto = f"""
        Contexto de dados para sua análise:
        ---
        {contexto_dados}
        ---
        
        Com base no contexto acima, responda a seguinte pergunta do usuário:
        Pergunta: "{prompt_usuario}"
        """

        # Inicia o chat com o histórico anterior
        conversa = modelo.start_chat(history=historico_para_api)
        # Envia a nova mensagem com contexto
        response = conversa.send_message(prompt_com_contexto)
        
        return response.text
    except Exception as e:
        print(f"Erro ao obter resposta da IA: {e}")
        # Retorna o erro de forma mais clara para o usuário
        return f"Ocorreu um erro ao comunicar com a API: {str(e)}"
