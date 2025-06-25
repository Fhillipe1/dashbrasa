# modules/visualization.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

def formatar_moeda(valor):
    """
    Formata um número para o padrão monetário brasileiro (R$).
    Exemplo: 1234.56 -> R$ 1.234,56
    """
    if valor is None:
        return "R$ 0,00"
    return f"R$ {valor:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")

def criar_cards_dias_semana(df):
    """
    Cria 7 cards, um para cada dia da semana, com métricas específicas.
    """
    st.subheader("Análise por Dia da Semana")

    dias_semana = ['1. Segunda', '2. Terça', '3. Quarta', '4. Quinta', '5. Sexta', '6. Sábado', '7. Domingo']
    
    cols = st.columns(7)

    for i, dia in enumerate(dias_semana):
        nome_dia_semana = dia.split('. ')[1]
        
        with cols[i]:
            st.markdown(f"<h5 style='text-align: center; height: 40px;'>{nome_dia_semana}</h5>", unsafe_allow_html=True)
            
            df_dia = df[df['Dia da Semana'] == dia]

            if df_dia.empty:
                st.text("Sem dados")
                # Preenche o espaço para manter o alinhamento
                for _ in range(4):
                    st.text("")
                continue

            total_vendas_dia = df_dia['Total'].sum()
            num_pedidos_dia = len(df_dia)
            ticket_medio = total_vendas_dia / num_pedidos_dia if num_pedidos_dia > 0 else 0
            
            horario_pico = df_dia['Hora'].mode()
            if not horario_pico.empty:
                horario_pico = int(horario_pico.iloc[0])
                horario_pico_str = f"{horario_pico}h - {horario_pico+1}h"
                df_horario_pico = df_dia[df_dia['Hora'] == horario_pico]
                valor_medio_pico = df_horario_pico['Total'].mean() if not df_horario_pico.empty else 0
            else:
                horario_pico_str = "N/A"
                valor_medio_pico = 0

            num_dias_unicos = df_dia['Data'].nunique()
            media_pedidos_dia = num_pedidos_dia / num_dias_unicos if num_dias_unicos > 0 else 0

            st.metric(label="Ticket Médio", value=formatar_moeda(ticket_medio))
            st.metric(label="Média de Pedidos", value=f"{media_pedidos_dia:.1f}")
            st.metric(label="Horário de Pico", value=horario_pico_str)
            st.metric(label="Média por Pedido (Pico)", value=formatar_moeda(valor_medio_pico))


def criar_grafico_tendencia(df):
    """
    Cria um gráfico de linha com Plotly que mostra a tendência do faturamento diário.
    A linha é colorida de verde para aumentos e vermelho para quedas.
    """
    st.subheader("Tendência do Faturamento Diário")

    # Agrupa os dados por dia e soma o faturamento
    daily_revenue = df.groupby('Data')['Total'].sum().reset_index()
    
    # Se tivermos menos de 2 dias, não há tendência para mostrar
    if len(daily_revenue) < 2:
        st.info("É necessário ter pelo menos dois dias de dados no período selecionado para mostrar uma tendência.")
        return

    # Calcula a diferença em relação ao dia anterior
    daily_revenue['diff'] = daily_revenue['Total'].diff()

    fig = go.Figure()

    # Adiciona os segmentos de linha um por um, colorindo-os
    for i in range(1, len(daily_revenue)):
        color = "green" if daily_revenue['diff'].iloc[i] >= 0 else "red"
        fig.add_trace(go.Scatter(
            x=daily_revenue['Data'].iloc[i-1:i+1],
            y=daily_revenue['Total'].iloc[i-1:i+1],
            mode='lines+markers',
            line=dict(color=color, width=2.5),
            marker=dict(size=4),
            hoverinfo='skip' # Desativa o hover para os segmentos individuais
        ))

    # Adiciona uma linha "invisível" completa para ter um hover unificado e limpo
    fig.add_trace(go.Scatter(
        x=daily_revenue['Data'],
        y=daily_revenue['Total'],
        mode='lines',
        line=dict(color='rgba(0,0,0,0)'), # Linha transparente
        hoverinfo='text',
        text=[f"Data: {d.strftime('%d/%m/%Y')}<br>Faturamento: {formatar_moeda(v)}" for d, v in zip(daily_revenue['Data'], daily_revenue['Total'])]
    ))

    # Customiza o layout para ficar limpo e adaptável ao tema do Streamlit
    fig.update_layout(
        template="streamlit",
        showlegend=False,
        yaxis_title="Faturamento (R$)",
        xaxis_title="Data",
        margin=dict(l=20, r=20, t=20, b=20),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )
    
    st.plotly_chart(fig, use_container_width=True)
