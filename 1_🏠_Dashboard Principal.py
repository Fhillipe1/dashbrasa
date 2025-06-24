import streamlit as st
import pandas as pd
import os
import plotly.express as px
import plotly.graph_objects as go
import pydeck as pdk
from datetime import datetime
import unicodedata
import pytz
from modules.utils import tratar_dados, carregar_base_ceps, create_gradient_line_chart, format_currency, carregar_dados_brutos
# Configuração da página
st.set_page_config(page_title="Dashboard de Vendas La Brasa", page_icon="https://site.labrasaburger.com.br/wp-content/uploads/2021/09/logo.png", layout="wide")

# --- Funções Auxiliares ---

def format_currency(value):
    """Formata um número para o padrão de moeda brasileiro (R$ 1.234,56)."""
    if pd.isna(value):
        return "R$ 0,00"
    s = f'{value:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
    return f"R$ {s}"

@st.cache_data
def carregar_dados_brutos():
    """Carrega o relatório .xlsx mais recente da pasta 'relatorios_saipos'."""
    caminho_relatorios = 'relatorios_saipos'
    if not os.path.exists(caminho_relatorios): return None
    arquivos_xlsx = [f for f in os.listdir(caminho_relatorios) if f.endswith('.xlsx')]
    if not arquivos_xlsx: return None
    caminho_completo = os.path.join(caminho_relatorios, max(arquivos_xlsx, key=lambda f: os.path.getmtime(os.path.join(caminho_relatorios, f))))
    try:
        # Lê a coluna de data como texto para evitar conversão automática de fuso
        return pd.read_excel(caminho_completo, dtype={'Data da venda': str})
    except Exception as e:
        st.error(f"Erro ao ler o arquivo de relatório: {e}")
        return None

@st.cache_data
def carregar_base_ceps():
    """Carrega a base de dados de CEPs e garante que as coordenadas sejam numéricas."""
    cache_file = 'cep_cache.csv'
    if os.path.exists(cache_file):
        df = pd.read_csv(cache_file, dtype=str)
        if 'CEP' in df.columns and 'cep' not in df.columns: df.rename(columns={'CEP': 'cep'}, inplace=True)
        df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
        df['lon'] = pd.to_numeric(df['lon'], errors='coerce')
        df.dropna(subset=['lat', 'lon'], inplace=True)
        return df
    return None

def padronizar_texto(texto):
    """Função para limpar e padronizar texto."""
    if not isinstance(texto, str): return texto
    texto = ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
    return texto.strip().upper()

def tratar_dados(df):
    """Aplica todas as transformações, incluindo a correção de fuso horário e o formato de data correto."""
    if df is None: return None, None
    if 'Pedido' in df.columns: df['Pedido'] = df['Pedido'].astype(str)
    if 'CEP' in df.columns: df['CEP'] = df['CEP'].astype(str).str.replace(r'\D', '', regex=True).str.zfill(8)
    if 'Bairro' in df.columns: df['Bairro'] = df['Bairro'].astype(str).apply(padronizar_texto)
    
    df_cancelados = df[df['Esta cancelado'] == 'S'].copy()
    df_validos = df[df['Esta cancelado'] == 'N'].copy()
    
    # CORREÇÃO DEFINITIVA DE DATA/HORA
    df_validos['Data da venda'] = pd.to_datetime(df_validos['Data da venda'], dayfirst=True, errors='coerce')
    df_validos.dropna(subset=['Data da venda'], inplace=True)
    
    df_validos['Data da venda'] = df_validos['Data da venda'] - pd.Timedelta(hours=3)
    
    fuso_aracaju = pytz.timezone('America/Maceio')
    df_validos['Data da venda'] = df_validos['Data da venda'].dt.tz_localize(fuso_aracaju, ambiguous='infer')
    
    hoje = datetime.now(fuso_aracaju)
    df_validos = df_validos[df_validos['Data da venda'] <= hoje]

    df_validos['Data'] = df_validos['Data da venda'].dt.date
    df_validos['Hora'] = df_validos['Data da venda'].dt.hour
    
    day_map = {0: '1. Segunda', 1: '2. Terça', 2: '3. Quarta', 3: '4. Quinta', 4: '5. Sexta', 5: '6. Sábado', 6: '7. Domingo'}
    df_validos['Dia da Semana'] = df_validos['Data da venda'].dt.weekday.map(day_map)
    
    cols_numericas = ['Itens', 'Total taxa de serviço', 'Total', 'Entrega', 'Acréscimo', 'Desconto']
    for col in cols_numericas:
        if col in df_validos.columns:
            df_validos[col] = pd.to_numeric(df_validos[col], errors='coerce').fillna(0)

    delivery_channels_padronizados = ['IFOOD', 'SITE DELIVERY (SAIPOS)', 'BRENDI']
    df_validos['Tipo de Canal'] = df_validos['Canal de venda'].astype(str).apply(padronizar_texto).apply(
        lambda x: 'Delivery' if x in delivery_channels_padronizados else 'Salão/Telefone'
    )
    return df_validos, df_cancelados

