# modules/data_handler.py

import streamlit as st
import pandas as pd
import gspread
from gspread_dataframe import set_with_dataframe
import numpy as np
import unicodedata
import pytz
from datetime import datetime
import os
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType

from selenium_stealth import stealth

# --- FUNÇÕES DE AUTENTICAÇÃO E CONEXÃO ---

def _get_google_sheets_client():
    try:
        credentials = st.secrets["google_credentials"]
        return gspread.service_account_from_dict(credentials)
    except Exception as e:
        st.error(f"Erro ao autenticar com o Google Sheets: {e}")
        return None

# --- FUNÇÕES DE EXTRAÇÃO (SELENIUM) ---

def extrair_dados_saipos(download_path):
    SAIPOS_LOGIN_URL = 'https://conta.saipos.com/#/access/login'
    SAIPOS_USER = st.secrets.get("SAIPOS_USER")
    SAIPOS_PASSWORD = st.secrets.get("SAIPOS_PASSWORD")

    if not os.path.exists(download_path):
        os.makedirs(download_path)
    else:
        for f in os.listdir(download_path):
            os.remove(os.path.join(download_path, f))

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("window-size=1920,1080")
    
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    prefs = {'download.default_directory': download_path}
    chrome_options.add_experimental_option('prefs', prefs)
    driver = None
    
    try:
        st.write("Configurando o ChromeDriver...")
        service = ChromeService(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())
        
        st.write("Inicializando o robô (WebDriver)...")
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        st.write("Aplicando camuflagem avançada (selenium-stealth)...")
        stealth(driver,
                languages=["pt-BR", "pt"],
                vendor="Google Inc.",
                platform="Win32",
                webgl_vendor="Intel Inc.",
                renderer="Intel Iris OpenGL Engine",
                fix_hairline=True,
                )
        
        wait = WebDriverWait(driver, 30) # Espera principal
        short_wait = WebDriverWait(driver, 5) # Espera curta para o pop-up

        st.write("Acessando a página de login da Saipos...")
        driver.get(SAIPOS_LOGIN_URL)

        st.write("Aguardando campo de e-mail ficar visível...")
        email_field = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "input[placeholder='E-mail']")))
        email_field.send_keys(SAIPOS_USER)

        password_field = driver.find_element(By.CSS_SELECTOR, "input[placeholder='Senha']")
        password_field.send_keys(SAIPOS_PASSWORD)

        st.write("Aguardando botão de login ficar clicável...")
        login_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[ng-click='lctrl.login()']")))
        login_button.click()
        
        try:
            st.write("Verificando se há pop-up de sessão ativa...")
            confirm_button = short_wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.confirm")))
            st.info("Pop-up de sessão ativa detectado! Clicando em 'Sim' para continuar...")
            confirm_button.click()
        except TimeoutException:
            st.write("Nenhum pop-up de sessão ativa encontrado. Continuando normalmente.")
        
        st.write("Aguardando painel principal carregar após login...")
        wait.until(EC.visibility_of_element_located((By.ID, "menu-trigger")))
        
        st.write("Navegando via menu: Clicando no menu principal...")
        menu_trigger = wait.until(EC.element_to_be_clickable((By.ID, "menu-trigger")))
        menu_trigger.click()
        
        st.write("Navegando via menu: Clicando em 'Vendas por período'...")
        vendas_link = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[href="#/app/report/sales-by-period"]')))
        vendas_link.click()

        st.write("Aguardando a página de relatórios carregar...")
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'button[ng-click*="vm.searchApiSales()"]')))

        st.write("Preenchendo o período do relatório...")
        campos_de_data = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "input[id='datePickerSaipos']")))
        data_inicial_campo, data_final_campo = campos_de_data[0], campos_de_data[1]
        
        data_inicial_texto = "01/01/2020"
        data_final_texto = datetime.now().strftime("%d/%m/%Y")
        
        data_inicial_campo.clear()
        data_inicial_campo.send_keys(data_inicial_texto)
        
        data_final_campo.clear()
        data_final_campo.send_keys(data_final_texto)
        time.sleep(1) # Pequena pausa para o site processar as datas

        st.write("Clicando em 'Buscar'...")
        buscar_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[ng-click*="vm.searchApiSales()"]')))
        buscar_button.click()
        
        st.write("Aguardando resultados da busca...")
        time.sleep(5) # Pausa para a tabela de resultados carregar

        st.write("Clicando em 'Exportar' para baixar o arquivo .xlsx...")
        exportar_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[ng-click="vm.exportReportPeriod();"]')))
        exportar_button.click()

        st.write("Aguardando o download finalizar (até 60s)...")
        time.sleep(60)
        
        report_files = [f for f in os.listdir(download_path) if f.endswith('.xlsx')]
        if not report_files:
            st.error("ERRO: Nenhum arquivo .xlsx foi baixado pelo robô.")
            return None
        
        full_path_to_file = os.path.join(download_path, report_files[0])
        st.write(f"Arquivo '{report_files[0]}' baixado com sucesso. Lendo os dados...")
        df_bruto = pd.read_excel(full_path_to_file, dtype={'CEP': str})
        return df_bruto

    except Exception as e:
        st.error(f"Ocorreu um erro durante a extração com o robô: {e}")
        if driver:
            st.error(f"URL atual: {driver.current_url}")
        return None
    finally:
        if driver:
            driver.quit()

