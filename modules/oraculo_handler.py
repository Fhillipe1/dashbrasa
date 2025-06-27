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
            "Seja sempre profissional, direto ao ponto e use emojis de forma sutil. "
            "Nunca invente dados. Se a informação não estiver no contexto, diga que você não tem acesso àquela informação específica."
        )
        
        # OTIMIZAÇÃO 1: Voltando para o modelo Flash, mais rápido e com limites mais generosos
        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash',
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
    Resumo dos Dados de Vendas da La Brasa Burger para análise:
    - Faturamento Total: {viz.formatar_moeda(faturamento_total)}
    - Total de Pedidos: {pedidos_totais}
    - Ticket Médio: {viz.formatar_moeda(ticket_medio)}
    - Principal Canal de Venda: {canal_principal}
    - Pedidos Cancelados: {pedidos_cancelados}
    - Prejuízo com Cancelamentos: {viz.formatar_moeda(valor_cancelado)}
    """
    return contexto

def obter_resposta_ia(modelo, historico_chat):
    """Envia o histórico de chat para a IA e retorna a resposta."""
    if modelo is None:
        return "Desculpe, a IA não está configurada."

    try:
        # Formata o histórico para a API
        historico_formatado = [
            {'role': 'user' if m['role'] == 'user' else 'model', 'parts': [m['content']]}
            for m in historico_chat
        ]
        
        conversa = modelo.start_chat(history=historico_formatado[:-1])
        response = conversa.send_message(historico_formatado[-1]['parts'])
        
        return response.text
    except Exception as e:
        print(f"Erro ao obter resposta da IA: {e}")
        return f"Ocorreu um erro ao comunicar com a API: {str(e)}"
