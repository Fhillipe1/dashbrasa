# pages/4_🔮_Oráculo.py
import streamlit as st
from modules.data_handler import ler_dados_do_gsheets
from modules.deepseek_integration import DeepSeekAPI

def show_oraculo():
    st.title("🔮 Oráculo La Brasa Burger")
    st.caption("Analista de dados inteligente - Pergunte sobre vendas, cancelamentos e otimizações")
    
    # Carrega dados
    df_validos, df_cancelados = ler_dados_do_gsheets()
    if df_validos.empty:
        st.error("Dados não carregados")
        return
    
    # Prepara contexto
    context = f"""
    📊 DADOS ATUAIS (Últimos {len(df_validos)} pedidos):
    - Período: {df_validos['Data'].min()} a {df_validos['Data'].max()}
    - Faturamento: R$ {df_validos['Total'].sum():,.2f}
    - Ticket Médio: R$ {df_validos['Total'].mean():,.2f}
    - Top Canais: {df_validos['Canal de venda'].value_counts().head(3).to_dict()}
    - Horário Pico: {df_validos['Hora'].mode()[0]}h
    """
    
    # Inicializa o chat
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Olá! Sou o Oráculo da La Brasa Burger. Pergunte-me sobre:"}
        ]
    
    # Mostra histórico do chat
    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])
    
    # Input do usuário
    if prompt := st.chat_input("Ex: 'Como melhorar as vendas às segundas?'"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)
        
        with st.spinner("Consultando os dados..."):
            resposta = DeepSeekAPI.ask(
                question=prompt,
                context=context,
                historical_data={
                    "validos": df_validos.head(1000).to_dict(),
                    "cancelados": df_cancelados.head(1000).to_dict()
                }
            )
        
        st.session_state.messages.append({"role": "assistant", "content": resposta})
        st.chat_message("assistant").write(resposta)

show_oraculo()
