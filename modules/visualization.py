# modules/visualization.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import textwrap
import altair as alt
import pydeck as pdk # Importa a biblioteca para o mapa

def aplicar_css_local(caminho_arquivo):
    try:
        with open(caminho_arquivo) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.error(f"Arquivo CSS não encontrado em: {caminho_arquivo}")

def formatar_moeda(valor):
    if valor is None: return "R$ 0,00"
    return f"R$ {valor:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")

def criar_card(label, valor, icone_html, delta_text=None):
    delta_html = ""
    if delta_text is not None:
        delta_str = str(delta_text)
        if delta_str.startswith('-'):
            delta_class = "metric-delta-negative"
            seta = "▼"
        else:
            delta_class = "metric-delta-positive"
            seta = "▲"
            if not delta_str.startswith('+'):
                 delta_str = "+" + delta_str
        delta_html = f"<div class='metric-delta {delta_class}'>{seta} {delta_str}</div>"
    card_html = f"""<div class="metric-card" style="min-height: 130px;"><div class="metric-label"><span class="metric-icon">{icone_html}</span><span>{label}</span></div><div class="metric-value">{valor}</div>{delta_html}</div>"""
    st.markdown(card_html, unsafe_allow_html=True)

def criar_cards_resumo(df):
    faturamento_sem_taxas = df['Total'].sum() - df['Total taxa de serviço'].sum()
    total_taxas = df['Total taxa de serviço'].sum()
    total_geral = df['Total'].sum()
    col1, col2, col3 = st.columns(3)
    with col1:
        criar_card("Faturamento (sem taxas)", formatar_moeda(faturamento_sem_taxas), "<i class='bi bi-cash-coin'></i>")
    with col2:
        criar_card("Total em Taxas", formatar_moeda(total_taxas), "<i class='bi bi-receipt'></i>")
    with col3:
        criar_card("Faturamento Geral", formatar_moeda(total_geral), "<i class='bi bi-graph-up-arrow'></i>")

def criar_cards_delivery_resumo(df_delivery_filtrado, df_delivery_total):
    qtd_entregas = len(df_delivery_filtrado)
    faturamento_delivery = df_delivery_filtrado['Total'].sum()
    ticket_medio_delivery = faturamento_delivery / qtd_entregas if qtd_entregas > 0 else 0
    dias_no_filtro = df_delivery_filtrado['Data'].nunique()
    media_pedidos_diaria_filtro = qtd_entregas / dias_no_filtro if dias_no_filtro > 0 else 0
    dias_no_total = df_delivery_total['Data'].nunique()
    media_pedidos_diaria_total = len(df_delivery_total) / dias_no_total if dias_no_total > 0 else 0
    delta_pedidos_percent = ((media_pedidos_diaria_filtro - media_pedidos_diaria_total) / media_pedidos_diaria_total) * 100 if media_pedidos_diaria_total > 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        criar_card("Total de Entregas", f"{qtd_entregas}", "<i class='bi bi-truck'></i>")
    with col2:
        criar_card("Faturamento Delivery", formatar_moeda(faturamento_delivery), "<i class='bi bi-cash-stack'></i>")
    with col3:
        criar_card("Ticket Médio Delivery", formatar_moeda(ticket_medio_delivery), "<i class='bi bi-tag-fill'></i>")
    with col4:
        criar_card(label="Pedidos/Dia vs Média", valor=f"{media_pedidos_diaria_filtro:.1f}", icone_html="<i class='bi bi-speedometer2'></i>", delta_text=f"{delta_pedidos_percent:.2f}%")

def criar_cards_dias_semana(df):
    st.markdown("#### <i class='bi bi-calendar-week'></i> Análise por Dia da Semana", unsafe_allow_html=True)
    dias_semana = ['1. Segunda', '2. Terça', '3. Quarta', '4. Quinta', '5. Sexta', '6. Sábado', '7. Domingo']
    cols = st.columns(7)
    for i, dia in enumerate(dias_semana):
        with cols[i]:
            df_dia = df[df['Dia da Semana'] == dia]
            nome_dia_semana = dia.split('. ')[1]
            if df_dia.empty:
                card_html = f"""<div class="metric-card" style="min-height: 230px;"><p class="metric-label" style="font-size: 1.1rem;">{nome_dia_semana}</p><div class='metric-value' style='font-size: 1rem; color: #555; margin-top: 1rem;'>Sem dados</div></div>"""
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
                media_pedidos_dia = num_dias_unicos > 0 and num_pedidos_dia / num_dias_unicos or 0
                card_html = textwrap.dedent(f"""<div class="metric-card" style="min-height: 230px;"><p class="metric-label" style="font-size: 1.1rem;">{nome_dia_semana}</p><p class="metric-value">{formatar_moeda(ticket_medio)}</p><p class="metric-label" style="font-size: 0.8rem; margin-bottom: 8px;">Ticket Médio</p><hr class="metric-divider"><p class="secondary-metric">Pedidos/Dia: <b>{media_pedidos_dia:.1f}</b></p><p class="secondary-metric">Horário Pico: <b>{horario_pico_str}</b></p><p class="secondary-metric">Média Pico: <b>{formatar_moeda(valor_medio_pico)}</b></p></div>""")
            st.markdown(card_html, unsafe_allow_html=True)

