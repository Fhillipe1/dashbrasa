import streamlit as st
from modules.data_handler import ler_dados_do_gsheets
from modules.deepseek_integration import DeepSeekAPI

def show_oraculo():
    # Carrega os dados primeiro
    df_validos, df_cancelados = ler_dados_do_gsheets()
    
    # Verificação segura dos dados
    if df_validos.empty:
        st.error("Dados válidos não encontrados. Verifique a conexão com a planilha.")
        return
    
    # Debug: mostrar colunas disponíveis (opcional)
    st.write("🔍 Colunas disponíveis nos dados válidos:", df_validos.columns.tolist())
    
    if not df_cancelados.empty:
        st.write("🔍 Colunas disponíveis nos cancelados:", df_cancelados.columns.tolist())
    
    # --- Contexto para o Oráculo ---
    context = f"""
    DADOS DA LA BRASA BURGER (últimos {len(df_validos)} pedidos):
    - Período: {df_validos['Data'].min()} a {df_validos['Data'].max()}
    - Faturamento total: {df_validos['Total'].sum():.2f}
    - Ticket médio: {df_validos['Total'].mean():.2f}
    """
    
    # --- Chat com o Oráculo ---
    st.subheader("💬 Pergunte ao Oráculo")
    user_question = st.text_input("Ex: 'Qual dia tem maior faturamento?'")
    
    if user_question:
        resposta = DeepSeekAPI.ask(
            question=user_question,
            context=context,
            historical_data=df_validos.to_dict()
        )
        st.markdown(f"**Resposta:** {resposta}")
    
    # --- Insights Automáticos ---
    st.subheader("📊 Insights do Dia")
    
    # Verificação segura de colunas antes de acessá-las
    if 'Dia da Semana' in df_validos.columns:
        dia_top = df_validos.groupby('Dia da Semana')['Total'].sum().idxmax()
        st.write(f"📅 **Melhor dia**: {dia_top}")
    
    if 'Hora' in df_validos.columns:
        hora_pico = df_validos['Hora'].mode()[0]
        st.write(f"⏰ **Horário de pico**: {hora_pico}h")

# Chamada principal com tratamento de erro
try:
    show_oraculo()
except Exception as e:
    st.error(f"Ocorreu um erro inesperado: {str(e)}")
    st.info("Por favor verifique os logs para mais detalhes.")
