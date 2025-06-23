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

from modules.sheets_handler import update_sheet_with_new_data

def run_extraction():
    SAIPOS_LOGIN_URL = 'https://conta.saipos.com/#/access/login'
    SAIPOS_USER = st.secrets.get("SAIPOS_USER")
    SAIPOS_PASSWORD = st.secrets.get("SAIPOS_PASSWORD")
    DOWNLOAD_PATH = os.path.join(os.getcwd(), 'relatorios_saipos')

    def limpar_pasta_relatorios(caminho_da_pasta):
        if os.path.exists(caminho_da_pasta):
            for nome_arquivo in os.listdir(caminho_da_pasta):
                os.remove(os.path.join(caminho_da_pasta, nome_arquivo))
        else:
            os.makedirs(DOWNLOAD_PATH)

    print("Iniciando o robô extrator de relatórios...")
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("window-size=1920,1080")
    chrome_options.binary_location = "/usr/bin/chromium"
    prefs = {'download.default_directory': DOWNLOAD_PATH}
    chrome_options.add_experimental_option('prefs', prefs)
    service = Service("/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=chrome_options)
    wait = WebDriverWait(driver, 30)

    try:
        print("Acessando a página de login...")
        driver.get(SAIPOS_LOGIN_URL)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder='E-mail']")))
        print(f"Página de login carregada em: {driver.current_url}")
        
        driver.find_element(By.CSS_SELECTOR, "input[placeholder='E-mail']").send_keys(SAIPOS_USER)
        driver.find_element(By.CSS_SELECTOR, "input[placeholder='Senha']").send_keys(SAIPOS_PASSWORD)
        driver.find_element(By.CSS_SELECTOR, "i.zmdi-arrow-forward").click()
        print("Tentativa de login enviada...")
        
        try:
            popup_wait = WebDriverWait(driver, 7)
            botao_sim_confirm = popup_wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.confirm")))
            print("  -> Pop-up de 'desconectar' encontrado! Clicando em 'Sim'...")
            botao_sim_confirm.click()
            print("  -> Pop-up 'Sim' clicado. Aguardando redirecionamento...")
        except TimeoutException:
            print("  -> Pop-up de 'desconectar' não apareceu. Continuando...")
        
        time.sleep(5) # Pausa crucial para o redirecionamento da página acontecer
        print(f"URL ATUAL APÓS LOGIN/POP-UP: {driver.current_url}")
        
        if "access/login" in driver.current_url:
            raise Exception("Falha no login. O robô permaneceu na página de login.")

        print("Aguardando o elemento principal do dashboard ('menu-trigger')...")
        menu_trigger_button = wait.until(EC.element_to_be_clickable((By.ID, "menu-trigger")))
        print("Elemento 'menu-trigger' encontrado! Painel principal carregado.")
        menu_trigger_button.click()
        
        # O resto da automação continua...

    except Exception as e:
        print("\n\n*********************************************************")
        print("*** INFORMAÇÕES DE DEPURAÇÃO CRÍTICA         ***")
        print("*********************************************************")
        print(f"Ocorreu um erro do tipo: {type(e).__name__}")
        
        url_no_erro = driver.current_url
        titulo_no_erro = driver.title
        
        print(f"\nURL ATUAL: {url_no_erro}")
        print(f"TÍTULO DA PÁGINA: '{titulo_no_erro}'")
        
        print("\n--- INÍCIO DO CÓDIGO-FONTE DA PÁGINA ---")
        print(driver.page_source[:3000]) # Imprime os primeiros 3000 caracteres
        print("--- FIM DO CÓDIGO-FONTE PARCIAL ---")
        print("*********************************************************\n")
        
        driver.quit()
        return None
    
    # Se tudo correu bem, o resto do código (que está fora do try/except principal de automação) seria executado
    # Esta parte foi omitida pois o erro ocorre antes dela.
    print("ERRO INESPERADO: O código de extração passou pelo Try/Except mas não deveria.")
    driver.quit()
    return None
