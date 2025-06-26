# modules/visualization.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.figure_factory as ff
import textwrap
import altair as alt
import os

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
            delta_class = "metric-delta-negative"; seta = "▼"
        else:
            delta_class = "metric-delta-positive"; seta = "▲"
            if not delta_str.startswith('+'): delta_str = "+" + delta_str
        delta_html = f"<div class='metric-delta {delta_class}'>{seta} {delta_str}</div>"
    card_html = f"""<div class="metric-card" style="min-height: 130px;"><div class="metric-label"><span class="metric-icon">{icone_html}</span><span>{label}</span></div><div class="metric-value">{valor}</div>{delta_html}</div>"""
    st.markdown(card_html, unsafe_allow_html=True)

def criar_cards_resumo(df):
    if df.empty: return
    faturamento_sem_taxas = df['Total'].sum() - df['Total taxa de serviço'].sum()
    total_taxas = df['Total taxa de serviço'].sum()
    total_geral = df['Total'].sum()
    col1, col2, col3 = st.columns(3)
    with col1: criar_card("Faturamento (sem taxas)", formatar_moeda(faturamento_sem_taxas), "<i class='bi bi-cash-coin'></i>")
    with col2: criar_card("Total em Taxas", formatar_moeda(total_taxas), "<i class='bi bi-receipt'></i>")
    with col3: criar_card("Faturamento Geral", formatar_moeda(total_geral), "<i class='bi bi-graph-up-arrow'></i>")

def criar_cards_delivery_resumo(df_delivery_filtrado, df_delivery_total):
    if df_delivery_filtrado.empty: return
    qtd_entregas = len(df_delivery_filtrado)
    faturamento_delivery = df_delivery_filtrado['Total'].sum()
    ticket_medio_delivery = faturamento_delivery / qtd_entregas if qtd_entregas > 0 else 0
    dias_no_filtro = df_delivery_filtrado['Data'].nunique()
    media_pedidos_diaria_filtro = qtd_entregas / dias_no_filtro if dias_no_filtro > 0 else 0
    dias_no_total = df_delivery_total['Data'].nunique()
    media_pedidos_diaria_total = len(df_delivery_total) / dias_no_total if dias_no_total > 0 else 0
    delta_pedidos_percent = ((media_pedidos_diaria_filtro - media_pedidos_diaria_total) / media_pedidos_diaria_total) * 100 if media_pedidos_diaria_total > 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    with col1: criar_card("Total de Entregas", f"{qtd_entregas}", "<i class='bi bi-truck'></i>")
    with col2: criar_card("Faturamento Delivery", formatar_moeda(faturamento_delivery), "<i class='bi bi-cash-stack'></i>")
    with col3: criar_card("Ticket Médio Delivery", formatar_moeda(ticket_medio_delivery), "<i class='bi bi-tag-fill'></i>")
    with col4: criar_card(label="Pedidos/Dia vs Média", valor=f"{media_pedidos_diaria_filtro:.1f}", icone_html="<i class='bi bi-speedometer2'></i>", delta_text=f"{delta_pedidos_percent:.2f}%")

def criar_cards_dias_semana(df):
    if df.empty: return
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
                ticket_medio = df_dia['Total'].mean()
                horario_pico = df_dia['Hora'].mode()
                if not horario_pico.empty:
                    horario_pico_val = int(horario_pico.iloc[0])
                    horario_pico_str = f"{horario_pico_val}h - {horario_pico_val+1}h"
                    valor_medio_pico = df_dia[df_dia['Hora'] == horario_pico_val]['Total'].mean() if not df_dia[df_dia['Hora'] == horario_pico_val].empty else 0
                else:
                    horario_pico_str = "N/A"; valor_medio_pico = 0
                media_pedidos_dia = len(df_dia) / df_dia['Data'].nunique() if df_dia['Data'].nunique() > 0 else 0
                card_html = textwrap.dedent(f"""<div class="metric-card" style="min-height: 230px;"><p class="metric-label" style="font-size: 1.1rem;">{nome_dia_semana}</p><p class="metric-value">{formatar_moeda(ticket_medio)}</p><p class="metric-label" style="font-size: 0.8rem; margin-bottom: 8px;">Ticket Médio</p><hr class="metric-divider"><p class="secondary-metric">Pedidos/Dia: <b>{media_pedidos_dia:.1f}</b></p><p class="secondary-metric">Horário Pico: <b>{horario_pico_str}</b></p><p class="secondary-metric">Média Pico: <b>{formatar_moeda(valor_medio_pico)}</b></p></div>""")
            st.markdown(card_html, unsafe_allow_html=True)

