# modules/sao_joao_handler.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.figure_factory as ff
from . import visualization as viz

def display_kpis(df):
    """Exibe os KPIs principais: Faturamento Total e Número de Pedidos."""
    if df.empty:
        total_revenue = 0.0
        total_orders = 0
    else:
        total_revenue = df['Total'].sum()
        total_orders = len(df)

    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Faturamento Total (Madrugada)", value=viz.formatar_moeda(total_revenue))
    with col2:
        st.metric(label="Total de Pedidos (Madrugada)", value=f"{total_orders}")

def display_daily_revenue_chart(df):
    """Exibe um gráfico de linha com a evolução do faturamento por dia."""
    with st.container(border=False):
        st.markdown("<h5 class='card-title'>Faturamento Diário na Madrugada</h5>", unsafe_allow_html=True)
        if df.empty or len(df['Data'].unique()) < 2:
            st.info("Selecione pelo menos dois dias para ver a tendência.")
            return
        
        daily_revenue = df.groupby('Data')['Total'].sum().reset_index()
        fig = go.Figure(data=go.Scatter(
            x=daily_revenue['Data'], y=daily_revenue['Total'],
            mode='lines+markers', line=dict(color='#FF4B4B', width=3),
            marker=dict(size=8, color='#FFB347', line=dict(width=1, color='#FF4B4B'))
        ))
        fig.update_layout(
            template="plotly_dark", yaxis_title='Faturamento (R$)',
            margin=dict(t=30, b=30, l=40, r=40),
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig, use_container_width=True)

def display_payment_method_pie_chart(df, payment_col):
    """Exibe um gráfico de pizza com a distribuição do faturamento por forma de pagamento."""
    with st.container(border=False):
        st.markdown("<h5 class='card-title'>Faturamento por Forma de Pagamento</h5>", unsafe_allow_html=True)
        if df.empty or not payment_col:
            st.info("Não há dados de pagamento para exibir."); return

        payment_revenue = df.groupby(payment_col)['Total'].sum().reset_index()
        pie_colors = ['#FF4B4B', '#FFB347', '#7ACC7A', '#5CB0E8', '#AF7AE3', '#FF8C4B']
        fig = go.Figure(data=go.Pie(
            values=payment_revenue['Total'], labels=payment_revenue[payment_col],
            hole=0.4, marker=dict(colors=pie_colors, line=dict(color='#0E1117', width=1.5)),
            textposition='inside', textinfo='percent+label', hoverinfo='label+percent+value'
        ))
        fig.update_layout(template="plotly_dark", margin=dict(t=30, b=30, l=40, r=40), paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)

def display_hourly_performance_chart(df):
    """Exibe um gráfico de barras com Pedidos e Faturamento por hora."""
    with st.container(border=False):
        st.markdown("<h5 class='card-title'>Pedidos por Hora na Madrugada</h5>", unsafe_allow_html=True)
        if df.empty: return

        hourly_summary = df.groupby('Hora').agg(Contagem_de_Pedidos=('Pedido', 'count')).reset_index()
        horas_template = pd.DataFrame({'Hora': range(5)})
        hourly_summary = pd.merge(horas_template, hourly_summary, on='Hora', how='left').fillna(0)
        
        hourly_summary['Hora_Str'] = hourly_summary['Hora'].apply(lambda x: f'{x:02d}:00')

        fig = go.Figure(data=go.Bar(
            x=hourly_summary['Hora_Str'], y=hourly_summary['Contagem_de_Pedidos'],
            marker=dict(color=hourly_summary['Contagem_de_Pedidos'], colorscale='Bluyl', line=dict(color='#0E1117', width=1)),
            hovertemplate="<b>Hora</b>: %{x}<br><b>Pedidos</b>: %{y}<extra></extra>"
        ))
        fig.update_layout(xaxis_title='Hora', yaxis_title='Número de Pedidos', template="plotly_dark", margin=dict(t=30, b=30, l=40, r=40), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)
