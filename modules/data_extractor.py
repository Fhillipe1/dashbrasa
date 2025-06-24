import streamlit as st
import time
import os
import pandas as pd
from datetime import datetime
import unicodedata
import pytz
import gspread
from gspread_dataframe import get_as_dataframe, set_with_dataframe
import numpy as np
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# --- Funções de Apoio (copiadas para autossuficiência) ---

def padronizar_texto(texto):
    if not isinstance(texto, str): return texto
    return ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn').strip().upper()

def tratar_dados_saipos(df_bruto):
    """Função que executa TODAS as transformações nos dados brutos do Excel."""
    if df_bruto is None or df_bruto.empty:
        return pd.DataFrame(), pd.DataFrame()

    df = df_bruto.copy()
    df.columns = [str(col) for col in df.columns]

    if 'Pedido' not in df.columns:
        print("ERRO CRÍTICO: Coluna 'Pedido' não encontrada.")
        return pd.DataFrame(), pd.DataFrame()
        
    df['Pedido'] = df['Pedido'].astype(str)
    if 'CEP' in df.columns: df['CEP'] = df['CEP'].astype(str).str.replace(r'\D', '', regex=True).str.zfill(8)
    if 'Bairro' in df.columns: df['Bairro'] = df['Bairro'].astype(str).apply(padronizar_texto)
    
    df_cancelados = df[df['Esta cancelado'] == 'S'].copy()
    df_validos = df[df['Esta cancelado'] == 'N'].copy()
    
    fuso_aracaju = pytz.timezone('America/Maceio')

    for temp_df in [df_validos, df_cancelados]:
        if not temp_df.empty and 'Data da venda' in temp_df.columns:
            temp_df['Data da venda'] = pd.to_datetime(temp_df['Data da venda'], dayfirst=True, errors='coerce')
            temp_df.dropna(subset=['Data da venda'], inplace=True)
            temp_df['Data da venda'] = temp_df['Data da venda'] - pd.Timedelta(hours=3)
            temp_df['Data da venda'] = temp_df['Data da venda'].dt.tz_localize(fuso_aracaju, ambiguous='infer')

    if not df_validos.empty:
        hoje = datetime.now(fuso_aracaju)
        df_validos = df_validos[df_validos['Data da venda'] <= hoje].copy()
        df_validos['Data'] = df_validos['Data da venda'].dt.date
        df_validos['Hora'] = df_validos['Data da venda'].dt.hour
        day_map = {0: '1. Segunda', 1: '2. Terça', 2: '3. Quarta', 3: '4. Quinta', 4: '5. Sexta', 5: '6. Sábado', 6: '7. Domingo'}
        df_validos['Dia da Semana'] = pd.to_datetime(df_validos['Data']).dt.weekday.map(day_map)
        
        cols_numericas = ['Itens', 'Total taxa de serviço', 'Total', 'Entrega', 'Acréscimo', 'Desconto']
        for col in cols_numericas:
            if col in df_validos.columns:
                df_validos[col] = pd.to_numeric(df_validos[col], errors='coerce').fillna(0)
        delivery_channels_padronizados = ['IFOOD', 'SITE DELIVERY (SAIPOS)', 'BRENDI']
        if 'Canal de venda' in df_validos.columns:
            df_validos['Tipo de Canal'] = df_validos['Canal de venda'].astype(str).apply(padronizar_texto).apply(lambda x: 'Delivery' if x in delivery_channels_padronizados else 'Salão/Telefone')
            
    for temp_df in [df_validos, df_cancelados]:
        if 'Data da venda' in temp_df.columns:
            temp_df['Data da venda'] = temp_df['Data da venda'].astype(str)
        if 'Data' in temp_df.columns:
            temp_df['Data'] = temp_df['Data'].astype(str)
            
    return df_validos, df_cancelados

def get_google_sheets_client():
    """Autentica no Google Sheets."""
    if "google_credentials" in st.secrets:
        return gspread.service_account_from_dict(st.secrets.get("google_credentials"))
    else:
        credentials_file = "google_credentials.json"
        if os.path.exists(credentials_file):
            return gspread.service_account(filename=credentials_file)
    st.error("ERRO: Credenciais do Google não encontradas.")
    return None

def update_target_sheet(spreadsheet, worksheet_index, df_new):
    """Atualiza uma aba específica com lógica de não duplicação."""
    worksheet = spreadsheet.get_worksheet(worksheet_index)
    worksheet_name = worksheet.title
    df_existing = get_as_dataframe(worksheet, evaluate_formulas=False, header=0)
    df_existing.dropna(how='all', axis=1, inplace=True)
    df_new_cleaned = df_new.astype(object).replace(np.nan, '')

    if df_existing.empty:
        print(f"Aba '{worksheet_name}' vazia. Escrevendo {len(df_new_cleaned)} linhas.")
        set_with_dataframe(worksheet, df_new_cleaned)
        return len(df_new_cleaned)
    else:
        df_existing['Pedido'] = df_existing['Pedido'].astype(str)
        df_new_cleaned['Pedido'] = df_new_cleaned['Pedido'].astype(str)
        
        linhas_novas = df_new_cleaned[~df_new_cleaned['Pedido'].isin(df_existing['Pedido'])]
        num_new_rows = len(linhas_novas)

        if num_new_rows > 0:
            print(f"Adicionando {num_new_rows} novas linhas à aba '{worksheet_name}'...")
            worksheet.append_rows(linhas_novas.values.tolist(), value_input_option='USER_ENTERED')
        else:
            print(f"Nenhuma linha nova para adicionar em '{worksheet_name}'.")
        return num_new_rows

