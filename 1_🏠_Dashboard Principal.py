from dotenv import load_dotenv

# Carrega variáveis de ambiente. Essencial para rodar localmente.
load_dotenv()

# --- Configuração da Página (com ícone e título restaurados) ---
st.set_page_config(page_title="Dashboard de Vendas La Brasa", page_icon="https://site.labrasaburger.com.br/wp-content/uploads/2021/09/logo.png", layout="wide")

# --- TODAS AS FUNÇÕES AUXILIARES ESTÃO AQUI ---

def format_currency(value):
    """Formata um número para o padrão de moeda brasileiro (R$ 1.234,56)."""
    if pd.isna(value):
        return "R$ 0,00"
    s = f'{value:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
    return f"R$ {s}"

@st.cache_data
def carregar_dados_das_planilhas():
    """Lê os dados das duas abas da Planilha Google de forma robusta."""
    print("Iniciando carregamento de dados da Planilha Google...")
    df_validos = pd.DataFrame()
    df_cancelados = pd.DataFrame()
    try:
        # Lógica de autenticação que funciona tanto na nuvem quanto localmente
        if "google_credentials" in st.secrets:
            creds_dict = st.secrets.get("google_credentials")
            gc = gspread.service_account_from_dict(creds_dict)
        else:
            credentials_file = "google_credentials.json"
            if not os.path.exists(credentials_file):
                st.error(f"ERRO: Arquivo de credenciais '{credentials_file}' não encontrado para execução local.")
                return None, None
            gc = gspread.service_account(filename=credentials_file)

        sheet_name = st.secrets.get("GOOGLE_SHEET_NAME") or os.getenv("GOOGLE_SHEET_NAME")
        if not sheet_name:
            st.error("ERRO: GOOGLE_SHEET_NAME não configurado.")
            return None, None
        
        spreadsheet = gc.open(sheet_name)
        worksheets = spreadsheet.worksheets()
        
        # Lê a primeira aba (índice 0) para Vendas Válidas
        if len(worksheets) > 0:
            worksheet_validos = worksheets[0]
            df_validos = get_as_dataframe(worksheet_validos, evaluate_formulas=False, header=0)
            df_validos.dropna(how='all', axis=1, inplace=True)
            print(f"Lidas {len(df_validos)} linhas da aba '{worksheet_validos.title}'.")
        
        # Lê a segunda aba (índice 1) para Vendas Canceladas, APENAS SE ELA EXISTIR
        if len(worksheets) > 1:
            worksheet_cancelados = worksheets[1]
            df_cancelados = get_as_dataframe(worksheet_cancelados, evaluate_formulas=False, header=0)
            df_cancelados.dropna(how='all', axis=1, inplace=True)
            print(f"Lidas {len(df_cancelados)} linhas da aba '{worksheet_cancelados.title}'.")
        
        return df_validos, df_cancelados
    except Exception as e:
        st.error(f"ERRO ao carregar dados da Planilha Google: {e}")
        return None, None

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

def tratar_dados_lidos(df_validos, df_cancelados):
    """Aplica as transformações de tipo de dado necessárias para os gráficos e análises."""
    if df_validos is None or df_validos.empty:
        return pd.DataFrame(), pd.DataFrame() if df_cancelados is None else df_cancelados

    df_validos = df_validos.copy()
    
    # Garante que os tipos de dados lidos da planilha estejam corretos para manipulação
    df_validos['Data da venda'] = pd.to_datetime(df_validos['Data da venda'], errors='coerce')
    df_validos.dropna(subset=['Data da venda'], inplace=True)
    
    # Cria/Recria colunas derivadas para garantir consistência
    df_validos['Data'] = pd.to_datetime(df_validos['Data da venda']).dt.date
    df_validos['Hora'] = df_validos['Data da venda'].dt.hour
    
    day_map = {0: '1. Segunda', 1: '2. Terça', 2: '3. Quarta', 3: '4. Quinta', 4: '5. Sexta', 5: '6. Sábado', 6: '7. Domingo'}
    df_validos['Dia da Semana'] = pd.to_datetime(df_validos['Data']).dt.weekday.map(day_map)

    # Converte colunas numéricas
    cols_numericas = ['Itens', 'Total taxa de serviço', 'Total', 'Entrega', 'Acréscimo', 'Desconto']
    for col in cols_numericas:
        if col in df_validos.columns:
            df_validos[col] = pd.to_numeric(df_validos[col], errors='coerce').fillna(0)
    
    return df_validos, df_cancelados

