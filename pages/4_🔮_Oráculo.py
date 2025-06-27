import streamlit as st
from modules.data_handler import ler_dados_do_gsheets
from modules.deepseek_integration import DeepSeekAPI

def show_oraculo():
    # Carrega os dados
    df_validos, df_cancelados = ler_dados_do_gsheets()
    
    # Verificação dos dados
    if df_validos.empty:
        st.error("Nenhum dado válido encontrado")
        return
    
    # --- Contexto detalhado para o Oráculo ---
    context = f"""
    DADOS DA LA BRASA BURGER - ÚLTIMOS {len(df_validos)} PEDIDOS:
    
    📅 Período: {df_validos['Data'].min()} a {df_validos['Data'].max()}
    💰 Faturamento Total: R$ {df_validos['Total'].sum():,.2f}
    🧾 Ticket Médio: R$ {df_validos['Total'].mean():,.2f}
    
    CANAIS DE VENDA:
    {df_validos['Canal de venda'].value_counts().to_string()}
    
    HORÁRIOS DE PICO:
    {df_validos['Hora'].value_counts().head(3).to_string()}
    
    TOP 3 BAIRROS:
    {df_validos['Bairro'].value_counts().head(3).to_string()}
    """
    
    # --- Chat Interativo ---
    st.subheader("💬 Pergunte ao Oráculo")
    user_question = st.text_input("Ex: 'Qual canal de venda tem maior ticket médio?'")
    
    if user_question:
        resposta = DeepSeekAPI.ask(
            question=user_question,
            context=context,
            historical_data=df_validos.to_dict()
        )
        st.markdown(f"**🔮 Resposta:** {resposta}")
    
    # --- Insights Automáticos ---
    st.subheader("📊 Principais Métricas")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Faturamento Total", f"R$ {df_validos['Total'].sum():,.2f}")
    
    with col2:
        st.metric("Ticket Médio", f"R$ {df_validos['Total'].mean():,.2f}")
    
    with col3:
        st.metric("Pedidos/Dia", len(df_validos) / df_validos['Data'].nunique())
    
    # --- Análise por Canal ---
    st.subheader("📶 Performance por Canal")
    canais = df_validos.groupby('Canal de venda').agg({
        'Total': ['sum', 'mean', 'count'],
        'Hora': lambda x: x.mode()[0]
    })
    st.dataframe(canais.style.format({
        ('Total', 'sum'): 'R$ {:.2f}',
        ('Total', 'mean'): 'R$ {:.2f}'
    }))
    
    # --- Análise de Cancelamentos ---
    if not df_cancelados.empty:
        st.subheader("❌ Análise de Cancelamentos")
        if 'Motivo do desconto' in df_cancelados.columns:
            st.write("Motivos mais comuns:")
            st.write(df_cancelados['Motivo do desconto'].value_counts().head(5))

try:
    show_oraculo()
except Exception as e:
    st.error(f"Erro: {str(e)}")
