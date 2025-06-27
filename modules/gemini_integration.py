import google.generativeai as genai
import streamlit as st
import pandas as pd

class BusinessOracle:
    def __init__(self):
        self.model = None
        self._initialize_model()
        self.canais_mapeados = {
            "SITE DELIVERY (SAIPOS)": "BRENDI (Site Próprio)",
            "BRENDI": "BRENDI (Site Próprio)",
            "IFOOD": "iFood",
            "BALCÃO": "Balcão"
        }
    
    def _initialize_model(self):
        try:
            genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        except Exception as e:
            st.error("Erro na conexão com o sistema de análise")

    def responder(self, df, pergunta):
        try:
            # Pré-processamento dos dados
            df['Canal_Atualizado'] = df['Canal de venda'].replace(self.canais_mapeados)
            
            # Construa o contexto aqui...
            contexto = f"Dados atualizados até {df['Data'].max()}"
            
            response = self.model.generate_content(
                f"Contexto: {contexto}\nPergunta: {pergunta}"
            )
            return response.text
            
        except Exception as e:
            return f"Sistema temporariamente indisponível. Código: {hash(str(e))%1000:03d}"