def create_gradient_line_chart(df_data):
    """Cria um gráfico de linha com cores de gradiente para subidas e descidas."""
    df_data['Data'] = pd.to_datetime(df_data['Data'])
    df_data = df_data.sort_values(by='Data')
    df_data['diff'] = df_data['Total'].diff().fillna(0)
    fig = go.Figure()
    color_subida = '#5D9C59'; color_descida = '#DF2E38'
    for i in range(1, len(df_data)):
        fig.add_trace(go.Scatter(
            x=list(df_data['Data'])[i-1:i+1], y=list(df_data['Total'])[i-1:i+1], mode='lines',
            line=dict(color=color_subida if df_data['diff'].iloc[i] >= 0 else color_descida, width=3),
            hoverinfo='none'
        ))
    fig.add_trace(go.Scatter(
        x=df_data['Data'], y=df_data['Total'], mode='markers',
        marker=dict(color='#FFFFFF', size=5, line=dict(width=1, color='DarkSlateGrey')),
        hovertemplate='<b>Data:</b> %{x|%d/%m/%Y}<br><b>Faturamento:</b> R$ %{y:,.2f}<extra></extra>'
    ))
    fig.update_layout(showlegend=False, height=350, yaxis_title="Faturamento (R$)", xaxis_title=None, margin=dict(l=20, r=20, t=20, b=20))
    return fig

# --- Início da Interface do Streamlit ---
col_logo, col_title = st.columns([1, 25])
with col_logo:
    st.image("https://site.labrasaburger.com.br/wp-content/uploads/2021/09/logo.png", width=50)
with col_title:
    st.title("Dashboard de Vendas La Brasa")

with st.spinner("Conectando à Planilha Google e processando dados..."):
    # carregar_dados_brutos agora lê da Planilha Google, nossa fonte da verdade
    df_bruto_gdrive = carregar_dados_brutos() 
    # tratar_dados agora só ajusta os tipos para visualização
    df_validos, df_cancelados = tratar_dados(df_bruto_gdrive)
    df_ceps_database = carregar_base_ceps()

if df_validos is None:
    st.error("Não foi possível carregar os dados da Planilha Google. Tente rodar a atualização ou verifique as permissões da planilha.")
    st.stop()

