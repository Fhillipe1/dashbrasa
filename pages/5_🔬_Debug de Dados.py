import streamlit as st
import pandas as pd
import sys
import os

# Adiciona a pasta raiz ao path para encontrar o módulo de utilidades
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Importa a função do nosso novo módulo
from modules.utils import carregar_dados_brutos

st.set_page_config(page_title="Debug de Dados", page_icon="🔬")
st.title("🔬 Ferramenta de Diagnóstico de Dados")
st.warning("Esta página é para uso técnico. Use o botão abaixo para inspecionar o processamento de datas do seu relatório.")

if st.button("Iniciar Inspeção de Datas"):
    df = carregar_dados_brutos()

    if df is not None:
        st.divider()
        # ETAPA 1: INSPECIONAR OS DADOS BRUTOS
        st.subheader("ETAPA 1: Dados Brutos do Excel")
        st.write("Estes são os 10 primeiros valores da coluna 'Data da venda' exatamente como lidos do arquivo:")
        st.code(df['Data da venda'].head(10).to_list())

        st.divider()

        # ETAPA 2: CONVERTER E VERIFICAR O FUSO HORÁRIO
        st.subheader("ETAPA 2: Conversão para Datetime")
        # Converte para datetime, assumindo que o formato é Dia/Mês/Ano
        df['data_convertida'] = pd.to_datetime(df['Data da venda'], dayfirst=True, errors='coerce')
        
        st.write("Os mesmos valores após a conversão com `pd.to_datetime`:")
        st.code(df['data_convertida'].head(10).to_list())
        
        fuso_horario = df['data_convertida'].dt.tz
        st.write(f"**Fuso Horário (Timezone) detectado automaticamente:** `{fuso_horario}`")
        if fuso_horario is None:
            st.info("A data é 'ingênua' (naive), ou seja, não tem fuso horário definido. Isso é o normal e esperado.")
        else:
            st.error(f"ALERTA: A data foi interpretada como estando no fuso {fuso_horario}. Esta é provavelmente a causa do problema.")

        st.divider()

        # ETAPA 3: APLICAR FUSO HORÁRIO DE ARACAJU
        st.subheader("ETAPA 3: Aplicando o Fuso Horário de Aracaju")
        try:
            # 'tz_localize' atribui um fuso horário a datas ingênuas.
            if df['data_convertida'].dt.tz is None:
                df['data_localizada'] = df['data_convertida'].dt.tz_localize('America/Maceio', ambiguous='infer')
            else:
                # Se já tiver um fuso (ex: UTC), converte para o de Aracaju
                df['data_localizada'] = df['data_convertida'].dt.tz_convert('America/Maceio')
                
            st.write("Valores finais após forçar a interpretação no fuso horário de Aracaju (-03:00):")
            st.code(df['data_localizada'].head(10).to_list())
            st.success("Compare os horários da ETAPA 1 com esta lista final. Eles devem ser iguais.")

        except Exception as e:
            st.error(f"Ocorreu um erro ao tentar aplicar o fuso horário: {e}")

    else:
        st.error("Não foi possível carregar o relatório para a inspeção.")
