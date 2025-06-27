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
    
    # Prepara contexto detalhado
    context = f"""
    🍔 DADOS DA LA BRASA BURGER (Últimos {len(df_validos)} pedidos):
    
    📅 Período: {df_validos['Data'].min()} a {df_validos['Data'].max()}
    💰 Faturamento Total: R$ {df_validos['Total'].sum():,.2f}
    🧾 Ticket Médio: R$ {df_validos['Total'].mean():,.2f}
    
    🚀 TOP 3 CANAIS:
    {df_validos['Canal de venda'].value_counts().head(3).to_string()}
    
    ⏰ HORÁRIO PICO: {df_validos['Hora'].mode()[0]}h
    🏙️ TOP BAIRROS: {df_validos['Bairro'].value_counts().head(3).to_string()}
    
    ❌ CANCELAMENTOS: {len(df_cancelados)} ({len(df_cancelados)/(len(df_validos)+len(df_cancelados)):.1%})
    """
    
    # Inicializa o chat
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Olá! Sou o Oráculo da La Brasa Burger. 🍔\n\nPergunte-me sobre:\n- Análise de vendas\n- Padrões de consumo\n- Como melhorar resultados"}
        ]
    
    # Mostra histórico
    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])
    
    # Input do usuário
    if prompt := st.chat_input("Ex: 'Como melhorar as vendas às segundas?'"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)
        
        with st.spinner("Analisando os dados..."):
            resposta = DeepSeekAPI.ask(
                question=prompt,
                context=context,
                historical_data={
                    "df_validos": df_validos.describe().to_dict(),
                    "df_cancelados": df_cancelados.describe().to_dict()
                }
            )
        
        st.session_state.messages.append({"role": "assistant", "content": resposta})
        st.chat_message("assistant", avatar="🍔").write(resposta)

show_oraculo()
