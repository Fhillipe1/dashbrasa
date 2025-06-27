# pages/4_Oráculo.py
import streamlit as st
import pandas as pd
from modules.data_handler import ler_dados_do_gsheets, tratar_dados_saipos
from modules.deepseek_integration import DeepSeekAPI
from modules.visualization import formatar_moeda

def show_oraculo():
    st.title("🔮 Oráculo La Brasa Burger")
    st.markdown("""
    **Analista de dados inteligente**. Faça perguntas sobre:
    - Faturamento por dia/hora 🕒
    - Cancelamentos ❌
    - Performance por bairro 🏘️
    - Como melhorar resultados 💡
    """)
    
    # --- Carrega os dados ---
    df_validos, df_cancelados = ler_dados_do_gsheets()
    if df_validos.empty:
        st.error("Dados não carregados. Verifique a conexão com o Google Sheets.")
        return
    
    # --- Contexto para o Oráculo (resumo estatístico) ---
    context = f"""
    DADOS DA LA BRASA BURGER (últimos {len(df_validos)} pedidos):
    - Período: {df_validos['Data'].min()} a {df_validos['Data'].max()}
    - Faturamento total: {formatar_moeda(df_validos['Total'].sum())}
    - Ticket médio: {formatar_moeda(df_validos['Total'].mean())}
    - Top 3 bairros: {df_validos['Bairro'].value_counts().head(3).index.tolist()}
    - Taxa de cancelamento: {(len(df_cancelados) / (len(df_validos) + len(df_cancelados)) * 100):.2f}%
    """
    
    # --- Chat com o Oráculo ---
    st.subheader("💬 Pergunte ao Oráculo")
    user_question = st.text_input("Ex: 'Qual dia da semana tem mais cancelamentos?'")
    
    if user_question:
        resposta = DeepSeekAPI.ask(
            question=user_question,
            context=context,
            historical_data=df_validos.to_dict()  # Envia dados brutos se necessário
        )
        st.markdown(f"**Resposta:** {resposta}")
    
    # --- Insights Automáticos ---
    st.subheader("📊 Insights do Dia")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**📅 Melhor dia da semana**")
        dia_top = df_validos.groupby('Dia da Semana')['Total'].sum().idxmax()
        st.write(f"- {dia_top.split('. ')[1]} (Faturamento: {formatar_moeda(df_validos[df_validos['Dia da Semana'] == dia_top]['Total'].sum())})")
        
    with col2:
        st.markdown("**⏰ Horário de pico**")
        hora_pico = df_validos['Hora'].mode()[0]
        st.write(f"- {hora_pico}h às {hora_pico+1}h (Média de pedidos: {len(df_validos[df_validos['Hora'] == hora_pico])})")
    
    # --- Análise de Cancelamentos ---
    if not df_cancelados.empty:
        st.markdown("**❌ Principais motivos de cancelamento**")
        motivo_top = df_cancelados['Motivo de cancelamento'].value_counts().idxmax()
        st.write(f"- '{motivo_top}' ({df_cancelados['Motivo de cancelamento'].value_counts().max()} ocorrências)")

# Chamada da página
show_oraculo()
