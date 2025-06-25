# modules/data_handler.py

import streamlit as st
import pandas as pd
import gspread
from gspread_dataframe import set_with_dataframe, get_as_dataframe
import numpy as np
import unicodedata
import pytz
from datetime import datetime

# --- FUNÇÕES DE AUTENTICAÇÃO E CONEXÃO ---

def _get_google_sheets_client():
    """Autentica no Google Sheets de forma segura."""
    try:
        return gspread.service_account_from_dict(st.secrets["google_credentials"])
    except Exception as e:
        st.error(f"Erro ao autenticar com o Google Sheets: {e}")
        return None

# --- FUNÇÕES DE DADOS ---

def tratar_dados_saipos(df_bruto):
    """Executa todas as transformações nos dados brutos do Excel."""
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
            temp_df['Data da venda'] = pd.to_datetime(temp_df['Data da venda'], dayfirst=True, errors='coerce')
            temp_df.dropna(subset=['Data da venda'], inplace=True)
            
            if temp_df['Data da venda'].dt.tz is None:
                temp_df['Data da venda'] = temp_df['Data da venda'].dt.tz_localize(fuso_horario)
            else:
                temp_df['Data da venda'] = temp_df['Data da venda'].dt.tz_convert(fuso_horario)

    if not df_validos.empty:
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
        if 'Canal de venda' in df_validos.columns:
            df_validos['Canal de venda Padronizado'] = df_validos['Canal de venda'].apply(_padronizar_texto)
            df_validos['Tipo de Canal'] = np.where(df_validos['Canal de venda Padronizado'].isin(delivery_channels), 'Delivery', 'Salão/Telefone')

    # --- CORREÇÃO FINAL PARA FORMATO DE TEXTO ---
    # Converte as colunas de data/hora para texto no formato desejado antes de salvar.
    for temp_df in [df_validos, df_cancelados]:
        if 'Data da venda' in temp_df.columns:
            # Converte 'Data da venda' para o formato 'AAAA-MM-DD HH:MM:SS'
            temp_df['Data da venda'] = pd.to_datetime(temp_df['Data da venda']).dt.strftime('%Y-%m-%d %H:%M:%S')
        if 'Data' in temp_df.columns:
             # Garante que a coluna 'Data' seja apenas 'AAAA-MM-DD'
            temp_df['Data'] = pd.to_datetime(temp_df['Data']).dt.strftime('%Y-%m-%d')

    return df_validos, df_cancelados

def _padronizar_texto(texto):
    if not isinstance(texto, str): return texto
    return ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn').strip().upper()


def carregar_dados_para_gsheets(df_novos_validos, df_novos_cancelados):
    """Carrega os DataFrames para o Google Sheets, verificando duplicatas e adicionando apenas novas linhas."""
    gc = _get_google_sheets_client()
    if gc is None: return
    sheet_name = st.secrets.get("GOOGLE_SHEET_NAME")
    if not sheet_name: return

    try:
        spreadsheet = gc.open(sheet_name)
        _atualizar_aba(spreadsheet, 0, "Página1", df_novos_validos)
        # Assumindo que a segunda aba se chamará "Cancelados"
        _atualizar_aba(spreadsheet, 1, "Cancelados", df_novos_cancelados)
    except Exception as e:
        st.error(f"Ocorreu um erro ao carregar os dados para o Google Sheets: {e}")

def _atualizar_aba(spreadsheet, index, nome_aba, df_novos):
    """Função auxiliar para atualizar uma aba específica."""
    try:
        worksheet = spreadsheet.worksheet(nome_aba)
    except gspread.WorksheetNotFound:
        st.write(f"Aba '{nome_aba}' não encontrada. Criando uma nova...")
        worksheet = spreadsheet.add_worksheet(title=nome_aba, rows="100", cols="40") # Aumentando o número de colunas por segurança
    
    st.write(f"Lendo dados existentes da aba '{nome_aba}'...")
    df_existente = get_as_dataframe(worksheet, evaluate_formulas=False)
    
    # Padroniza tudo para string para uma comparação segura de duplicatas
    if not df_existente.empty:
      df_existente = df_existente.astype(str)
    
    df_novos = df_novos.astype(str)

    if df_existente.empty:
        st.write(f"Aba '{nome_aba}' vazia. Adicionando {len(df_novos)} novas linhas.")
        set_with_dataframe(worksheet, df_novos, include_index=False, resize=True)
    else:
        # Garante que as colunas de ambos os dataframes sejam as mesmas para a concatenação
        colunas_comuns = list(set(df_existente.columns) & set(df_novos.columns))
        df_existente_comum = df_existente[colunas_comuns]
        df_novos_comum = df_novos[colunas_comuns]

        # Combina os dataframes e remove as duplicatas completas
        df_combinado = pd.concat([df_existente_comum, df_novos_comum]).drop_duplicates(keep=False)
        
        # As linhas restantes no df_combinado são as verdadeiramente novas
        if not df_combinado.empty:
            # Filtra o df_novos original para garantir que estamos adicionando apenas as linhas que devem ser novas
            df_para_adicionar = df_novos[df_novos['Pedido'].isin(df_combinado['Pedido'])]
            if not df_para_adicionar.empty:
                st.write(f"Adicionando {len(df_para_adicionar)} novas linhas à aba '{nome_aba}'...")
                worksheet.append_rows(df_para_adicionar.values.tolist(), value_input_option='USER_ENTERED')
            else:
                 st.write(f"Nenhuma linha nova para adicionar em '{nome_aba}'. A planilha já está atualizada.")
        else:
            st.write(f"Nenhuma linha nova para adicionar em '{nome_aba}'. A planilha já está atualizada.")
