import streamlit as st
import time
import os
import pandas as pd
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from modules.utils import tratar_dados
from modules.sheets_handler import sync_with_google_sheets

try:
    from modules.sheets_handler import update_sheet_with_new_data
except ImportError:
    def update_sheet_with_new_data(df):
        print("AVISO: Módulo sheets_handler não encontrado.")
        return 0

def run_extraction():
    """Extrai, Transforma e Carrega os dados na Planilha Google."""
    SAIPOS_LOGIN_URL = 'https://conta.saipos.com/#/access/login'
    SAIPOS_USER = st.secrets.get("SAIPOS_USER")
    SAIPOS_PASSWORD = st.secrets.get("SAIPOS_PASSWORD")
    DOWNLOAD_PATH = os.path.join(os.getcwd(), 'relatorios_saipos')

    # ... (A função limpar_pasta_relatorios e a automação do Selenium continuam aqui, sem alterações)...
    
    # Código completo está abaixo
    def limpar_pasta_relatorios(caminho_da_pasta):
        if not os.path.exists(caminho_da_pasta): os.makedirs(caminho_da_pasta)
        else:
            for nome_arquivo in os.listdir(caminho_da_pasta): os.remove(os.path.join(caminho_da_pasta, nome_arquivo))
        print("-> Pasta de relatórios limpa.")
    
    print("Iniciando o robô extrator...")
    chrome_options = Options(); service = Service("/usr/bin/chromedriver") # Simplificado
    chrome_options.add_argument("--headless"); chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage"); chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("window-size=1920,1080"); chrome_options.binary_location = "/usr/bin/chromium"
    prefs = {'download.default_directory': DOWNLOAD_PATH}; chrome_options.add_experimental_option('prefs', prefs)
    driver = None
    try:
        driver = webdriver.Chrome(service=service, options=chrome_options); wait = WebDriverWait(driver, 40)
        print("Acessando a página de login..."); driver.get(SAIPOS_LOGIN_URL)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder='E-mail']"))); print("Página de login carregada.")
        driver.find_element(By.CSS_SELECTOR, "input[placeholder='E-mail']").send_keys(SAIPOS_USER)
        driver.find_element(By.CSS_SELECTOR, "input[placeholder='Senha']").send_keys(SAIPOS_PASSWORD)
        driver.find_element(By.CSS_SELECTOR, "i.zmdi-arrow-forward").click()
        print("Formulário de login enviado.")
        try:
            botao_sim_confirm = WebDriverWait(driver, 7).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.confirm")))
            print("-> INFO: Pop-up de 'desconectar' encontrado. Clicando..."); botao_sim_confirm.click(); time.sleep(3)
        except TimeoutException: print("-> INFO: Pop-up de 'desconectar' não apareceu.")
        print("Aguardando painel principal..."); menu_trigger_button = wait.until(EC.element_to_be_clickable((By.ID, "menu-trigger")))
        menu_trigger_button.click(); print("Clicando em 'Vendas por período'...")
        vendas_por_periodo_link = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[href="#/app/report/sales-by-period"]')))
        vendas_por_periodo_link.click(); print("Preenchendo datas...")
        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "input[id='datePickerSaipos']")))
        campos_de_data = driver.find_elements(By.CSS_SELECTOR, "input[id='datePickerSaipos']")
        if len(campos_de_data) < 2: raise Exception("Campos de data não encontrados.")
        data_inicial_campo = campos_de_data[0]; data_final_campo = campos_de_data[1]
        data_inicial_texto = "07/05/2025"; data_final_texto = datetime.now().strftime("%d/%m/%Y")
        data_inicial_campo.clear(); data_inicial_campo.send_keys(data_inicial_texto)
        data_final_campo.clear(); data_final_campo.send_keys(data_final_texto); time.sleep(2)
        driver.find_element(By.CSS_SELECTOR, 'button[ng-click*="vm.searchApiSales()"]').click(); time.sleep(5)
        limpar_pasta_relatorios(DOWNLOAD_PATH)
        driver.find_element(By.CSS_SELECTOR, 'button[ng-click="vm.exportReportPeriod();"]').click()
        print("Aguardando o download..."); time.sleep(90)
    finally:
        if driver: driver.quit()

    print("\n--- Processamento e Carga ---")
    try:
        report_files = [f for f in os.listdir(DOWNLOAD_PATH) if f.endswith('.xlsx')]
        if not report_files:
            print("ERRO: Nenhum arquivo .xlsx foi baixado."); return None
        
        full_path_to_file = os.path.join(DOWNLOAD_PATH, report_files[0])
        print(f"Lendo arquivo baixado: {full_path_to_file}")
        df_bruto = pd.read_excel(full_path_to_file, dtype={'Data da venda': str})
        
        print("Transformando dados (corrigindo horas, etc.)...")
        df_validos, df_cancelados = tratar_dados(df_bruto)
        
        print("Sincronizando com a Planilha Google...")
        sync_with_google_sheets(df_validos, df_cancelados)
        
        # Retorna o dataframe de vendas válidas para possível exibição no app de atualização
        return df_validos
    except Exception as e:
        print(f"Ocorreu um erro ao processar o arquivo ou sincronizar: {e}"); return None