if df_validos is not None:
    abas = st.tabs(["📊 Resumo Geral", "🛵 Delivery", "❌ Cancelamentos"])

    # Aba 1: Resumo Geral
    with abas[0]:
        with st.expander("📅 Aplicar Filtros no Dashboard", expanded=True):
            col_filtro1, col_filtro2 = st.columns(2)
            with col_filtro1:
                data_min = df_validos['Data'].min(); data_max = df_validos['Data'].max()
                data_selecionada = st.date_input("Selecione o Período", value=(data_min, data_max), min_value=data_min, max_value=data_max)
            with col_filtro2:
                opcoes_canal = sorted(list(df_validos['Canal de venda'].fillna('Não especificado').unique()))
                canal_selecionado = st.multiselect("Selecione o Canal de Venda", options=opcoes_canal, default=opcoes_canal)
        
        if len(data_selecionada) != 2: st.stop()
        
        start_date, end_date = data_selecionada
        df_filtrado = df_validos[(df_validos['Data'] >= start_date) & (df_validos['Data'] <= end_date) & (df_validos['Canal de venda'].fillna('Não especificado').isin(canal_selecionado))]
        
        st.subheader("Resumo do Período Selecionado")
        col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
        total_itens = df_filtrado['Itens'].sum(); total_taxas = df_filtrado['Total taxa de serviço'].sum(); faturamento_total = df_filtrado['Total'].sum()
        with col_kpi1: st.metric(label="💰 Total em Itens", value=format_currency(total_itens))
        with col_kpi2: st.metric(label="➕ Total em Taxas", value=format_currency(total_taxas))
        with col_kpi3: st.metric(label="📈 FATURAMENTO TOTAL", value=format_currency(faturamento_total))
        
        st.divider()

        st.subheader("Performance Semanal")
        st.caption("Cada card compara a média de pedidos/dia no período com a média histórica. A hora de pico refere-se ao total no período filtrado.")
        
        if not df_filtrado.empty:
            vendas_por_dia_geral = df_validos.groupby(['Data', 'Dia da Semana']).agg(Qtd_Pedidos=('Pedido', 'count')).reset_index()
            media_historica = vendas_por_dia_geral.groupby('Dia da Semana').agg(Pedidos_Medios=('Qtd_Pedidos', 'mean'))
            vendas_por_dia_filtrado = df_filtrado.groupby(['Data', 'Dia da Semana']).agg(Total_Vendas=('Total', 'sum'), Qtd_Pedidos=('Pedido', 'count')).reset_index()
            media_filtrada = vendas_por_dia_filtrado.groupby('Dia da Semana').agg(Valor_Medio=('Total_Vendas', 'mean'), Pedidos_Medios=('Qtd_Pedidos', 'mean'))
            pico_por_dia = df_filtrado.groupby(['Dia da Semana', 'Hora']).agg(Pedidos_Hora=('Pedido', 'count'), Vendas_Hora=('Total', 'sum')).reset_index()
            idx_pico = pico_por_dia.groupby('Dia da Semana')['Pedidos_Hora'].idxmax()
            horas_pico_info = pico_por_dia.loc[idx_pico]
            
            cols_dias = st.columns(7)
            dias_ordenados = sorted(df_validos['Dia da Semana'].unique())

            for i, dia_semana in enumerate(dias_ordenados):
                with cols_dias[i]:
                    with st.container(border=True, height=440):
                        st.markdown(f"**{dia_semana[3:]}**")
                        if dia_semana in media_filtrada.index:
                            row_filtrada = media_filtrada.loc[dia_semana]
                            row_historica = media_historica.loc[dia_semana]
                            delta = ((row_filtrada['Pedidos_Medios'] - row_historica['Pedidos_Medios']) / row_historica['Pedidos_Medios'] * 100) if row_historica['Pedidos_Medios'] > 0 else 0
                            st.metric(label="Média Pedidos/Dia", value=f"{row_filtrada['Pedidos_Medios']:.1f}", delta=f"{delta:.1f}%")
                            st.markdown(f"**Vendas Médias:** {format_currency(row_filtrada['Valor_Medio'])}")
                            st.divider()
                            hora_pico_dia = horas_pico_info[horas_pico_info['Dia da Semana'] == dia_semana]
                            if not hora_pico_dia.empty:
                                hora_pico = int(hora_pico_dia['Hora'].iloc[0])
                                pedidos_hora_pico = int(hora_pico_dia['Pedidos_Hora'].iloc[0])
                                vendas_hora_pico = hora_pico_dia['Vendas_Hora'].iloc[0]
                                st.markdown(f"**Pico às {hora_pico}:00**")
                                st.caption(f"{pedidos_hora_pico} pedidos (total)")
                                st.caption(f"{format_currency(vendas_hora_pico)} faturados")
                        else:
                            st.caption("Sem dados no período")
        
        st.divider()
        st.subheader("Evolução do Faturamento Diário")
        faturamento_diario = df_filtrado.groupby('Data')['Total'].sum().reset_index()
        if not faturamento_diario.empty and len(faturamento_diario) > 1:
            fig_faturamento = create_gradient_line_chart(faturamento_diario)
            st.plotly_chart(fig_faturamento, use_container_width=True)

    # Aba 2: Delivery
    with abas[1]:
        st.header("Análise de Delivery 🛵")
        df_delivery_filtrado = df_filtrado[df_filtrado['Tipo de Canal'] == 'Delivery']
        if not df_delivery_filtrado.empty:
            df_delivery_geral = df_validos[df_validos['Tipo de Canal'] == 'Delivery']
            
            st.subheader("Performance de Entregas por Bairro")
            st.caption("O percentual (Δ) compara a média de 'Pedidos por Dia' no período com a média histórica daquele bairro.")
            
            media_taxa_filtrada = df_delivery_filtrado['Entrega'].mean()
            media_taxa_geral = df_delivery_geral['Entrega'].mean()
            delta_taxa = ((media_taxa_filtrada - media_taxa_geral) / media_taxa_geral * 100) if media_taxa_geral > 0 else 0
            total_arrecadado_entregas = df_delivery_filtrado['Entrega'].sum()
            numero_de_entregas = len(df_delivery_filtrado)
            ticket_medio_delivery = df_delivery_filtrado['Total'].mean()
            top_bairros_filtrado = df_delivery_filtrado.groupby('Bairro').agg(Pedidos=('Pedido', 'count'), Valor_Total=('Total', 'sum'), Taxa_Entrega_Total=('Entrega', 'sum')).sort_values(by='Pedidos', ascending=False).head(3)
            pedidos_diarios_geral_bairro = df_delivery_geral.groupby(['Bairro', 'Data'])['Pedido'].count().reset_index()
            media_geral_bairro = pedidos_diarios_geral_bairro.groupby('Bairro')['Pedido'].mean()
            pedidos_diarios_filtrado_bairro = df_delivery_filtrado.groupby(['Bairro', 'Data'])['Pedido'].count().reset_index()
            media_filtrada_bairro = pedidos_diarios_filtrado_bairro.groupby('Bairro')['Pedido'].mean()
            
            col_d1, col_d2, col_d3, col_d4 = st.columns(4)
            with col_d1:
                with st.container(border=True, height=300):
                    st.markdown("##### Métricas Gerais Delivery")
                    st.markdown(f"**{numero_de_entregas}** entregas totais")
                    st.markdown(f"**{format_currency(total_arrecadado_entregas)}** em taxas")
                    st.markdown(f"**{format_currency(ticket_medio_delivery)}** de ticket médio")
                    st.metric(label="Taxa Média por Entrega", value=format_currency(media_taxa_filtrada), delta=f"{delta_taxa:.1f}%", delta_color="inverse")
            
            card_cols_bairro = [col_d2, col_d3, col_d4]
            for i, (bairro, row) in enumerate(top_bairros_filtrado.iterrows()):
                if i < len(card_cols_bairro):
                    with card_cols_bairro[i]:
                        with st.container(border=True, height=300):
                            st.markdown(f"##### Top {i+1}º: {bairro}")
                            st.markdown(f"**{row['Pedidos']}** pedidos")
                            st.markdown(f"**{format_currency(row['Valor_Total'])}** em vendas")
                            st.markdown(f"**{format_currency(row['Taxa_Entrega_Total'])}** em taxas")
                            media_geral = media_geral_bairro.get(bairro, 0)
                            media_filtrada = media_filtrada_bairro.get(bairro, 0)
                            delta_pedidos = ((media_filtrada - media_geral) / media_geral * 100) if media_geral > 0 else 0
                            st.metric(label="Pedidos/dia (vs. média)", value=f"{media_filtrada:.1f}", delta=f"{delta_pedidos:.1f}%")

            st.divider()
            st.markdown("##### Mapa de Calor de Pedidos por CEP")
            if df_ceps_database is not None:
                pedidos_por_cep = df_delivery_filtrado['CEP'].dropna().value_counts().reset_index()
                pedidos_por_cep.columns = ['CEP', 'num_pedidos']
                map_data = pd.merge(left=pedidos_por_cep, right=df_ceps_database, left_on='CEP', right_on='cep', how='inner')
                if not map_data.empty:
                    map_data.rename(columns={'latitude': 'lat', 'longitude': 'lon'}, inplace=True, errors='ignore')
                    st.pydeck_chart(pdk.Deck(map_style=None, initial_view_state=pdk.ViewState(latitude=map_data['lat'].mean(), longitude=map_data['lon'].mean(), zoom=11, pitch=0),
                        layers=[pdk.Layer('HeatmapLayer', data=map_data, get_position='[lon, lat]', get_weight='num_pedidos', opacity=0.8, radius_pixels=60)],
                        tooltip={"text": "CEP: {cep}\nPedidos: {num_pedidos}"}))
                else: st.warning("Nenhum CEP do relatório foi encontrado no seu cache. Rode `build_cep_cache.py` para atualizar.")
        else:
            st.info("Nenhum pedido de delivery encontrado no período selecionado.")

    # Aba 3: Cancelamentos
    with abas[2]:
        st.subheader("Análise de Pedidos Cancelados")
        if not df_cancelados.empty:
            total_cancelado = df_cancelados['Total'].sum()
            st.metric(label="Total de Pedidos Cancelados", value=len(df_cancelados))
            st.metric(label="Prejuízo com Cancelamentos", value=format_currency(total_cancelado))
            st.dataframe(df_cancelados)
        else:
            st.info("Nenhum pedido cancelado no período selecionado.")
else:
    st.warning("Não foi possível carregar os dados.")
