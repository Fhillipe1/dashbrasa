import google.generativeai as genai
import streamlit as st
import pandas as pd
from datetime import datetime

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
        """Configuração robusta com tratamento de erros"""
        try:
            if "GEMINI_API_KEY" not in st.secrets:
                raise ValueError("Chave API não encontrada nos segredos")
                
            genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            st.success("✅ Sistema de análise inicializado!")
        except Exception as e:
            st.error(f"🔴 Erro na inicialização: {str(e)}")
            self.model = None

    def _preparar_contexto(self, df):
        """Prepara os dados de forma segura para análise"""
        try:
            if df is None or df.empty:
                return {"erro": "Nenhum dado carregado"}
            
            # Processamento seguro dos dados
            df['Canal_Atualizado'] = df['Canal de venda'].replace(self.canais_mapeados)
            
            return {
                "periodo": f"{df['Data'].min().strftime('%d/%m/%Y')} a {df['Data'].max().strftime('%d/%m/%Y')}",
                "total_pedidos": len(df),
                "faturamento_total": f"R$ {df['Total'].sum():,.2f}",
                "canais": df['Canal_Atualizado'].value_counts().to_dict()
            }
        except Exception as e:
            return {"erro": f"Erro no processamento: {str(e)}"}

    def responder(self, df, pergunta):
        """Método principal com tratamento completo de erros"""
        try:
            if self.model is None:
                raise RuntimeError("Sistema não inicializado")
            
            contexto = self._preparar_contexto(df)
            
            if "erro" in contexto:
                raise ValueError(contexto["erro"])
            
            prompt = f"""
            CONTEXTO LA BRASA BURGER:
            - Período: {contexto['periodo']}
            - Total Pedidos: {contexto['total_pedidos']}
            - Faturamento: {contexto['faturamento_total']}
            - Canais: {contexto['canais']}
            
            PERGUNTA: {pergunta}
            
            INSTRUÇÕES:
            1. Seja objetivo e analítico
            2. Use emojis relevantes
            3. Formate valores como R$ 1.234,56
            4. Destaque insights importantes
            """
            
            response = self.model.generate_content(prompt)
            return response.text
            
        except Exception as e:
            error_code = hash(str(e)) % 1000
            st.error(f"⚠️ Detalhes técnicos (código {error_code}): {str(e)}")
            return "Nosso sistema de análise está passando por instabilidades. Por favor, tente novamente mais tarde ou contate o suporte técnico."
