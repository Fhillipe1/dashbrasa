# modules/sao_joao_handler.py

import streamlit as st
import pandas as pd
import altair as alt
from . import visualization # Importa nosso módulo de visualização para usar o formatar_moeda

def display_kpis(df):
    """Exibe os KPIs principais: Faturamento Total e Número de Pedidos."""
    if df.empty:
        st.info("Nenhum dado encontrado para o período e filtros selecionados.")
        return

    faturamento_total = df['Total'].sum()
    num_pedidos = len(df)

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Faturamento Total (Madrugada)", visualization.formatar_moeda(faturamento_total))
    with col2:
        st.metric("Nº de Pedidos (Madrugada)", num_pedidos)

def display_daily_revenue_chart(df):
    """Exibe um gráfico de linha com a evolução do faturamento por dia."""
    st.markdown("##### Faturamento Diário na Madrugada")
    
    if df.empty:
        return

    df_daily = df.groupby(df['Data'].dt.date)['Total'].sum().reset_index()
    
    chart = alt.Chart(df_daily).mark_line(
        point=alt.OverlayMarkDef(color="#2196F3"),
        color='#2196F3'
    ).encode(
        x=alt.X('Data:T', title='Data'),
        y=alt.Y('Total:Q', title='Faturamento (R$)'),
        tooltip=[
            alt.Tooltip('Data:T', title='Data'),
            alt.Tooltip('Total:Q', title='Faturamento', format='$,.2f')
        ]
    ).properties(
        height=300
    )
    st.altair_chart(chart, use_container_width=True)

def display_payment_method_pie_chart(df):
    """Exibe um gráfico de pizza com a distribuição do faturamento por forma de pagamento."""
    st.markdown("##### Faturamento por Forma de Pagamento")

    if df.empty or 'Forma de pagamento' not in df.columns:
        return

    df_payment = df.groupby('Forma de pagamento')['Total'].sum().reset_index()

    chart = alt.Chart(df_payment).mark_arc(innerRadius=50).encode(
        theta=alt.Theta(field="Total", type="quantitative", stack=True),
        color=alt.Color(field="Forma de pagamento", type="nominal", legend=alt.Legend(title="Formas de Pagamento")),
        tooltip=[
            alt.Tooltip('Forma de pagamento', title='Forma de Pagamento'),
            alt.Tooltip('Total:Q', title='Faturamento', format='$,.2f')
        ]
    ).properties(
        height=350
    )
    st.altair_chart(chart, use_container_width=True)


def display_hourly_performance_chart(df):
    """Exibe um gráfico de barras com Pedidos e Faturamento por hora."""
    st.markdown("##### Performance por Hora (00h - 05h)")
    if df.empty:
        return

    hourly_summary = df.groupby('Hora').agg(
        Pedidos=('Pedido', 'count'),
        Faturamento=('Total', 'sum')
    ).reset_index()

    # Garante que todas as horas da madrugada estejam presentes
    horas_madrugada = pd.DataFrame({'Hora': range(5)}) # Horas 0, 1, 2, 3, 4
    hourly_summary = pd.merge(horas_madrugada, hourly_summary, on='Hora', how='left').fillna(0)

    # Gráfico de barras
    base = alt.Chart(hourly_summary).encode(x=alt.X('Hora:O', title='Hora', axis=alt.Axis(labelAngle=0)))

    barras = base.mark_bar().encode(
        y=alt.Y('Pedidos:Q', title='Nº de Pedidos'),
        color=alt.value('#2196F3'),
        tooltip=[
            alt.Tooltip('Hora:N', title='Hora'),
            alt.Tooltip('Pedidos:Q', title='Nº de Pedidos'),
            alt.Tooltip('Faturamento:Q', title='Faturamento', format='$,.2f')
        ]
    )

    pontos = base.mark_point(
        size=100,
        filled=True,
        color='orange'
    ).encode(
        y=alt.Y('Faturamento:Q', title='Faturamento (R$)'),
    )
    
    # Combina os gráficos
    chart = alt.layer(barras, pontos).resolve_scale(y='independent').properties(height=300)
    st.altair_chart(chart, use_container_width=True)