# --- FUNÇÕES DE TRANSFORMAÇÃO DE DADOS ---

def _padronizar_texto(texto):
    if not isinstance(texto, str):
        return texto
    return ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn').strip().upper()

def tratar_dados_saipos(df_bruto):
    if df_bruto is None or df_bruto.empty:
        return pd.DataFrame(), pd.DataFrame()

    df = df_bruto.copy()
    
    df.columns = [str(col).strip() for col in df.columns]

    if 'Pedido' not in df.columns:
        st.error("ERRO CRÍTICO: Coluna 'Pedido' não encontrada no relatório.")
        return pd.DataFrame(), pd.DataFrame()

    df['Pedido'] = df['Pedido'].astype(str)
    if 'CEP' in df.columns:
        df['CEP'] = df['CEP'].astype(str).str.replace(r'\D', '', regex=True).str.zfill(8)
    if 'Bairro' in df.columns:
        df['Bairro'] = df['Bairro'].apply(_padronizar_texto)
    
    df_cancelados = df[df['Esta cancelado'] == 'S'].copy()
    df_validos = df[df['Esta cancelado'] == 'N'].copy()
    
    fuso_horario = pytz.timezone('America/Maceio')

    for temp_df in [df_validos, df_cancelados]:
        if not temp_df.empty and 'Data da venda' in temp_df.columns:
            temp_df['Data da venda'] = pd.to_datetime(temp_df['Data da venda'], errors='coerce')
            temp_df.dropna(subset=['Data da venda'], inplace=True)
            temp_df['Data da venda'] = temp_df['Data da venda'].dt.tz_localize('UTC').dt.tz_convert(fuso_horario)

    if not df_validos.empty:
        hoje = datetime.now(fuso_horario)
        df_validos = df_validos[df_validos['Data da venda'] <= hoje].copy()
        
        df_validos['Data'] = df_validos['Data da venda'].dt.date
        df_validos['Hora'] = df_validos['Data da venda'].dt.hour
        df_validos['Ano'] = df_validos['Data da venda'].dt.year
        df_validos['Mês'] = df_validos['Data da venda'].dt.month
        day_map = {0: '1. Segunda', 1: '2. Terça', 2: '3. Quarta', 3: '4. Quinta', 4: '5. Sexta', 5: '6. Sábado', 6: '7. Domingo'}
        df_validos['Dia da Semana'] = df_validos['Data da venda'].dt.weekday.map(day_map)
        
        cols_numericas = ['Itens', 'Total taxa de serviço', 'Total', 'Entrega', 'Acréscimo', 'Desconto']
        for col in cols_numericas:
            if col in df_validos.columns:
                df_validos[col] = pd.to_numeric(df_validos[col], errors='coerce').fillna(0)
        
        delivery_channels = ['IFOOD', 'SITE DELIVERY (SAIPOS)', 'BRENDI']
        if 'Canal de venda' in df.columns:
            df_validos['Canal de venda Padronizado'] = df_validos['Canal de venda'].apply(_padronizar_texto)
            df_validos['Tipo de Canal'] = np.where(df_validos['Canal de venda Padronizado'].isin(delivery_channels), 'Delivery', 'Salão/Telefone')

    for temp_df in [df_validos, df_cancelados]:
        for col in temp_df.select_dtypes(include=['datetime64[ns, UTC]', 'datetime64[ns, America/Maceio]', 'datetime64[ns]']).columns:
             temp_df[col] = temp_df[col].astype(str)
        if 'Data' in temp_df.columns:
             temp_df['Data'] = temp_df['Data'].astype(str)

    return df_validos, df_cancelados

# --- FUNÇÕES DE CARGA (GOOGLE SHEETS) ---

def carregar_dados_para_gsheets(df_validos, df_cancelados):
    gc = _get_google_sheets_client()
    if gc is None:
        st.error("Não foi possível conectar ao Google Sheets. Upload cancelado.")
        return

    sheet_name = st.secrets.get("GOOGLE_SHEET_NAME")
    if not sheet_name:
        st.error("Nome da planilha não encontrado nos segredos. Upload cancelado.")
        return

    try:
        spreadsheet = gc.open(sheet_name)
        
        st.write("Carregando dados válidos para a aba 'Página1'...")
        worksheet_validos = spreadsheet.get_worksheet(0)
        worksheet_validos.clear()
        set_with_dataframe(worksheet_validos, df_validos.fillna(""), include_index=False, resize=True)
        st.write(f"{len(df_validos)} linhas de vendas válidas salvas com sucesso!")

        try:
            worksheet_cancelados = spreadsheet.worksheet("Cancelados")
        except gspread.WorksheetNotFound:
            st.write("Aba 'Cancelados' não encontrada. Criando uma nova...")
            worksheet_cancelados = spreadsheet.add_worksheet(title="Cancelados", rows="100", cols="20")

        st.write("Carregando dados cancelados para a aba 'Cancelados'...")
        worksheet_cancelados.clear()
        set_with_dataframe(worksheet_cancelados, df_cancelados.fillna(""), include_index=False, resize=True)
        st.write(f"{len(df_cancelados)} linhas de vendas canceladas salvas com sucesso!")

    except Exception as e:
        st.error(f"Ocorreu um erro ao carregar os dados para o Google Sheets: {e}")
