# modules/visualization.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

def aplicar_css_local(caminho_arquivo):
    try:
        with open(caminho_arquivo) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.error(f"Arquivo CSS não encontrado em: {caminho_arquivo}")

def formatar_moeda(valor):
    if valor is None: return "R$ 0,00"
    return f"R$ {valor:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")

def criar_cards_resumo(df):
    """Cria os 3 cards principais de resumo usando st.metric."""
    faturamento_sem_taxas = df['Total'].sum() - df['Total taxa de serviço'].sum()
    total_taxas = df['Total taxa de serviço'].sum()
    total_geral = df['Total'].sum()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="💰 Faturamento (sem taxas)", value=formatar_moeda(faturamento_sem_taxas))
    with col2:
        st.metric(label="🧾 Total em Taxas", value=formatar_moeda(total_taxas))
    with col3:
        st.metric(label="📈 Faturamento Geral", value=formatar_moeda(total_geral))


def criar_cards_dias_semana(df):
    """Cria 7 cards para os dias da semana usando st.container e st.metric."""
    st.markdown("#### <i class='bi bi-calendar-week'></i> Análise por Dia da Semana", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    dias_semana = ['1. Segunda', '2. Terça', '3. Quarta', '4. Quinta', '5. Sexta', '6. Sábado', '7. Domingo']
    
    cols = st.columns(7)

    for i, dia in enumerate(dias_semana):
        with cols[i]:
            with st.container(border=True): # Usando o container nativo do Streamlit
                nome_dia_semana = dia.split('. ')[1]
                st.markdown(f"<h6 style='text-align: center;'>{nome_dia_semana}</h6>", unsafe_allow_html=True)
                
                df_dia = df[df['Dia da Semana'] == dia]

                if df_dia.empty:
                    st.markdown("<p style='text-align: center; font-size: 0.9rem;'>Sem dados</p>", unsafe_allow_html=True)
                else:
                    total_vendas_dia = df_dia['Total'].sum()
                    num_pedidos_dia = len(df_dia)
                    ticket_medio = total_vendas_dia / num_pedidos_dia if num_pedidos_dia > 0 else 0
                    
                    horario_pico = df_dia['Hora'].mode()
                    if not horario_pico.empty:
                        horario_pico_val = int(horario_pico.iloc[0])
                        horario_pico_str = f"{horario_pico_val}h"
                    else:
                        horario_pico_str = "N/A"

                    num_dias_unicos = df_dia['Data'].nunique()
                    media_pedidos_dia = num_pedidos_dia / num_dias_unicos if num_dias_unicos > 0 else 0

                    st.metric(label="Ticket Médio", value=formatar_moeda(ticket_medio))
                    st.metric(label="Média Pedidos/Dia", value=f"{media_pedidos_dia:.1f}")
                    st.metric(label="Horário de Pico", value=horario_pico_str)

def criar_grafico_tendencia(df):
    """Cria um gráfico de linha com Plotly."""
    st.markdown("#### <i class='bi bi-graph-up'></i> Tendência do Faturamento Diário", unsafe_allow_html=True)

    if df.empty:
        st.info("Não há dados para o período selecionado.")
        return

    daily_revenue = df.groupby(pd.to_datetime(df['Data']))['Total'].sum().reset_index()
    daily_revenue = daily_revenue.sort_values(by='Data')
    
    if len(daily_revenue) < 2:
        st.info("É necessário ter pelo menos dois dias de dados para mostrar uma tendência.")
        return

    daily_revenue['diff'] = daily_revenue['Total'].diff()

    fig = go.Figure()

    for i in range(1, len(daily_revenue)):
        color = "#2E8B57" if daily_revenue['diff'].iloc[i] >= 0 else "#CD5C5C"
        fig.add_trace(go.Scatter(x=daily_revenue['Data'].iloc[i-1:i+1], y=daily_revenue['Total'].iloc[i-1:i+1], mode='lines', line=dict(color=color, width=3), hoverinfo='skip'))

    fig.add_trace(go.Scatter(x=daily_revenue['Data'], y=daily_revenue['Total'], mode='markers', marker=dict(color='#FAFAFA', size=6, line=dict(color='#333', width=1)), hoverinfo='text', text=[f"Data: {d.strftime('%d/%m/%Y')}<br>Faturamento: {formatar_moeda(v)}" for d, v in zip(daily_revenue['Data'], daily_revenue['Total'])]))

    fig.update_layout(template="streamlit", showlegend=False, yaxis_title="Faturamento (R$)", xaxis_title="Data", margin=dict(l=20, r=20, t=20, b=20), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', height=350)
    
    st.plotly_chart(fig, use_container_width=True)
