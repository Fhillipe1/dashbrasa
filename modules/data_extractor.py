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
from selenium.common.exceptions import TimeoutException

# Importa as funções dos outros módulos
from modules.sheets_handler import update_sheet_with_new_data

def run_extraction():
    """
    Função principal que executa toda a automação com Selenium para extrair o relatório da Saipos,
    e depois atualiza uma planilha Google com os novos dados.
    Configurada para rodar tanto localmente quanto no Streamlit Cloud.
    """
    # Lê os segredos de forma segura
    SAIPOS_LOGIN_URL = 'https://conta.saipos.com/#/access/login'
    SAIPOS_USER = st.secrets.get("SAIPOS_USER")
    SAIPOS_PASSWORD = st.secrets.get("SAIPOS_PASSWORD")
    DOWNLOAD_PATH = os.path.join(os.getcwd(), 'relatorios_saipos')

    def limpar_pasta_relatorios(caminho_da_pasta):
        print(f"Verificando e limpando a pasta: {caminho_da_pasta}")
        if os.path.exists(caminho_da_pasta):
            for nome_arquivo in os.listdir(caminho_da_pasta):
                caminho_completo = os.path.join(caminho_da_pasta, nome_arquivo)
                if os.path.isfile(caminho_completo):
                    print(f"  -> Deletando arquivo antigo: {nome_arquivo}")
                    os.remove(caminho_completo)
        else:
            print("Pasta de download não existe, será criada.")
            os.makedirs(DOWNLOAD_PATH)

    # --- Início da Automação ---
    print("Iniciando o robô extrator de relatórios...")
    
    # --- OPÇÕES DO CHROME PARA NUVEM ---
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    
    # Aponta para o local onde o Chromium foi instalado pelo packages.txt
    chrome_options.binary_location = "/usr/bin/chromium"

    prefs = {'download.default_directory': DOWNLOAD_PATH}
    chrome_options.add_experimental_option('prefs', prefs)
    
    # Aponta para o local onde o ChromeDriver foi instalado
    service = Service("/usr/bin/chromedriver")
    
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        # ETAPA 1 E 2: LOGIN, NAVEGAÇÃO E DOWNLOAD
        print("Acessando a página de login...")
        driver.get(SAIPOS_LOGIN_URL)
        time.sleep(5) # Dando um tempo extra para o JS carregar no ambiente da nuvem
        
        print("Preenchendo informações de login...")
        driver.find_element(By.CSS_SELECTOR, "input[placeholder='E-mail']").send_keys(SAIPOS_USER)
        driver.find_element(By.CSS_SELECTOR, "input[placeholder='Senha']").send_keys(SAIPOS_PASSWORD)
        
        print("Clicando na seta para iniciar o login...")
        driver.find_element(By.CSS_SELECTOR, "i.zmdi-arrow-forward").click()
        
        try:
            print("Verificando se o pop-up 'desconectar de outro local' apareceu...")
            wait = WebDriverWait(driver, 5)
            botao_sim_confirm = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.confirm")))
            print("  -> Pop-up encontrado! Clicando em 'Sim'...")
            botao_sim_confirm.click()
            time.sleep(2)
        except TimeoutException:
            print("  -> Pop-up não apareceu. Ótimo, seguindo em frente!")
        
        print("Login finalizado. Aguardando carregamento do painel...")
        time.sleep(15)

        print("Clicando no menu principal (menu-trigger)...")
        driver.find_element(By.ID, "menu-trigger").click()
        time.sleep(3)
        print("Clicando em 'Vendas por período'...")
        driver.find_element(By.CSS_SELECTOR, 'a[href="#/app/report/sales-by-period"]').click()
        time.sleep(10)
        print("Localizando e preenchendo os campos de data...")
        campos_de_data = driver.find_elements(By.CSS_SELECTOR, "input[id='datePickerSaipos']")
        if len(campos_de_data) < 2:
            print("ERRO: Não foi possível encontrar os dois campos de data na página.")
            driver.quit()
            return None

        data_inicial_campo = campos_de_data[0]
        data_inicial_texto = "07/05/2025"
        data_inicial_campo.clear(); data_inicial_campo.send_keys(data_inicial_texto)

        data_final_campo = campos_de_data[1]
        data_final_texto = datetime.now().strftime("%d/%m/%Y")
        data_final_campo.clear(); data_final_campo.send_keys(data_final_texto)
        time.sleep(3)

        print("Clicando em 'Buscar' para filtrar os resultados...")
        driver.find_element(By.CSS_SELECTOR, 'button[ng-click*="vm.searchApiSales()"]').click()
        time.sleep(5) 

        limpar_pasta_relatorios(DOWNLOAD_PATH)
        
        print("Clicando no botão 'Exportar'...")
        driver.find_element(By.CSS_SELECTOR, 'button[ng-click="vm.exportReportPeriod();"]').click()
        print("Aguardando o download do arquivo...")
        time.sleep(60)
        print("Extração automatizada finalizada com sucesso!")

    finally:
        print("Fechando o navegador.")
        driver.quit()

    # --- ETAPA 3: Processamento do Relatório e Sincronização com Google Sheets ---
    print("\n--- Processando o arquivo baixado ---")
    try:
        report_files = [f for f in os.listdir(DOWNLOAD_PATH) if f.endswith('.xlsx')]
        if not report_files:
            print("ERRO: Nenhum arquivo de relatório (.xlsx) foi encontrado na pasta de download.")
            return None

        nome_do_relatorio = report_files[0]
        full_path_to_file = os.path.join(DOWNLOAD_PATH, nome_do_relatorio)
        print(f"Encontrado o relatório: {full_path_to_file}")
        
        df = pd.read_excel(full_path_to_file)
        print("\nSucesso! DataFrame criado a partir do arquivo Excel.")
        
        print("\n--- Iniciando sincronização com o Google Sheets ---")
        linhas_adicionadas = update_sheet_with_new_data(df)

        if linhas_adicionadas > 0:
            print(f"Sincronização concluída. {linhas_adicionadas} novas linhas foram adicionadas à planilha.")
        elif linhas_adicionadas == 0:
            print("Sincronização concluída. A planilha já estava atualizada.")
        else:
            print("Ocorreu um erro durante a sincronização com o Google Sheets. Verifique as mensagens acima.")
        
        return df

    except Exception as e:
        print(f"\nOcorreu um erro ao tentar ler o arquivo baixado ou sincronizar: {e}")
        return None