def criar_grafico_tendencia(df):
    if df.empty or len(df.groupby('Data')) < 2: st.info("É necessário ter pelo menos dois dias de dados para mostrar uma tendência."); return
    st.markdown("##### <i class='bi bi-graph-up'></i> Tendência do Faturamento Diário", unsafe_allow_html=True)
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
    if df.empty: return
    st.markdown("##### <i class='bi bi-clock-history'></i> Performance por Hora", unsafe_allow_html=True)
    hourly_summary = df.groupby('Hora').agg(Num_Pedidos=('Pedido', 'count'), Faturamento_Total=('Total', 'sum')).reset_index()
    horas_template = pd.DataFrame({'Hora': range(24)})
    hourly_summary = pd.merge(horas_template, hourly_summary, on='Hora', how='left').fillna(0)
    hourly_summary['Ticket_Medio'] = hourly_summary.apply(lambda row: row['Faturamento_Total'] / row['Num_Pedidos'] if row['Num_Pedidos'] > 0 else 0, axis=1)
    chart = alt.Chart(hourly_summary).mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3).encode(x=alt.X('Hora:O', title='Hora do Dia', axis=alt.Axis(labelAngle=0)), y=alt.Y('Num_Pedidos:Q', title='Número de Pedidos'), color=alt.Color('Num_Pedidos:Q', scale=alt.Scale(scheme='blues'), legend=None), tooltip=[alt.Tooltip('Hora:N', title='Hora do Dia'), alt.Tooltip('Num_Pedidos:Q', title='Nº de Pedidos'), alt.Tooltip('Faturamento_Total:Q', title='Faturamento', format='$.2f'), alt.Tooltip('Ticket_Medio:Q', title='Ticket Médio', format='$.2f')]).configure_axis(grid=False).configure_view(strokeWidth=0)
    st.altair_chart(chart, use_container_width=True)

def criar_top_bairros_delivery(df_delivery_filtrado, df_delivery_total):
    if df_delivery_filtrado.empty: return
    st.markdown("#### <i class='bi bi-geo-alt-fill'></i> Top Bairros por Nº de Entregas", unsafe_allow_html=True)
    top_bairros = df_delivery_filtrado['Bairro'].value_counts().nlargest(3).index.tolist()
    if not top_bairros: st.info("Não há informações de bairro suficientes para gerar o top 3."); return
    cols = st.columns(3)
    for i, bairro_nome in enumerate(top_bairros):
        with cols[i]:
            df_bairro_filtrado = df_delivery_filtrado[df_delivery_filtrado['Bairro'] == bairro_nome]
            df_bairro_total = df_delivery_total[df_delivery_total['Bairro'] == bairro_nome]
            pedidos_bairro = len(df_bairro_filtrado)
            faturamento_bairro = df_bairro_filtrado['Total'].sum()
            ticket_medio_bairro = faturamento_bairro / pedidos_bairro if pedidos_bairro > 0 else 0
            total_taxa_entrega = df_bairro_filtrado['Entrega'].sum()
            media_diaria_filtro = pedidos_bairro / df_bairro_filtrado['Data'].nunique() if df_bairro_filtrado['Data'].nunique() > 0 else 0
            media_diaria_total = len(df_bairro_total) / df_bairro_total['Data'].nunique() if df_bairro_total['Data'].nunique() > 0 else 0
            delta_percent = ((media_diaria_filtro - media_diaria_total) / media_diaria_total) * 100 if media_diaria_total > 0 else 0
            delta_str = f"{delta_percent:+.2f}%"
            seta = "▲" if delta_percent >= 0 else "▼"; delta_class = "metric-delta-positive" if delta_percent >= 0 else "metric-delta-negative"
            delta_html = f"<div class='{delta_class}'>{seta} {delta_str.replace('-', '').replace('+', '')} vs Média</div>"
            card_html = textwrap.dedent(f"""<div class="metric-card" style="min-height: 230px;"><p class="metric-label" style="font-size: 1.1rem;">{i+1}º - {bairro_nome}</p><p class="metric-value">{pedidos_bairro}</p><p class="metric-label" style="font-size: 0.8rem; margin-bottom: 8px;">Nº de Pedidos</p>{delta_html}<hr class="metric-divider"><p class="secondary-metric">Faturamento: <b>{formatar_moeda(faturamento_bairro)}</b></p><p class="secondary-metric">Ticket Médio: <b>{formatar_moeda(ticket_medio_bairro)}</b></p><p class="secondary-metric">Total Taxas: <b>{formatar_moeda(total_taxa_entrega)}</b></p></div>""")
            st.markdown(card_html, unsafe_allow_html=True)

