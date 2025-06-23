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

# Tenta importar o handler do sheets, mas não quebra se não encontrar (para focar no erro do extrator)
try:
    from modules.sheets_handler import update_sheet_with_new_data
except ImportError:
    def update_sheet_with_new_data(df):
        print("AVISO: Módulo sheets_handler não encontrado. Apenas a extração será testada.")
        return 0

def run_extraction():
    """
    Função de extração com depuração máxima para o ambiente da nuvem.
    """
    # Carrega segredos DENTRO da função para garantir que st.secrets esteja disponível
    SAIPOS_LOGIN_URL = 'https://conta.saipos.com/#/access/login'
    SAIPOS_USER = st.secrets.get("SAIPOS_USER")
    SAIPOS_PASSWORD = st.secrets.get("SAIPOS_PASSWORD")
    DOWNLOAD_PATH = os.path.join(os.getcwd(), 'relatorios_saipos')

    def limpar_pasta_relatorios(caminho_da_pasta):
        if not os.path.exists(caminho_da_pasta):
            os.makedirs(caminho_da_pasta)
        for nome_arquivo in os.listdir(caminho_da_pasta):
            os.remove(os.path.join(caminho_da_pasta, nome_arquivo))
        print(f"Pasta de relatórios '{caminho_da_pasta}' está limpa.")

    print("Iniciando o robô extrator de relatórios (versão de depuração)...")
    
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
    driver = None # Inicializa o driver como None

    try:
        print("Inicializando o WebDriver do Chrome...")
        driver = webdriver.Chrome(service=service, options=chrome_options)
        wait = WebDriverWait(driver, 30)
        print("WebDriver inicializado com sucesso.")

        print("Acessando a página de login...")
        driver.get(SAIPOS_LOGIN_URL)
        
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder='E-mail']")))
        print(f"-> SUCESSO: Página de login carregada em: {driver.current_url}")
        
        driver.find_element(By.CSS_SELECTOR, "input[placeholder='E-mail']").send_keys(SAIPOS_USER)
        driver.find_element(By.CSS_SELECTOR, "input[placeholder='Senha']").send_keys(SAIPOS_PASSWORD)
        driver.find_element(By.CSS_SELECTOR, "i.zmdi-arrow-forward").click()
        print("-> SUCESSO: Formulário de login enviado.")
        
        try:
            popup_wait = WebDriverWait(driver, 7)
            botao_sim_confirm = popup_wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.confirm")))
            print("-> INFO: Pop-up de 'desconectar' encontrado. Clicando em 'Sim'...")
            botao_sim_confirm.click()
        except TimeoutException:
            print("-> INFO: Pop-up de 'desconectar' não apareceu.")
        
        time.sleep(5) 
        print(f"URL ATUAL APÓS LOGIN/POP-UP: {driver.current_url}")
        
        if "access/login" in driver.current_url:
            raise Exception("Falha no login. O robô permaneceu na página de login.")

        print("Aguardando o elemento principal do dashboard ('menu-trigger')...")
        menu_trigger_button = wait.until(EC.element_to_be_clickable((By.ID, "menu-trigger")))
        print("-> SUCESSO: Elemento 'menu-trigger' encontrado! Painel principal carregado.")
        menu_trigger_button.click()
        
        # O resto da automação continua...
        print("Continuando para a extração do relatório...")
        # (O código para navegar e baixar o relatório iria aqui)

    except Exception as e:
        print("\n\n*********************************************************")
        print("*********************************************************")
        print("*** INFORMAÇÕES DE DEPURAÇÃO CRÍTICA           ***")
        print("*********************************************************")
        print("*********************************************************")
        print(f"\nOcorreu um erro do tipo: {type(e).__name__}")
        
        if driver:
            url_no_erro = driver.current_url
            titulo_no_erro = driver.title
            print(f"\nURL NO MOMENTO DO ERRO: {url_no_erro}")
            print(f"TÍTULO DA PÁGINA: '{titulo_no_erro}'")
            print("\n--- INÍCIO DO CÓDIGO-FONTE DA PÁGINA ---")
            print(driver.page_source[:3000])
            print("--- FIM DO CÓDIGO-FONTE PARCIAL ---")
        else:
            print("O WebDriver não pôde ser inicializado.")

        print("\n*********************************************************")
        print(f"MENSAGEM DE ERRO COMPLETA: {e}")
        print("*********************************************************\n\n")

        if driver:
            driver.quit()
        return None
    
    # Se chegarmos aqui, significa que a automação principal funcionou.
    # O restante do código para processar o arquivo seria executado.
    # Esta parte foi simplificada para focarmos no erro de automação.
    print("Processo de automação concluído. Tentando finalizar...")
    if driver:
        driver.quit()
    
    # Simplesmente retornamos um DataFrame de exemplo para testar o fluxo
    return pd.DataFrame({'status': ['sucesso']})
