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

# Importa a função do outro módulo
from modules.sheets_handler import update_sheet_with_new_data

def run_extraction():
    """
    Função principal que executa toda a automação com Selenium para extrair o relatório da Saipos,
    e depois atualiza uma planilha Google com os novos dados.
    Configurada para rodar tanto localmente quanto no Streamlit Cloud.
    """
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
    chrome_options.binary_location = "/usr/bin/chromium"

    prefs = {'download.default_directory': DOWNLOAD_PATH}
    chrome_options.add_experimental_option('prefs', prefs)
    
    service = Service("/usr/bin/chromedriver")
    
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # Define um tempo máximo de espera para os elementos
    wait = WebDriverWait(driver, 30)

    try:
        print("Acessando a página de login...")
        driver.get(SAIPOS_LOGIN_URL)
        
        # Espera INTELIGENTE pelo campo de e-mail antes de prosseguir
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder='E-mail']")))
        
        print("Preenchendo informações de login...")
        driver.find_element(By.CSS_SELECTOR, "input[placeholder='E-mail']").send_keys(SAIPOS_USER)
        driver.find_element(By.CSS_SELECTOR, "input[placeholder='Senha']").send_keys(SAIPOS_PASSWORD)
        
        print("Clicando na seta para iniciar o login...")
        driver.find_element(By.CSS_SELECTOR, "i.zmdi-arrow-forward").click()
        
        try:
            # Tenta clicar no pop-up de "já logado", mas com um tempo curto
            popup_wait = WebDriverWait(driver, 5)
            botao_sim_confirm = popup_wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.confirm")))
            print("  -> Pop-up encontrado! Clicando em 'Sim'...")
            botao_sim_confirm.click()
        except TimeoutException:
            print("  -> Pop-up de 'desconectar' não apareceu. Ótimo, seguindo em frente!")
        
        # --- LÓGICA DE ESPERA ATUALIZADA ---
        print("Login finalizado. Aguardando o painel principal carregar...")
        # Substitui time.sleep(15) pela espera inteligente pelo botão de menu
        menu_trigger_button = wait.until(EC.element_to_be_clickable((By.ID, "menu-trigger")))
        print("Painel carregado. Clicando no menu principal...")
        menu_trigger_button.click()

        print("Clicando em 'Vendas por período'...")
        vendas_por_periodo_link = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[href="#/app/report/sales-by-period"]')))
        vendas_por_periodo_link.click()

        print("Localizando e preenchendo os campos de data...")
        # Espera pelo menos um dos campos de data aparecer
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[id='datePickerSaipos']")))
        campos_de_data = driver.find_elements(By.CSS_SELECTOR, "input[id='datePickerSaipos']")
        if len(campos_de_data) < 2: raise Exception("Não foi possível encontrar os dois campos de data.")
        
        # O resto da automação continua como antes...
        data_inicial_campo = campos_de_data[0]
        data_inicial_texto = "07/05/2025"
        data_inicial_campo.clear(); data_inicial_campo.send_keys(data_inicial_texto)
        data_final_campo = campos_de_data[1]
        data_final_texto = datetime.now().strftime("%d/%m/%Y")
        data_final_campo.clear(); data_final_campo.send_keys(data_final_texto)
        time.sleep(2)

        print("Clicando em 'Buscar' para filtrar os resultados...")
        driver.find_element(By.CSS_SELECTOR, 'button[ng-click*="vm.searchApiSales()"]').click()
        time.sleep(5) 

        limpar_pasta_relatorios(DOWNLOAD_PATH)
        
        print("Clicando no botão 'Exportar'...")
        driver.find_element(By.CSS_SELECTOR, 'button[ng-click="vm.exportReportPeriod();"]').click()
        print("Aguardando o download do arquivo...")
        time.sleep(60)
        print("Extração automatizada finalizada com sucesso!")

    except (TimeoutException, NoSuchElementException, Exception) as e:
        # Bloco de erro aprimorado para nos dar mais informações
        print("\n--- OCORREU UM ERRO DURANTE A AUTOMAÇÃO ---")
        print(f"Erro: {e}")
        # Salva o código-fonte da página atual para depuração
        page_source = driver.page_source
        print("\n--- CÓDIGO-FONTE DA PÁGINA NO MOMENTO DO ERRO ---")
        print(page_source[:2000] + "...") # Imprime os primeiros 2000 caracteres
        return None # Retorna None para indicar que a extração falhou
    finally:
        print("Fechando o navegador.")
        driver.quit()

    # --- Processamento do Relatório e Sincronização ---
    try:
        report_files = [f for f in os.listdir(DOWNLOAD_PATH) if f.endswith('.xlsx')]
        if not report_files:
            print("ERRO: Nenhum arquivo de relatório (.xlsx) foi encontrado na pasta de download.")
            return None

        nome_do_relatorio = report_files[0]
        full_path_to_file = os.path.join(DOWNLOAD_PATH, nome_do_relatorio)
        print(f"Encontrado o relatório: {full_path_to_file}")
        
        df = pd.read_excel(full_path_to_file)
        
        print("\n--- Iniciando sincronização com o Google Sheets ---")
        linhas_adicionadas = update_sheet_with_new_data(df)

        if linhas_adicionadas >= 0:
            print(f"Sincronização concluída. {linhas_adicionadas} novas linhas adicionadas.")
        else:
            print("Ocorreu um erro durante a sincronização com o Google Sheets.")
        
        return df

    except Exception as e:
        print(f"\nOcorreu um erro ao processar o arquivo baixado ou sincronizar: {e}")
        return None
