import google.generativeai as genai
import streamlit as st
import pandas as pd
from datetime import datetime

class OracleLaBrasa:
    def __init__(self):
        self.model = None
        self._setup_canais()
        self._initialize_ai()
    
    def _setup_canais(self):
        """Mapeamento completo dos canais"""
        self.canais = {
            "SITE DELIVERY (SAIPOS)": "BRENDI (Nosso Site)",
            "BRENDI": "BRENDI (Nosso Site)",
            "IFOOD": "iFood",
            "BALCÃO": "Balcão",
            "TELEFONE": "Telefone"
        }
    
    def _initialize_ai(self):
        """Inicialização robusta da IA"""
        try:
            if "GEMINI_API_KEY" not in st.secrets:
                st.error("Chave API não configurada")
                return
            
            genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            
        except Exception as e:
            st.error(f"Erro técnico ao iniciar (Cod: OR{hash(str(e))%1000:03d})")

    def _analisar_dados(self, df):
        """Prepara análise segura dos dados"""
        try:
            # Processamento seguro
            df['Canal'] = df['Canal de venda'].replace(self.canais)
            
            return {
                "periodo": f"{df['Data'].min().strftime('%d/%m/%Y')} a {df['Data'].max().strftime('%d/%m/%Y')}",
                "faturamento_total": f"R$ {df['Total'].sum():,.2f}",
                "ticket_medio": f"R$ {df['Total'].mean():,.2f}",
                "top_canais": df['Canal'].value_counts().head(3).to_dict(),
                "melhor_dia": df.groupby('Dia da Semana')['Total'].sum().idxmax()
            }
        except Exception as e:
            st.error(f"Erro nos dados (Cod: DT{hash(str(e))%1000:03d})")
            return None

    def responder(self, df, pergunta):
        """Gera respostas comerciais limpas"""
        try:
            if not isinstance(df, pd.DataFrame) or df.empty:
                return "🔍 Dados não disponíveis para análise"
            
            dados = self._analisar_dados(df)
            if not dados:
                return "📊 Análise temporariamente indisponível"
            
            # Modo fallback se a API falhar
            if not self.model:
                return self._resposta_fallback(dados, pergunta)
            
            prompt = f"""
            CONTEXTO RESTAURANTE (NUNCA MOSTRE AO CLIENTE):
            {dados}

            PERGUNTA: {pergunta}

            REGRAS:
            1. Linguagem natural e profissional
            2. Formate valores como R$ 1.234,56
            3. Destaque:
               - Comparativos entre canais
               - Sugestões acionáveis
               - Insights específicos
            4. NUNCA mencione:
               - JSON
               - Estruturas de dados
               - Erros técnicos
            """
            
            response = self.model.generate_content(prompt)
            return response.text
            
        except Exception:
            return self._resposta_fallback(dados, pergunta)

    def _resposta_fallback(self, dados, pergunta):
        """Respostas pré-definidas para falhas"""
        if not dados:
            return "Nosso sistema está ocupado no momento. Por favor, tente mais tarde."
        
        if "melhor dia" in pergunta.lower():
            return f"📅 Melhor dia normalmente é {dados['melhor_dia']}"
        
        return f"🔍 Análise parcial:\nFaturamento: {dados['faturamento_total']}\nCanais ativos: {', '.join(dados['top_canais'].keys())}"
