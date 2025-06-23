import pandas as pd
import requests
import os
import time
import streamlit as st

CACHE_FILE = 'cep_cache.csv'

def geocode_new_ceps(ceps_a_buscar):
    """Busca coordenadas para uma lista de CEPs e retorna um DataFrame com os resultados."""
    novas_coordenadas = []
    
    # Exibe uma barra de progresso no Streamlit
    progress_text = "Buscando coordenadas para novos CEPs. Aguarde..."
    my_bar = st.progress(0, text=progress_text)

    for i, cep in enumerate(ceps_a_buscar):
        try:
            url = f"https://brasilapi.com.br/api/cep/v2/{cep}"
            response = requests.get(url, timeout=5) # Timeout de 5 segundos
            if response.status_code == 200:
                data = response.json()
                if data.get('location'):
                    coordenadas = data['location']['coordinates']
                    novas_coordenadas.append({
                        'CEP': cep, 
                        'lat': data['location']['coordinates']['latitude'], 
                        'lon': data['location']['coordinates']['longitude']
                    })
            # Pausa educada para não sobrecarregar a API pública
            time.sleep(0.1) 
        except Exception as e:
            print(f"Falha ao buscar o CEP {cep}: {e}")
        
        # Atualiza a barra de progresso
        my_bar.progress((i + 1) / len(ceps_a_buscar), text=f"Buscando CEP: {cep} ({i+1}/{len(ceps_a_buscar)})")

    my_bar.empty() # Limpa a barra de progresso ao final
    return pd.DataFrame(novas_coordenadas)

def update_cep_cache(df_novas_coordenadas):
    """Adiciona novas coordenadas ao arquivo de cache."""
    if os.path.exists(CACHE_FILE):
        df_cache = pd.read_csv(CACHE_FILE, dtype={'CEP': str})
        df_cache_atualizado = pd.concat([df_cache, df_novas_coordenadas], ignore_index=True)
    else:
        df_cache_atualizado = df_novas_coordenadas
    
    df_cache_atualizado.to_csv(CACHE_FILE, index=False)
    print(f"{len(df_novas_coordenadas)} novas coordenadas salvas no cache.")