def sync_with_google_sheets(df_validos, df_cancelados):
    """Orquestra a atualização das planilhas."""
    gc = get_google_sheets_client()
    if gc is None: return
    sheet_name = st.secrets.get("GOOGLE_SHEET_NAME") or os.getenv("GOOGLE_SHEET_NAME")
    if not sheet_name: return
    try:
        spreadsheet = gc.open(sheet_name)
        update_target_sheet(spreadsheet, 0, df_validos)
        update_target_sheet(spreadsheet, 1, df_cancelados)
    except Exception as e:
        print(f"ERRO ao sincronizar com o Google Sheets: {e}")

# --- FUNÇÃO PRINCIPAL DO ROBÔ ---

def run_extraction():
    """Função que executa o ciclo ETL: Extrai, Transforma e Carrega."""
    
    SAIPOS_LOGIN_URL = 'https://conta.saipos.com/#/access/login'
    REPORT_URL = 'https://conta.saipos.com/#/app/report/sales-by-period'
    SAIPOS_USER = st.secrets.get("SAIPOS_USER")
    SAIPOS_PASSWORD = st.secrets.get("SAIPOS_PASSWORD")
    DOWNLOAD_PATH = os.path.join(os.getcwd(), 'relatorios_saipos')

    def limpar_pasta_relatorios(caminho_da_pasta):
        if not os.path.exists(caminho_da_pasta): os.makedirs(caminho_da_pasta)
        else:
            for nome_arquivo in os.listdir(caminho_da_pasta): os.remove(os.path.join(caminho_da_pasta, nome_arquivo))
    
    chrome_options = Options(); service = Service("/usr/bin/chromedriver")
    chrome_options.add_argument("--headless"); chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage"); chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("window-size=1920,1080"); chrome_options.binary_location = "/usr/bin/chromium"
    prefs = {'download.default_directory': DOWNLOAD_PATH}; chrome_options.add_experimental_option('prefs', prefs)
    driver = None
    
    try:
        print("Inicializando WebDriver..."); driver = webdriver.Chrome(service=service, options=chrome_options)
        wait = WebDriverWait(driver, 40)
        
        # ETAPA 1: LOGIN
        print("Acessando a página de login..."); driver.get(SAIPOS_LOGIN_URL)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder='E-mail']")))
        driver.find_element(By.CSS_SELECTOR, "input[placeholder='E-mail']").send_keys(SAIPOS_USER)
        driver.find_element(By.CSS_SELECTOR, "input[placeholder='Senha']").send_keys(SAIPOS_PASSWORD)
        driver.find_element(By.CSS_SELECTOR, "i.zmdi-arrow-forward").click()
        print("Formulário de login enviado.")
        
        time.sleep(7) # Pausa generosa para o processamento do login

        # ETAPA 2: NAVEGAÇÃO DIRETA E ESPERA INTELIGENTE
        print(f"Login processado. Navegando diretamente para a página de relatórios: {REPORT_URL}")
        driver.get(REPORT_URL)

        print("Aguardando página de relatório carregar (esperando pelo botão 'Buscar')...")
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[ng-click*="vm.searchApiSales()"]')))
        print("Página de relatório carregada com sucesso.")

        # ETAPA 3: FILTRO E DOWNLOAD
        campos_de_data = driver.find_elements(By.CSS_SELECTOR, "input[id='datePickerSaipos']")
        if len(campos_de_data) < 2: raise Exception("Campos de data não encontrados.")
        
        data_inicial_campo = campos_de_data[0]; data_final_campo = campos_de_data[1]
        data_inicial_texto = "07/05/2025"; data_final_texto = datetime.now().strftime("%d/%m/%Y")
        data_inicial_campo.clear(); data_inicial_campo.send_keys(data_inicial_texto)
        data_final_campo.clear(); data_final_campo.send_keys(data_final_texto); time.sleep(2)
        
        print("Clicando em 'Buscar'...")
        driver.find_element(By.CSS_SELECTOR, 'button[ng-click*="vm.searchApiSales()"]').click(); time.sleep(5)
        
        print("Clicando em 'Exportar'...")
        limpar_pasta_relatorios(DOWNLOAD_PATH)
        driver.find_element(By.CSS_SELECTOR, 'button[ng-click="vm.exportReportPeriod();"]').click()
        
        print("Aguardando o download..."); time.sleep(90)
    finally:
        if driver: driver.quit()

    # Bloco de Transformação e Carga
    try:
        report_files = [f for f in os.listdir(DOWNLOAD_PATH) if f.endswith('.xlsx')]
        if not report_files:
            st.error("ERRO: Nenhum arquivo .xlsx foi baixado pelo robô."); return None
        
        full_path_to_file = os.path.join(DOWNLOAD_PATH, report_files[0])
        df_bruto = pd.read_excel(full_path_to_file, dtype={'Data da venda': str})
        
        print("Transformando dados (corrigindo horas, etc.)...")
        df_validos, df_cancelados = tratar_dados_saipos(df_bruto)
        
        print("Sincronizando com a Planilha Google...")
        sync_with_google_sheets(df_validos, df_cancelados)
        
        return df_validos
    except Exception as e:
        st.error(f"Ocorreu um erro ao processar o arquivo ou sincronizar: {e}"); return None