def criar_grafico_tendencia(df):
    st.markdown("##### <i class='bi bi-graph-up'></i> Tendência do Faturamento Diário", unsafe_allow_html=True)
    if df.empty or len(df.groupby('Data')) < 2:
        st.info("É necessário ter pelo menos dois dias de dados no período selecionado para mostrar uma tendência.")
        return
    daily_revenue = df.groupby(pd.to_datetime(df['Data']))['Total'].sum().reset_index().sort_values(by='Data')
    daily_revenue['diff'] = daily_revenue['Total'].diff()
    fig = go.Figure()
    for i in range(1, len(daily_revenue)):
        color = "#2E8B57" if daily_revenue['diff'].iloc[i] >= 0 else "#CD5C5C"
        fig.add_trace(go.Scatter(x=daily_revenue['Data'].iloc[i-1:i+1], y=daily_revenue['Total'].iloc[i-1:i+1], mode='lines', line=dict(color=color, width=3), hoverinfo='skip'))
    fig.add_trace(go.Scatter(x=daily_revenue['Data'], y=daily_revenue['Total'], mode='markers', marker=dict(color='#FAFAFA', size=6, line=dict(color='#333', width=1)), hoverinfo='text', text=[f"Data: {d.strftime('%d/%m/%Y')}<br>Faturamento: {formatar_moeda(v)}" for d, v in zip(daily_revenue['Data'], daily_revenue['Total'])]))
    fig.update_layout(template="streamlit", showlegend=False, yaxis_title="Faturamento (R$)", xaxis_title="Data", margin=dict(l=20, r=20, t=20, b=20), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', height=350)
    st.plotly_chart(fig, use_container_width=True)

def criar_grafico_barras_horarios(df):
    st.markdown("##### <i class='bi bi-clock-history'></i> Performance por Hora", unsafe_allow_html=True)
    if df.empty:
        st.info("Não há dados para exibir no gráfico de performance por hora.")
        return
    hourly_summary = df.groupby('Hora').agg(Num_Pedidos=('Pedido', 'count'), Faturamento_Total=('Total', 'sum')).reset_index()
    horas_template = pd.DataFrame({'Hora': range(24)})
    hourly_summary = pd.merge(horas_template, hourly_summary, on='Hora', how='left').fillna(0)
    hourly_summary['Ticket_Medio'] = hourly_summary.apply(lambda row: row['Faturamento_Total'] / row['Num_Pedidos'] if row['Num_Pedidos'] > 0 else 0, axis=1)
    chart = alt.Chart(hourly_summary).mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3).encode(x=alt.X('Hora:O', title='Hora do Dia', axis=alt.Axis(labelAngle=0)), y=alt.Y('Num_Pedidos:Q', title='Número de Pedidos'), color=alt.Color('Num_Pedidos:Q', scale=alt.Scale(scheme='blues'), legend=None), tooltip=[alt.Tooltip('Hora:N', title='Hora do Dia'), alt.Tooltip('Num_Pedidos:Q', title='Nº de Pedidos'), alt.Tooltip('Faturamento_Total:Q', title='Faturamento', format='$.2f'), alt.Tooltip('Ticket_Medio:Q', title='Ticket Médio', format='$.2f')]).configure_axis(grid=False).configure_view(strokeWidth=0)
    st.altair_chart(chart, use_container_width=True)

