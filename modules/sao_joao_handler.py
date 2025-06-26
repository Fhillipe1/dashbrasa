# modules/sao_joao_handler.py

import streamlit as st
import pandas as pd
import altair as alt
from . import visualization as viz

def display_kpis(df):
    """Exibe os KPIs principais: Faturamento Total e Número de Pedidos."""
    st.markdown("##### <i class='bi bi-clipboard-data'></i> Resumo do Período", unsafe_allow_html=True)
    
    if df.empty:
        st.info("Nenhum dado encontrado para o período e filtros selecionados.")
        return

    faturamento_total = df['Total'].sum()
    num_pedidos = len(df)

    col1, col2 = st.columns(2)
    with col1:
        viz.criar_card("Faturamento na Madrugada", viz.formatar_moeda(faturamento_total), "<i class='bi bi-moon-stars-fill'></i>")
    with col2:
        viz.criar_card("Nº de Pedidos na Madrugada", f"{num_pedidos}", "<i class='bi bi-journal-check'></i>")

def display_daily_revenue_chart(df):
    """Exibe um gráfico de linha com a evolução do faturamento por dia."""
    st.markdown("##### <i class='bi bi-graph-up'></i> Faturamento Diário na Madrugada", unsafe_allow_html=True)
    
    if df.empty: return
    
    df_daily = df.groupby(df['Data'])['Total'].sum().reset_index()

    if len(df_daily) < 2:
        st.info("Selecione pelo menos dois dias no filtro para visualizar a tendência.")
        return
    
    chart = alt.Chart(df_daily).mark_line(
        point=alt.OverlayMarkDef(color="#FFD700"),
        color='#2196F3'
    ).encode(
        x=alt.X('Data:T', title='Data'),
        y=alt.Y('Total:Q', title='Faturamento (R$)'),
        tooltip=[alt.Tooltip('Data:T', title='Data', format='%d/%m/%Y'), alt.Tooltip('Total:Q', title='Faturamento', format='R$,.2f')]
    ).properties(height=300)
    st.altair_chart(chart, use_container_width=True)

def display_payment_method_pie_chart(df, payment_col):
    """Exibe um gráfico de pizza com a distribuição do faturamento por forma de pagamento."""
    st.markdown("##### <i class='bi bi-pie-chart-fill'></i> Faturamento por Forma de Pagamento", unsafe_allow_html=True)

    if df.empty or not payment_col:
        st.info("Coluna de forma de pagamento não encontrada ou sem dados para exibir.")
        return

    df_payment = df.groupby(payment_col)['Total'].sum().reset_index()

    chart = alt.Chart(df_payment).mark_arc(innerRadius=50).encode(
        theta=alt.Theta(field="Total", type="quantitative", stack=True),
        color=alt.Color(field=payment_col, type="nominal", legend=alt.Legend(title="Formas de Pagamento")),
        tooltip=[alt.Tooltip(payment_col, title='Pagamento'), alt.Tooltip('Total:Q', title='Faturamento', format='R$,.2f')]
    ).properties(height=350)
    st.altair_chart(chart, use_container_width=True)

def display_hourly_performance_chart(df):
    """Exibe um gráfico de barras com Pedidos por hora."""
    st.markdown("##### <i class='bi bi-clock-history'></i> Pedidos por Hora (Madrugada)", unsafe_allow_html=True)
    if df.empty: return

    hourly_summary = df.groupby('Hora').agg(Pedidos=('Pedido', 'count')).reset_index()
    horas_madrugada = pd.DataFrame({'Hora': range(5)})
    hourly_summary = pd.merge(horas_madrugada, hourly_summary, on='Hora', how='left').fillna(0)

    chart = alt.Chart(hourly_summary).mark_bar().encode(
        x=alt.X('Hora:O', title='Hora', axis=alt.Axis(labelAngle=0)),
        y=alt.Y('Pedidos:Q', title='Nº de Pedidos'),
        tooltip=[alt.Tooltip('Hora:N', title='Hora'), alt.Tooltip('Pedidos:Q', title='Nº de Pedidos')]
    ).properties(height=300)
    st.altair_chart(chart, use_container_width=True)