def criar_mapa_de_calor(df_delivery, df_cache_cep):
    st.markdown("#### <i class='bi bi-map-fill'></i> Concentração de Entregas", unsafe_allow_html=True)
    if df_cache_cep.empty: st.warning("O arquivo de cache de CEPs está vazio."); return
    df_delivery['CEP'] = df_delivery['CEP'].astype(str); df_cache_cep['cep'] = df_cache_cep['cep'].astype(str)
    df_mapa = pd.merge(df_delivery, df_cache_cep, left_on='CEP', right_on='cep', how='left').dropna(subset=['lat', 'lon'])
    if df_mapa.empty: st.warning("Nenhum CEP dos pedidos foi encontrado no cache."); return
    df_mapa_final = df_mapa[['lat', 'lon']].copy()
    df_mapa_final['lat'] = pd.to_numeric(df_mapa_final['lat']); df_mapa_final['lon'] = pd.to_numeric(df_mapa_final['lon'])
    st.map(df_mapa_final, zoom=11)

def criar_cards_cancelamento_resumo(df_cancelados, df_validos):
    num_cancelados = len(df_cancelados); num_validos = len(df_validos); total_pedidos = num_validos + num_cancelados
    valor_perdido = pd.to_numeric(df_cancelados['Total'], errors='coerce').sum()
    taxa_cancelamento = (num_cancelados / total_pedidos) * 100 if total_pedidos > 0 else 0
    col1, col2, col3 = st.columns(3)
    with col1: st.metric("Pedidos Cancelados", num_cancelados)
    with col2: st.metric("Valor Perdido", formatar_moeda(valor_perdido))
    with col3: st.metric("Taxa de Cancelamento", f"{taxa_cancelamento:.2f}%")

def criar_grafico_motivos_cancelamento(df_cancelados):
    if df_cancelados.empty or 'Motivo de cancelamento' not in df_cancelados.columns: return
    st.markdown("##### <i class='bi bi-question-circle'></i> Principais Motivos de Cancelamento", unsafe_allow_html=True)
    motivos = df_cancelados['Motivo de cancelamento'].value_counts().reset_index(); motivos.columns = ['Motivo', 'Contagem']
    chart = alt.Chart(motivos).mark_bar().encode(y=alt.Y('Motivo:N', title='Motivo', sort='-x'), x=alt.X('Contagem:Q', title='Número de Ocorrências'), tooltip=['Motivo', 'Contagem']).properties(height=300)
    st.altair_chart(chart, use_container_width=True)

def criar_grafico_cancelamentos_por_hora(df_cancelados):
    if df_cancelados.empty: return
    st.markdown("##### <i class='bi bi-clock'></i> Cancelamentos por Hora", unsafe_allow_html=True)
    df_cancelados['Hora'] = pd.to_numeric(df_cancelados['Hora'], errors='coerce')
    hourly_cancel = df_cancelados.groupby('Hora').size().reset_index(name='Contagem')
    horas_template = pd.DataFrame({'Hora': range(24)})
    hourly_cancel = pd.merge(horas_template, hourly_cancel, on='Hora', how='left').fillna(0)
    chart = alt.Chart(hourly_cancel).mark_bar(color="#CD5C5C").encode(x=alt.X('Hora:O', title='Hora do Dia'), y=alt.Y('Contagem:Q', title='Nº de Cancelamentos'), tooltip=['Hora', 'Contagem']).properties(height=300)
    st.altair_chart(chart, use_container_width=True)

