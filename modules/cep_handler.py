
# modules/cep_handler.py

import pandas as pd
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import streamlit as st
from tqdm import tqdm
import os

CACHE_FILE = 'data/cep_cache.csv'

def _fetch_coordinate(cep):
    """
    Busca a coordenada para um único CEP. Função privada.
    """
    try:
        url = f"https://brasilapi.com.br/api/cep/v2/{cep}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            coords = data.get('location', {}).get('coordinates', {})
            lat = coords.get('latitude')
            lon = coords.get('longitude')
            if lat and lon:
                return {'cep': cep, 'lat': lat, 'lon': lon}
    except requests.exceptions.RequestException:
        # Silencia erros de rede para não poluir o log, a menos que seja um erro inesperado
        pass
    return None

def atualizar_cache_cep(df_pedidos_validos):
    """
    Verifica os CEPs em um DataFrame de pedidos, busca os que não estão no cache
    e atualiza o arquivo de cache (cep_cache.csv).
    """
    st.write("Iniciando a atualização do cache de CEPs...")
    if 'CEP' not in df_pedidos_validos.columns:
        st.warning("Coluna 'CEP' não encontrada nos pedidos. Puxando a geolocalização.")
        return

    ceps_in_report = set(df_pedidos_validos['CEP'].dropna().unique())

    # Garante que o diretório 'data' exista
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)

    if os.path.exists(CACHE_FILE):
        df_cache = pd.read_csv(CACHE_FILE, dtype={'cep': str})
        ceps_in_cache = set(df_cache['cep'])
    else:
        df_cache = pd.DataFrame(columns=['cep', 'lat', 'lon'])
        ceps_in_cache = set()

    ceps_to_fetch = list(ceps_in_report - ceps_in_cache)

    if not ceps_to_fetch:
        st.write("Cache de CEPs já está 100% atualizado.")
        return

    st.write(f"Encontrados {len(ceps_to_fetch)} novos CEPs para geocodificar...")
    new_coords = []
    
    # Usando uma barra de progresso do Streamlit
    progress_bar = st.progress(0)
    total_ceps = len(ceps_to_fetch)

    with ThreadPoolExecutor(max_workers=15) as executor:
        futures = {executor.submit(_fetch_coordinate, cep): cep for cep in ceps_to_fetch}
        for i, future in enumerate(as_completed(futures)):
            result = future.result()
            if result:
                new_coords.append(result)
            progress_bar.progress((i + 1) / total_ceps)

    progress_bar.empty() # Limpa a barra de progresso

    if new_coords:
        df_new = pd.DataFrame(new_coords)
        df_cache_updated = pd.concat([df_cache, df_new], ignore_index=True)
        df_cache_updated.drop_duplicates(subset=['cep'], keep='last', inplace=True)
        df_cache_updated.to_csv(CACHE_FILE, index=False)
        st.write(f"Cache atualizado! {len(new_coords)} novas coordenadas foram salvas em '{CACHE_FILE}'.")
    else:
        st.write("Nenhuma nova coordenada foi encontrada para os CEPs buscados.")
