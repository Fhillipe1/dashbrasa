# modules/sao_joao_handler.py

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import gspread
from gspread_dataframe import get_as_dataframe
from datetime import time
from . import visualization as viz 

# --- FUNÇÃO DE CONEXÃO (AGORA AUTOCONTIDA NO MÓDULO) ---
def _get_google_sheets_client():
    """Autentica no Google Sheets de forma segura."""
    try:
        return gspread.service_account_from_dict(st.secrets["google_credentials"])
    except Exception as e:
        # Imprime o erro no console para depuração sem quebrar o app
        print(f"Erro ao autenticar com o Google Sheets: {e}")
        return None

# --- FUNÇÕES DE DADOS ---
@st.cache_data(ttl=600)
def carregar_dados_sao_joao():
    """Carrega e prepara os dados das planilhas para a análise de São João."""
    try:
        # CORREÇÃO: Chama a função local deste módulo
        gc = _get_google_sheets_client()
        if gc is None: 
            st.error("Falha na autenticação com o Google Sheets.")
            return pd.DataFrame(), pd.DataFrame()
        
        spreadsheet = gc.open(st.secrets["GOOGLE_SHEET_NAME"])
        
        df_validos = get_as_dataframe(spreadsheet.worksheet("Página1"), evaluate_formulas=False).dropna(how='all')
        df_cancelados = get_as_dataframe(spreadsheet.worksheet("Cancelados"), evaluate_formulas=False).dropna(how='all')

        for df in [df_validos, df_cancelados]:
            if not df.empty:
                df['Data'] = pd.to_datetime(df['Data'], errors='coerce').dt.date
                df['Hora'] = pd.to_numeric(df['Hora'], errors='coerce')
                df['Total'] = pd.to_numeric(df['Total'], errors='coerce')
                df.dropna(subset=['Data', 'Hora'], inplace=True) # Remove linhas onde a data/hora falhou
        
        df_validos_madrugada = df_validos[df_validos['Hora'].between(0, 4)].copy()
        df_cancelados_madrugada = df_cancelados[df_cancelados['Hora'].between(0, 4)].copy()
        
        return df_validos_madrugada, df_cancelados_madrugada

    except Exception as e:
        st.error(f"Ocorreu um erro ao carregar os dados da planilha: {e}")
        return pd.DataFrame(), pd.DataFrame()

# --- FUNÇÕES DE VISUALIZAÇÃO ---

def display_kpis(df):
    st.markdown("##### <i class='bi bi-clipboard-data'></i> Resumo do Período", unsafe_allow_html=True)
    if df.empty:
        total_revenue = 0.0; total_orders = 0
    else:
        total_revenue = df['Total'].sum()
        total_orders = len(df)
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Faturamento Total (Madrugada)", value=viz.formatar_moeda(total_revenue))
    with col2:
        st.metric(label="Total de Pedidos (Madrugada)", value=f"{total_orders}")

def display_daily_revenue_chart(df):
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
    fig.update_layout(template="plotly_dark", yaxis_title='Faturamento (R$)', xaxis_title=None, margin=dict(t=20, b=20, l=20, r=20), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', height=300)
    st.plotly_chart(fig, use_container_width=True)

def display_hourly_performance_chart(df):
    st.markdown("<h5 class='card-title'>Performance por Hora (Madrugada)</h5>", unsafe_allow_html=True)
    if df.empty: return
    hourly_summary = df.groupby('Hora').agg(Pedidos=('Pedido', 'count'), Faturamento=('Total', 'sum')).reset_index()
    horas_template = pd.DataFrame({'Hora': range(5)})
    hourly_summary = pd.merge(horas_template, hourly_summary, on='Hora', how='left').fillna(0)
    hourly_summary['Faturamento_Texto'] = hourly_summary['Faturamento'].apply(viz.formatar_moeda)
    hourly_summary['Hora_Str'] = hourly_summary['Hora'].apply(lambda x: f'{x:02d}:00')
    fig = go.Figure(data=go.Bar(
        x=hourly_summary['Hora_Str'], y=hourly_summary['Faturamento'],
        text=hourly_summary['Faturamento_Texto'], textposition='outside',
        marker=dict(color=hourly_summary['Faturamento'], colorscale='YlOrRd', line=dict(color='#0E1117', width=1)),
        hovertemplate="<b>Hora</b>: %{x}<br><b>Faturamento</b>: R$ %{y:,.2f}<br><b>Pedidos</b>: %{customdata[0]}<extra></extra>",
        customdata=hourly_summary[['Pedidos']]
    ))
    fig.update_layout(xaxis_title=None, yaxis_title='Faturamento (R$)', template="plotly_dark", margin=dict(t=20, b=20, l=20, r=20), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', height=300)
    st.plotly_chart(fig, use_container_width=True)

def display_cancelled_orders_table(df_cancelados):
    st.markdown("---")
    st.markdown("#### <i class='bi bi-x-circle-fill'></i> Pedidos Cancelados na Madrugada", unsafe_allow_html=True)
    if df_cancelados.empty:
        st.info("Nenhum pedido cancelado no período e filtros selecionados.")
        return
    df_display = df_cancelados.copy()
    colunas_para_exibir = {'Data': 'Data', 'Hora': 'Hora', 'Canal de venda': 'Canal', 'Motivo de cancelamento': 'Motivo', 'Total': 'Valor'}
    colunas_existentes = [col for col in colunas_para_exibir.keys() if col in df_display.columns]
    df_display = df_display[colunas_existentes].rename(columns=colunas_para_exibir)
    df_display['Valor'] = df_display['Valor'].apply(viz.formatar_moeda)
    df_display['Hora'] = df_display['Hora'].apply(lambda x: f"{int(x):02d}:00")
    st.dataframe(df_display, use_container_width=True, hide_index=True)