def criar_donut_cancelamentos_por_canal(df_cancelados):
    if df_cancelados.empty or 'Canal de venda' not in df_cancelados.columns: return
    st.markdown("##### <i class='bi bi-pie-chart-fill'></i> Divisão por Canal de Venda", unsafe_allow_html=True)
    canal_counts = df_cancelados['Canal de venda'].value_counts().reset_index(); canal_counts.columns = ['Canal', 'Contagem']
    chart = alt.Chart(canal_counts).mark_arc(innerRadius=80).encode(theta=alt.Theta(field="Contagem", type="quantitative"), color=alt.Color(field="Canal", type="nominal", title="Canal"), tooltip=['Canal', 'Contagem']).properties(height=300)
    st.altair_chart(chart, use_container_width=True)
    
def criar_donut_e_resumo_canais(df):
    if df.empty:
        st.info("Não há dados para exibir na análise de canais."); return
    st.markdown("#### <i class='bi bi-pie-chart-fill'></i> Análise por Canal de Venda", unsafe_allow_html=True)
    col1, col2 = st.columns([1, 1])
    with col1:
        df_canal = df.groupby('Canal de venda').agg(Faturamento=('Total', 'sum'), Pedidos=('Pedido', 'count')).reset_index()
        df_canal['Ticket Medio'] = df_canal.apply(lambda r: r['Faturamento']/r['Pedidos'] if r['Pedidos']>0 else 0, axis=1)
        df_canal['Faturamento Formatado'] = df_canal['Faturamento'].apply(formatar_moeda)
        df_canal['Ticket Medio Formatado'] = df_canal['Ticket Medio'].apply(formatar_moeda)
        chart = alt.Chart(df_canal).mark_arc(innerRadius=80, outerRadius=120).encode(theta=alt.Theta(field="Faturamento", type="quantitative", stack=True), color=alt.Color(field="Canal de venda", type="nominal", legend=alt.Legend(title="Canais de Venda")), tooltip=[alt.Tooltip('Canal de venda', title='Canal'), alt.Tooltip('Faturamento Formatado', title='Faturamento'), alt.Tooltip('Pedidos', title='Nº de Pedidos'), alt.Tooltip('Ticket Medio Formatado', title='Ticket Médio')])
        st.altair_chart(chart, use_container_width=True)
    with col2:
        st.markdown("###### Insights sobre os Canais")
        ticket_medio_geral = df['Total'].sum() / len(df) if len(df) > 0 else 0
        df_canal_sorted = df_canal.sort_values(by="Faturamento", ascending=False)
        for index, row in df_canal_sorted.iterrows():
            canal = row['Canal de venda']; tm_canal = row['Ticket Medio']
            if tm_canal > ticket_medio_geral * 1.02: status_cor = "green"; status_texto = "Acima da média"
            elif tm_canal < ticket_medio_geral * 0.98: status_cor = "red"; status_texto = "Abaixo da média"
            else: status_cor = "orange"; status_texto = "Na média"
            insight_cols = st.columns([4, 2])
            with insight_cols[0]:
                st.markdown(f"• **{canal}:** Ticket médio de **{formatar_moeda(tm_canal)}**")
            with insight_cols[1]:
                st.badge(status_texto, color=status_cor)