# --- Início da Interface do Streamlit ---
col_logo, col_title = st.columns([1, 25])
with col_logo:
    st.image("https://site.labrasaburger.com.br/wp-content/uploads/2021/09/logo.png", width=50)
with col_title:
    st.title("Dashboard de Vendas La Brasa")

with st.spinner("Conectando à Planilha Google e processando dados..."):
    df_validos_raw, df_cancelados = carregar_dados_das_planilhas()
    df_validos, df_cancelados = tratar_dados_pos_leitura(df_validos_raw, df_cancelados)
    df_ceps_database = carregar_base_ceps()

if df_validos is None or df_validos.empty:
    st.error("Não foi possível carregar ou tratar os dados da Planilha Google. Verifique os logs ou execute a atualização.")
    st.stop()

# --- Corpo Principal do Dashboard ---
st.success("Dados carregados e processados com sucesso!")
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
st.session_state['df_filtrado'] = df_filtrado

abas = st.tabs(["📊 Resumo Geral", "🛵 Delivery", "❌ Cancelamentos"])

with abas[0]:
    st.subheader("Resumo do Período Selecionado")
    col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
    faturamento_total = df_filtrado['Total'].sum()
    with col_kpi1: st.metric(label="📈 FATURAMENTO TOTAL", value=format_currency(faturamento_total))
    with col_kpi2: st.metric(label="Total de Pedidos Válidos", value=df_filtrado['Pedido'].nunique())
    with col_kpi3: 
        if df_filtrado['Pedido'].nunique() > 0:
            st.metric(label="Ticket Médio", value=format_currency(faturamento_total / df_filtrado['Pedido'].nunique()))

    st.divider()
    
    st.subheader("Evolução do Faturamento no Período")
    faturamento_diario = df_filtrado.groupby('Data')['Total'].sum().reset_index()
    if not faturamento_diario.empty and len(faturamento_diario) > 1:
        st.plotly_chart(create_gradient_line_chart(faturamento_diario), use_container_width=True)

with abas[1]:
    st.header("Análise de Delivery")
    df_delivery = df_filtrado[df_filtrado['Tipo de Canal'] == 'Delivery']
    if not df_delivery.empty:
        if df_ceps_database is not None:
            st.markdown("##### Mapa de Calor de Pedidos por CEP")
            pedidos_por_cep = df_delivery['CEP'].dropna().value_counts().reset_index()
            pedidos_por_cep.columns = ['CEP', 'num_pedidos']
            map_data = pd.merge(pedidos_por_cep, df_ceps_database, left_on='CEP', right_on='cep', how='inner')
            if not map_data.empty:
                map_data.rename(columns={'latitude': 'lat', 'longitude': 'lon'}, inplace=True, errors='ignore')
                st.pydeck_chart(pdk.Deck(
                    map_style=None,
                    initial_view_state=pdk.ViewState(latitude=map_data['lat'].mean(), longitude=map_data['lon'].mean(), zoom=11, pitch=0),
                    layers=[pdk.Layer('HeatmapLayer', data=map_data, get_position='[lon, lat]', get_weight='num_pedidos', opacity=0.8, radius_pixels=40)],
                    tooltip={"text": "CEP: {cep}\nPedidos: {num_pedidos}"}))
        else:
            st.warning("`cep_cache.csv` não encontrado. Rode `python build_cep_cache.py` para gerar o mapa.")
    else:
        st.info("Nenhum pedido de delivery no período selecionado.")

with abas[2]:
    st.subheader("Análise de Pedidos Cancelados")
    if df_cancelados is not None and not df_cancelados.empty:
        st.dataframe(df_cancelados)
    else:
        st.info("Nenhum pedido cancelado encontrado.")
