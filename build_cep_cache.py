import pandas as pd
import os
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

# Arquivos de entrada e saída
SAIPOS_REPORTS_DIR = 'relatorios_saipos'
CACHE_FILE = 'cep_cache.csv'

def get_latest_report_path():
    """Encontra o relatório .xlsx mais recente na pasta."""
    if not os.path.exists(SAIPOS_REPORTS_DIR):
        print(f"ERRO: A pasta '{SAIPOS_REPORTS_DIR}' não foi encontrada.")
        return None
    files = [os.path.join(SAIPOS_REPORTS_DIR, f) for f in os.listdir(SAIPOS_REPORTS_DIR) if f.endswith('.xlsx')]
    if not files:
        print(f"ERRO: Nenhum relatório .xlsx encontrado em '{SAIPOS_REPORTS_DIR}'.")
        return None
    return max(files, key=os.path.getctime)

def fetch_coordinate(cep):
    """
    Busca a coordenada para um único CEP de forma segura e retorna
    um dicionário com chaves em letras minúsculas ('cep', 'lat', 'lon').
    """
    try:
        url = f"https://brasilapi.com.br/api/cep/v2/{cep}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if 'location' in data and data.get('location') and 'coordinates' in data['location'] and data['location'].get('coordinates'):
                coordinates = data['location']['coordinates']
                lat = coordinates.get('latitude')
                lon = coordinates.get('longitude')
                
                if lat and lon:
                    # Padroniza as chaves para minúsculas
                    return {'cep': cep, 'lat': lat, 'lon': lon}
    except requests.exceptions.RequestException as e:
        if hasattr(e, 'response') and e.response is not None and e.response.status_code != 404:
            print(f"Erro de rede para o CEP {cep}: {e}")
            
    return None

def main():
    """Função principal para construir e atualizar o cache de CEPs de forma massiva e paralela."""
    print("Iniciando a construção do cache de CEPs...")
    
    report_path = get_latest_report_path()
    if not report_path: return
    
    print(f"Lendo relatório: {report_path}")
    df_report = pd.read_excel(report_path)
    
    if 'CEP' not in df_report.columns:
        print("ERRO: Coluna 'CEP' não encontrada no relatório.")
        return
    
    df_report['CEP'] = df_report['CEP'].astype(str).str.replace(r'\D', '', regex=True).str.zfill(8)
    ceps_in_report = set(df_report['CEP'].dropna().unique())

    if os.path.exists(CACHE_FILE):
        df_cache = pd.read_csv(CACHE_FILE, dtype=str)
        # LÓGICA DEFENSIVA: Renomeia 'CEP' para 'cep' se encontrar a versão em maiúsculas
        if 'CEP' in df_cache.columns:
            df_cache.rename(columns={'CEP': 'cep'}, inplace=True)
        ceps_in_cache = set(df_cache['cep'])
    else:
        df_cache = pd.DataFrame(columns=['cep', 'lat', 'lon'])
        ceps_in_cache = set()

    ceps_to_fetch = list(ceps_in_report - ceps_in_cache)

    if not ceps_to_fetch:
        print("Cache de CEPs já está atualizado.")
        return

    print(f"Encontrados {len(ceps_to_fetch)} novos CEPs para geocodificar...")
    new_coords = []
    
    with ThreadPoolExecutor(max_workers=15) as executor:
        with tqdm(total=len(ceps_to_fetch), desc="Geocodificando CEPs") as pbar:
            futures = {executor.submit(fetch_coordinate, cep): cep for cep in ceps_to_fetch}
            for future in as_completed(futures):
                result = future.result()
                if result:
                    new_coords.append(result)
                pbar.update(1)

    if new_coords:
        df_new = pd.DataFrame(new_coords)
        df_cache_updated = pd.concat([df_cache, df_new], ignore_index=True)
        df_cache_updated.drop_duplicates(subset=['cep'], keep='last', inplace=True)
        df_cache_updated.to_csv(CACHE_FILE, index=False)
        print(f"\nCache atualizado com sucesso! {len(new_coords)} novas coordenadas foram salvas em '{CACHE_FILE}'.")
    else:
        print("\nNenhuma nova coordenada foi encontrada.")

if __name__ == "__main__":
    main()