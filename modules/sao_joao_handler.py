# modules/sao_joao_handler.py

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import gspread
from gspread_dataframe import get_as_dataframe
from . import visualization as viz

# --- FUNÇÕES DE DADOS (AUTOCONTIDAS) ---
@st.cache_data(ttl=600)
def carregar_dados_sao_joao():
    """Carrega e prepara os dados das planilhas para a análise de São João."""
    try:
        gc = viz._get_google_sheets_client() # Reutiliza a função de conexão
        if gc is None: return pd.DataFrame(), pd.DataFrame()
        
        spreadsheet = gc.open(st.secrets["GOOGLE_SHEET_NAME"])
        
        # Carrega dados válidos
        worksheet_validos = spreadsheet.worksheet("Página1")
        df_validos = get_as_dataframe(worksheet_validos, evaluate_formulas=False).dropna(how='all')
        
        # Carrega dados cancelados
        worksheet_cancelados = spreadsheet.worksheet("Cancelados")
        df_cancelados = get_as_dataframe(worksheet_cancelados, evaluate_formulas=False).dropna(how='all')

        # Processa ambos os dataframes
        for df in [df_validos, df_cancelados]:
            if not df.empty:
                df['Data'] = pd.to_datetime(df['Data'], errors='coerce').dt.date
                df['Hora'] = pd.to_numeric(df['Hora'], errors='coerce')
                df['Total'] = pd.to_numeric(df['Total'], errors='coerce')
                df.dropna(subset=['Data', 'Hora', 'Total'], inplace=True)
        
        # Filtra pela madrugada
        df_validos_madrugada = df_validos[df_validos['Hora'].between(0, 4)].copy()
        df_cancelados_madrugada = df_cancelados[df_cancelados['Hora'].between(0, 4)].copy()
        
        return df_validos_madrugada, df_cancelados_madrugada

    except Exception as e:
        st.error(f"Ocorreu um erro ao carregar os dados da planilha: {e}")
        return pd.DataFrame(), pd.DataFrame()

# --- FUNÇÕES DE VISUALIZAÇÃO (ADAPTADAS) ---

def display_kpis(df):
    """Exibe os KPIs principais: Faturamento Total e Número de Pedidos."""
    st.markdown("##### <i class='bi bi-clipboard-data'></i> Resumo do Período", unsafe_allow_html=True)
    if df.empty:
        st.info("Nenhum dado encontrado para o período e filtros selecionados.")
        return
    total_revenue = df['Total'].sum()
    total_orders = len(df)
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Faturamento Total (Madrugada)", value=viz.formatar_moeda(total_revenue))
    with col2:
        st.metric(label="Total de Pedidos (Madrugada)", value=f"{total_orders}")

def display_daily_revenue_chart(df):
    """Exibe um gráfico de linha com a evolução do faturamento por dia."""
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
    fig.update_layout(template="plotly_dark", yaxis_title='Faturamento (R$)', margin=dict(t=30, b=30, l=40, r=40), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', height=300)
    st.plotly_chart(fig, use_container_width=True)

def display_hourly_performance_chart(df):
    """Exibe um gráfico de barras com Faturamento e hover com mais detalhes."""
    st.markdown("<h5 class='card-title'>Performance por Hora (Madrugada)</h5>", unsafe_allow_html=True)
    if df.empty: return
    hourly_summary = df.groupby('Hora').agg(Pedidos=('Pedido', 'count'), Faturamento=('Total', 'sum')).reset_index()
    horas_template = pd.DataFrame({'Hora': range(5)})
    hourly_summary = pd.merge(horas_template, hourly_summary, on='Hora', how='left').fillna(0)
    hourly_summary['Ticket_Medio'] = hourly_summary.apply(lambda r: r['Faturamento']/r['Pedidos'] if r['Pedidos']>0 else 0, axis=1)
    hourly_summary['Hora_Str'] = hourly_summary['Hora'].apply(lambda x: f'{x:02d}:00')
    
    # CORREÇÃO: Formata o texto para exibição completa
    hourly_summary['Faturamento_Texto'] = hourly_summary['Faturamento'].apply(viz.formatar_moeda)

    fig = go.Figure(data=go.Bar(
        x=hourly_summary['Hora_Str'], y=hourly_summary['Faturamento'],
        text=hourly_summary['Faturamento_Texto'], textposition='outside',
        marker=dict(color=hourly_summary['Faturamento'], colorscale='YlOrRd', line=dict(color='#0E1117', width=1)),
        customdata=hourly_summary[['Ticket_Medio', 'Pedidos']],
        hovertemplate="<b>Hora</b>: %{x}<br><b>Faturamento</b>: R$ %{y:,.2f}<br><b>Pedidos</b>: %{customdata[1]}<br><b>Ticket Médio</b>: R$ %{customdata[0]:,.2f}<extra></extra>"
    ))
    fig.update_layout(xaxis_title='Hora', yaxis_title='Faturamento (R$)', template="plotly_dark", margin=dict(t=30, b=30, l=40, r=40), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', height=300)
    st.plotly_chart(fig, use_container_width=True)

def display_cancelled_orders_table(df_cancelados):
    """Exibe uma tabela com os pedidos cancelados do período."""
    st.markdown("---")
    st.markdown("#### <i class='bi bi-x-circle-fill'></i> Pedidos Cancelados na Madrugada", unsafe_allow_html=True)
    if df_cancelados.empty:
        st.info("Nenhum pedido cancelado no período e filtros selecionados.")
        return
    
    # Seleciona, renomeia e formata as colunas para exibição
    df_display = df_cancelados.copy()
    colunas_para_exibir = {
        'Data': 'Data',
        'Hora': 'Hora',
        'Canal de venda': 'Canal',
        'Motivo de cancelamento': 'Motivo',
        'Total': 'Valor'
    }
    
    # Filtra apenas as colunas que existem no dataframe
    colunas_existentes = [col for col in colunas_para_exibir.keys() if col in df_display.columns]
    df_display = df_display[colunas_existentes]
    df_display = df_display.rename(columns=colunas_para_exibir)
    
    df_display['Valor'] = df_display['Valor'].apply(viz.formatar_moeda)
    df_display['Hora'] = df_display['Hora'].apply(lambda x: f"{int(x):02d}:00")

    st.dataframe(df_display, use_container_width=True, hide_index=True)
