# modules/sao_joao_handler.py

import streamlit as st
import pandas as pd
import altair as alt
from . import visualization as viz 

def display_kpis(df):
    """Exibe os KPIs principais: Faturamento Total e Número de Pedidos."""
    st.markdown("##### <i class='bi bi-clipboard-data'></i> Resumo do Período", unsafe_allow_html=True)
    
    # Usa nosso card customizado para manter a identidade visual
    with st.container(border=False):
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
    
    if df.empty:
        st.info("Nenhum dado no período selecionado.")
        return
    
    df_daily = df.groupby('Data')['Total'].sum().reset_index()

    if len(df_daily) < 2:
        st.info("Selecione pelo menos dois dias no filtro para visualizar a tendência.")
        return
    
    chart = alt.Chart(df_daily).mark_line(
        point=alt.OverlayMarkDef(color="#FFB347"),
        color='#FF4B4B'
    ).encode(
        x=alt.X('Data:T', title='Data'),
        y=alt.Y('Total:Q', title='Faturamento (R$)'),
        tooltip=[
            alt.Tooltip('Data:T', title='Data', format='%d/%m/%Y'),
            alt.Tooltip('Total:Q', title='Faturamento', format='R$,.2f')
        ]
    ).properties(height=350)
    st.altair_chart(chart, use_container_width=True)

def display_hourly_performance_chart(df):
    """Exibe um gráfico de barras com Faturamento e hover com mais detalhes."""
    st.markdown("##### <i class='bi bi-clock-history'></i> Performance por Hora (Madrugada)", unsafe_allow_html=True)
    if df.empty:
        st.info("Nenhum dado no período selecionado.")
        return

    hourly_summary = df.groupby('Hora').agg(
        Pedidos=('Pedido', 'count'),
        Faturamento=('Total', 'sum')
    ).reset_index()

    horas_madrugada = pd.DataFrame({'Hora': range(5)})
    hourly_summary = pd.merge(horas_madrugada, hourly_summary, on='Hora', how='left').fillna(0)
    
    hourly_summary['Ticket Medio'] = hourly_summary.apply(
        lambda row: row['Faturamento'] / row['Pedidos'] if row['Pedidos'] > 0 else 0, axis=1
    )

    # Gráfico de barras onde a altura é o Faturamento
    barras = alt.Chart(hourly_summary).mark_bar(
        cornerRadius=5
    ).encode(
        x=alt.X('Hora:O', title='Hora', axis=alt.Axis(labelAngle=0)),
        y=alt.Y('Faturamento:Q', title='Faturamento (R$)'),
        color=alt.Color('Faturamento:Q', scale=alt.Scale(scheme='reds'), legend=None),
        tooltip=[
            alt.Tooltip('Hora:N', title='Hora'),
            alt.Tooltip('Faturamento:Q', title='Faturamento', format='R$,.2f'),
            alt.Tooltip('Pedidos:Q', title='Nº de Pedidos'),
            alt.Tooltip('Ticket Medio:Q', title='Ticket Médio', format='R$,.2f')
        ]
    )
    
    # Texto (indicador) em cima das barras
    texto = barras.mark_text(
        align='center',
        baseline='bottom',
        dy=-5, # Deslocamento vertical para ficar acima da barra
        color='white'
    ).encode(
        text=alt.Text('Faturamento:Q', format=',.0f')
    )

    chart = (barras + texto).properties(height=350)
    st.altair_chart(chart, use_container_width=True)