def criar_distplot_e_analise(df):
    st.markdown("#### <i class='bi bi-distribute-vertical'></i> Análise de Distribuição de Valores", unsafe_allow_html=True)
    if df.empty:
        st.info("Não há dados para a análise de dispersão."); return
    col1, col2 = st.columns([1, 1])
    with col1:
        dias_semana_ordem = ['1. Segunda', '2. Terça', '3. Quarta', '4. Quinta', '5. Sexta', '6. Sábado', '7. Domingo']
        
        hist_data = []
        group_labels = []

        for dia in dias_semana_ordem:
            dados_dia = df[df['Dia da Semana'] == dia]['Total']
            # --- CORREÇÃO APLICADA AQUI ---
            # Apenas inclui o dia no gráfico se tiver 2 ou mais pedidos para evitar erro estatístico
            if len(dados_dia) > 1:
                hist_data.append(dados_dia.tolist())
                group_labels.append(dia.split('. ')[1])
        
        if not hist_data:
             st.info("Não há dados suficientes (pelo menos 2 pedidos em um mesmo dia da semana) para gerar o gráfico de distribuição.")
             return

        fig = ff.create_distplot(hist_data, group_labels, show_hist=False, show_rug=False)
        fig.update_layout(template="streamlit", showlegend=True, yaxis_title="Densidade", xaxis_title="Valor do Pedido (R$)", margin=dict(l=20, r=20, t=40, b=20), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', height=350)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("###### O que este gráfico significa?")
        st.markdown("Este gráfico mostra a **densidade** ou **concentração** dos valores dos pedidos para cada dia da semana. O pico da curva indica o valor de pedido mais comum. Curvas mais 'gordas' e espalhadas indicam uma grande variedade nos valores dos pedidos, enquanto curvas 'magras' e altas indicam que os valores dos pedidos são muito parecidos entre si.")
        Q1 = df['Total'].quantile(0.25); Q3 = df['Total'].quantile(0.75); IQR = Q3 - Q1
        limite_superior = Q3 + 1.5 * IQR
        outliers = df[df['Total'] > limite_superior].sort_values(by='Total', ascending=False)
        if not outliers.empty:
            st.markdown("###### Pedidos com Valores Atípicos (Acima)")
            for index, row in outliers.head(5).iterrows():
                data_formatada = pd.to_datetime(row['Data']).strftime('%d/%m')
                st.markdown(f" • **{formatar_moeda(row['Total'])}** em {data_formatada} ({row['Canal de venda']})")
        else:
            st.text("Nenhum pedido com valor muito acima da média foi detectado no período.")

def criar_tabela_top_clientes(df_delivery, nome_coluna_cliente='Consumidor'):
    st.markdown("#### <i class='bi bi-person-check-fill'></i> Top Clientes por Frequência", unsafe_allow_html=True)
    
    nome_coluna_cliente = 'Consumidor'

    if df_delivery.empty or nome_coluna_cliente not in df_delivery.columns or df_delivery[nome_coluna_cliente].isnull().all():
        st.info("Não há dados de clientes suficientes para gerar um ranking.")
        return

    df_delivery_com_cliente = df_delivery.dropna(subset=[nome_coluna_cliente])
    if df_delivery_com_cliente.empty:
        st.info("Não há nomes de clientes válidos para gerar um ranking.")
        return

    agg_dict = {
        'Quantidade_Pedidos': ('Pedido', 'count'),
        'Valor_Total': ('Total', 'sum')
    }
    if 'Bairro' in df_delivery_com_cliente.columns:
        agg_dict['Bairro'] = ('Bairro', lambda x: x.mode().iat[0] if not x.mode().empty else 'N/A')
    if 'Canal de venda' in df_delivery_com_cliente.columns:
        agg_dict['Canal_Preferido'] = ('Canal de venda', lambda x: x.mode().iat[0] if not x.mode().empty else 'N/A')

    df_clientes = df_delivery_com_cliente.groupby(nome_coluna_cliente).agg(**agg_dict).reset_index()
    
    df_clientes_sorted = df_clientes.sort_values(by='Quantidade_Pedidos', ascending=False).reset_index(drop=True)
    
    medalhas = {0: "1º 🥇", 1: "2º 🥈", 2: "3º 🥉"}
    df_clientes_sorted['Rank'] = [medalhas.get(i, f"{i+1}º") for i in df_clientes_sorted.index]
    
    df_clientes_sorted.rename(columns={nome_coluna_cliente: 'Cliente'}, inplace=True)
    
    colunas_para_exibir = ['Rank', 'Cliente']
    if 'Bairro' in df_clientes_sorted.columns: colunas_para_exibir.append('Bairro')
    if 'Canal_Preferido' in df_clientes_sorted.columns: colunas_para_exibir.append('Canal_Preferido')
    colunas_para_exibir.extend(['Quantidade_Pedidos', 'Valor_Total'])
    
    df_final = df_clientes_sorted[colunas_para_exibir]

    # No visualization.py, atualize a chamada st.dataframe():
    st.dataframe(
        df_final,
        column_config={
            "Rank": st.column_config.TextColumn("Posição"),
            "Cliente": st.column_config.TextColumn("Nome do Cliente"),
            "Bairro": st.column_config.TextColumn("Bairro"),
            "Canal_Preferido": st.column_config.TextColumn("Canal Preferido"),
            "Valor_Total": st.column_config.NumberColumn(
                "Valor Gasto (R$)",
                format="R$ %.2f",
                help="Valor total gasto pelo cliente"
            ),
            "Quantidade_Pedidos": st.column_config.NumberColumn(
                "Nº de Pedidos",
                help="Total de pedidos realizados"
            )
        },
        hide_index=True,
        use_container_width=True,
        height=min(400, 200 + len(df_final) * 35)  # Altura dinâmica
    )
