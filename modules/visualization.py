# modules/visualization.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

def aplicar_css_local(caminho_arquivo):
    """Aplica um arquivo CSS local ao app Streamlit."""
    try:
        with open(caminho_arquivo) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.error(f"Arquivo CSS não encontrado em: {caminho_arquivo}")

def formatar_moeda(valor):
    """Formata um número para o padrão monetário brasileiro (R$)."""
    if valor is None:
        return "R$ 0,00"
    return f"R$ {valor:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")

def criar_card(label, valor, icone):
    """Cria um card de resumo customizado com HTML e CSS."""
    st.markdown(f"""
    <div class="metric-card" style="height: 130px;">
        <div class="metric-label">
            <span class="metric-icon">{icone}</span>
            <span>{label}</span>
        </div>
        <div class="metric-value">{valor}</div>
    </div>
    """, unsafe_allow_html=True)

def criar_cards_resumo(df):
    """Cria os 3 cards principais de resumo."""
    faturamento_sem_taxas = df['Total'].sum() - df['Total taxa de serviço'].sum()
    total_taxas = df['Total taxa de serviço'].sum()
    total_geral = df['Total'].sum()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        criar_card("Faturamento (sem taxas)", formatar_moeda(faturamento_sem_taxas), "💰")
    with col2:
        criar_card("Total em Taxas", formatar_moeda(total_taxas), "🧾")
    with col3:
        criar_card("Faturamento Geral", formatar_moeda(total_geral), "📈")


def criar_cards_dias_semana(df):
    """Cria 7 cards para os dias da semana, com estilo customizado e todas as métricas."""
    st.subheader(":icon[calendar-week] Análise por Dia da Semana")

    dias_semana = ['1. Segunda', '2. Terça', '3. Quarta', '4. Quinta', '5. Sexta', '6. Sábado', '7. Domingo']
    
    cols = st.columns(7)

    for i, dia in enumerate(dias_semana):
        nome_dia_semana = dia.split('. ')[1]
        
        with cols[i]:
            df_dia = df[df['Dia da Semana'] == dia]

            # Inicia a construção do card com Markdown
            st.markdown(f"""
            <div class="metric-card" style="height: 250px;">
                <div class="metric-label">{nome_dia_semana}</div>
            """, unsafe_allow_html=True)

            if df_dia.empty:
                st.markdown("<div class='metric-value' style='font-size: 1rem;'>Sem dados</div>", unsafe_allow_html=True)
            else:
                total_vendas_dia = df_dia['Total'].sum()
                num_pedidos_dia = len(df_dia)
                ticket_medio = total_vendas_dia / num_pedidos_dia if num_pedidos_dia > 0 else 0
                
                horario_pico = df_dia['Hora'].mode()
                if not horario_pico.empty:
                    horario_pico_val = int(horario_pico.iloc[0])
                    horario_pico_str = f"{horario_pico_val}h - {horario_pico_val+1}h"
                    df_horario_pico = df_dia[df_dia['Hora'] == horario_pico_val]
                    valor_medio_pico = df_horario_pico['Total'].mean() if not df_horario_pico.empty else 0
                else:
                    horario_pico_str = "N/A"
                    valor_medio_pico = 0

                num_dias_unicos = df_dia['Data'].nunique()
                media_pedidos_dia = num_pedidos_dia / num_dias_unicos if num_dias_unicos > 0 else 0

                # Exibe a métrica principal (Ticket Médio)
                st.markdown(f"<div class='metric-value'>{formatar_moeda(ticket_medio)}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='metric-label' style='font-size: 0.8rem;'>Ticket Médio</div>", unsafe_allow_html=True)
                
                # Divisor e métricas secundárias
                st.markdown("<hr class='metric-divider'>", unsafe_allow_html=True)
                st.markdown(f"<div class='secondary-metric'>Pedidos/Dia: <b>{media_pedidos_dia:.1f}</b></div>", unsafe_allow_html=True)
                st.markdown(f"<div class='secondary-metric'>Horário Pico: <b>{horario_pico_str}</b></div>", unsafe_allow_html=True)
                st.markdown(f"<div class='secondary-metric'>Média Pico: <b>{formatar_moeda(valor_medio_pico)}</b></div>", unsafe_allow_html=True)
            
            # Fecha a div do card
            st.markdown("</div>", unsafe_allow_html=True)


def criar_grafico_tendencia(df):
    """Cria um gráfico de linha com Plotly que mostra a tendência do faturamento diário."""
    st.subheader(":icon[graph-up] Tendência do Faturamento Diário")

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
        fig.add_trace(go.Scatter(
            x=daily_revenue['Data'].iloc[i-1:i+1],
            y=daily_revenue['Total'].iloc[i-1:i+1],
            mode='lines',
            line=dict(color=color, width=3),
            hoverinfo='skip' 
        ))

    fig.add_trace(go.Scatter(
        x=daily_revenue['Data'],
        y=daily_revenue['Total'],
        mode='markers',
        marker=dict(color='#FAFAFA', size=6, line=dict(color='#333', width=1)),
        hoverinfo='text',
        text=[f"Data: {d.strftime('%d/%m/%Y')}<br>Faturamento: {formatar_moeda(v)}" for d, v in zip(daily_revenue['Data'], daily_revenue['Total'])]
    ))

    fig.update_layout(
        template="streamlit",
        showlegend=False,
        yaxis_title="Faturamento (R$)",
        xaxis_title="Data",
        margin=dict(l=20, r=20, t=20, b=20),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        height=350,
    )
    
    st.plotly_chart(fig, use_container_width=True)