def criar_top_bairros_delivery(df_delivery_filtrado, df_delivery_total):
    st.markdown("#### <i class='bi bi-geo-alt-fill'></i> Top Bairros por Nº de Entregas", unsafe_allow_html=True)
    if df_delivery_filtrado.empty:
        st.info("Sem dados de delivery para analisar os bairros.")
        return
    top_bairros = df_delivery_filtrado['Bairro'].value_counts().nlargest(3).index.tolist()
    if not top_bairros:
        st.info("Não há informações de bairro suficientes para gerar o top 3.")
        return
    cols = st.columns(3)
    for i, bairro_nome in enumerate(top_bairros):
        with cols[i]:
            df_bairro_filtrado = df_delivery_filtrado[df_delivery_filtrado['Bairro'] == bairro_nome]
            df_bairro_total = df_delivery_total[df_delivery_total['Bairro'] == bairro_nome]
            pedidos_bairro = len(df_bairro_filtrado)
            faturamento_bairro = df_bairro_filtrado['Total'].sum()
            ticket_medio_bairro = faturamento_bairro / pedidos_bairro if pedidos_bairro > 0 else 0
            total_taxa_entrega = df_bairro_filtrado['Entrega'].sum()
            dias_no_filtro = df_bairro_filtrado['Data'].nunique()
            media_diaria_filtro = pedidos_bairro / dias_no_filtro if dias_no_filtro > 0 else 0
            dias_no_total = df_bairro_total['Data'].nunique()
            media_diaria_total = len(df_bairro_total) / dias_no_total if dias_no_total > 0 else 0
            delta_percent = ((media_diaria_filtro - media_diaria_total) / media_diaria_total) * 100 if media_diaria_total > 0 else 0
            delta_str = f"{delta_percent:+.2f}%"
            card_html = textwrap.dedent(f"""<div class="metric-card" style="min-height: 230px;"><p class="metric-label" style="font-size: 1.1rem;">{i+1}º - {bairro_nome}</p><p class="metric-value">{pedidos_bairro}</p><p class="metric-label" style="font-size: 0.8rem; margin-bottom: 8px;">Nº de Pedidos</p><div class='metric-delta {'metric-delta-positive' if delta_percent >= 0 else 'metric-delta-negative'}'>{'▲' if delta_percent >= 0 else '▼'} {delta_str.replace('-', '')} vs Média</div><hr class="metric-divider"><p class="secondary-metric">Faturamento: <b>{formatar_moeda(faturamento_bairro)}</b></p><p class="secondary-metric">Ticket Médio: <b>{formatar_moeda(ticket_medio_bairro)}</b></p><p class="secondary-metric">Total Taxas: <b>{formatar_moeda(total_taxa_entrega)}</b></p></div>""")
            st.markdown(card_html, unsafe_allow_html=True)

# --- NOVA FUNÇÃO PARA O MAPA DE CALOR ---
def criar_mapa_de_calor(df_delivery, df_cache_cep):
    """Cria e exibe um mapa de calor das entregas usando Pydeck."""
    st.markdown("#### <i class='bi bi-map-fill'></i> Mapa de Calor das Entregas", unsafe_allow_html=True)

    # Junta os dados de entrega com as coordenadas do cache
    df_mapa = pd.merge(df_delivery, df_cache_cep, on='CEP', how='left')
    
    # Remove pedidos que não tiveram o CEP encontrado no cache
    df_mapa.dropna(subset=['lat', 'lon'], inplace=True)
    
    if df_mapa.empty:
        st.warning("Não foi possível gerar o mapa. Verifique se os CEPs dos pedidos existem no cache de coordenadas.")
        return

    # Converte lat/lon para numérico
    df_mapa['lat'] = pd.to_numeric(df_mapa['lat'])
    df_mapa['lon'] = pd.to_numeric(df_mapa['lon'])

    # Define a visualização inicial do mapa (centralizado na média das coordenadas)
    view_state = pdk.ViewState(
        latitude=df_mapa['lat'].mean(),
        longitude=df_mapa['lon'].mean(),
        zoom=11,
        pitch=50,
    )

    # Define a camada de mapa de calor
    heatmap_layer = pdk.Layer(
        'HeatmapLayer',
        data=df_mapa,
        get_position='[lon, lat]',
        opacity=0.9,
        get_weight=1, # Cada ponto tem o mesmo peso
        threshold=0.05,
        radius_pixels=40
    )

    # Renderiza o mapa
    st.pydeck_chart(pdk.Deck(
        map_style='mapbox://styles/mapbox/dark-v9',
        initial_view_state=view_state,
        layers=[heatmap_layer],
        tooltip={"text": "{Bairro}\nPedidos: {Num_Pedidos}"} # Tooltip a ser ajustado/melhorado
    ))
