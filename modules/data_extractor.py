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

try:
    from modules.sheets_handler import update_sheet_with_new_data
except ImportError:
    def update_sheet_with_new_data(df):
        print("AVISO: Módulo sheets_handler não encontrado.")
        return 0

def run_extraction():
    SAIPOS_LOGIN_URL = 'https://conta.saipos.com/#/access/login'
    SAIPOS_USER = st.secrets.get("SAIPOS_USER")
    SAIPOS_PASSWORD = st.secrets.get("SAIPOS_PASSWORD")
    DOWNLOAD_PATH = os.path.join(os.getcwd(), 'relatorios_saipos')

    def limpar_pasta_relatorios(caminho_da_pasta):
        if not os.path.exists(caminho_da_pasta):
            os.makedirs(caminho_da_pasta)
        else:
            for nome_arquivo in os.listdir(caminho_da_pasta):
                os.remove(os.path.join(caminho_da_pasta, nome_arquivo))
        print("-> Pasta de relatórios limpa.")

    print("Iniciando o robô extrator (v. otimizada)...")
    
    chrome_options = Options()
    # --- Flags de Otimização de Memória ---
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--disable-images")
    chrome_options.add_argument("--blink-settings=imagesEnabled=false")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.binary_location = "/usr/bin/chromium"

    prefs = {'download.default_directory': DOWNLOAD_PATH}
    chrome_options.add_experimental_option('prefs', prefs)
    
    service = Service("/usr/bin/chromedriver")
    driver = None

    try:
        print("[PASSO 1/8] Inicializando WebDriver...")
        driver = webdriver.Chrome(service=service, options=chrome_options)
        wait = WebDriverWait(driver, 40)
        print("[PASSO 2/8] Acessando a página de login...")
        driver.get(SAIPOS_LOGIN_URL)
        
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder='E-mail']")))
        print("[PASSO 3/8] Preenchendo formulário de login...")
        driver.find_element(By.CSS_SELECTOR, "input[placeholder='E-mail']").send_keys(SAIPOS_USER)
        driver.find_element(By.CSS_SELECTOR, "input[placeholder='Senha']").send_keys(SAIPOS_PASSWORD)
        driver.find_element(By.CSS_SELECTOR, "i.zmdi-arrow-forward").click()
        
        try:
            popup_wait = WebDriverWait(driver, 7)
            botao_sim_confirm = popup_wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.confirm")))
            print("-> INFO: Pop-up de 'desconectar' encontrado. Clicando...")
            botao_sim_confirm.click()
        except TimeoutException:
            print("-> INFO: Pop-up de 'desconectar' não apareceu.")
        
        print("[PASSO 4/8] Login enviado. Aguardando painel principal...")
        menu_trigger_button = wait.until(EC.element_to_be_clickable((By.ID, "menu-trigger")))
        menu_trigger_button.click()

        print("[PASSO 5/8] Navegando para o relatório 'Vendas por período'...")
        vendas_por_periodo_link = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[href="#/app/report/sales-by-period"]')))
        vendas_por_periodo_link.click()

        print("[PASSO 6/8] Preenchendo datas e buscando...")
        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "input[id='datePickerSaipos']")))
        campos_de_data = driver.find_elements(By.CSS_SELECTOR, "input[id='datePickerSaipos']")
        if len(campos_de_data) < 2: raise Exception("Campos de data não encontrados.")
        
        # ... (Preenchimento das datas)
        data_inicial_campo = campos_de_data[0]; data_final_campo = campos_de_data[1]
        data_inicial_texto = "07/05/2025"; data_final_texto = datetime.now().strftime("%d/%m/%Y")
        data_inicial_campo.clear(); data_inicial_campo.send_keys(data_inicial_texto)
        data_final_campo.clear(); data_final_campo.send_keys(data_final_texto)
        time.sleep(1)
        driver.find_element(By.CSS_SELECTOR, 'button[ng-click*="vm.searchApiSales()"]').click()
        time.sleep(5) 

        print("[PASSO 7/8] Exportando o relatório...")
        limpar_pasta_relatorios(DOWNLOAD_PATH)
        driver.find_element(By.CSS_SELECTOR, 'button[ng-click="vm.exportReportPeriod();"]').click()
        print("-> Aguardando o download (até 90s)...")
        time.sleep(90)
        print("-> Extração via Selenium concluída.")

    except Exception as e:
        print(f"\n--- ERRO NA AUTOMAÇÃO NO PASSO ANTERIOR A ESTA MENSAGEM ---")
        if driver:
            print(f"URL no momento do erro: {driver.current_url}")
            print(f"Título da página: '{driver.title}'")
        print(f"Erro: {e}")
        if driver: driver.quit()
        return None
    finally:
        if driver:
            print("[PASSO 8/8] Finalizando e fechando o navegador.")
            driver.quit()

    # --- Processamento do Arquivo e Sincronização ---
    try:
        report_files = [f for f in os.listdir(DOWNLOAD_PATH) if f.endswith('.xlsx')]
        if not report_files:
            print("ERRO: Nenhum arquivo .xlsx foi encontrado na pasta de download.")
            return None
        
        full_path_to_file = os.path.join(DOWNLOAD_PATH, report_files[0])
        df = pd.read_excel(full_path_to_file)
        
        print("-> Iniciando sincronização com o Google Sheets...")
        linhas_adicionadas = update_sheet_with_new_data(df)
        print(f"-> Sincronização finalizada. {linhas_adicionadas} linhas adicionadas.")
        return df
    except Exception as e:
        print(f"\nOcorreu um erro ao processar o arquivo baixado ou sincronizar: {e}")
        return None
