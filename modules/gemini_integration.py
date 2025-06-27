# modules/gemini_integration.py
import google.generativeai as genai
import streamlit as st
import pandas as pd
import json

class SmartOracle:
    def __init__(self):
        self.model = None
        self._initialize_model()
    
    def _initialize_model(self):
        """Configuração robusta do modelo Gemini"""
        try:
            genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        except Exception as e:
            st.error(f"Erro na inicialização: {str(e)}")
            self.model = None

    def _generate_analysis(self, df: pd.DataFrame) -> dict:
        """Pré-analisa os dados para enviar contexto estruturado"""
        if df.empty:
            return {}
        
        # Análise por dia da semana
        dias_analise = df.groupby('Dia da Semana').agg({
            'Total': ['sum', 'mean', 'count'],
            'Hora': lambda x: x.mode()[0]
        }).reset_index()
        
        # Convertemos para dicionário estruturado
        analysis = {
            "periodo": {
                "inicio": str(df['Data'].min()),
                "fim": str(df['Data'].max())
            },
            "metricas_gerais": {
                "faturamento_total": float(df['Total'].sum()),
                "ticket_medio": float(df['Total'].mean()),
                "total_pedidos": len(df)
            },
            "dias_semana": dias_analise.to_dict(orient='records'),
            "top_canais": df['Canal de venda'].value_counts().head(3).to_dict()
        }
        
        return analysis

    def ask_question(self, df: pd.DataFrame, question: str) -> str:
        """Processa perguntas com análise prévia dos dados"""
        if self.model is None:
            return "⚠️ Modelo não inicializado. Verifique sua chave API."
        
        try:
            # Pré-analisa os dados
            analysis = self._generate_analysis(df)
            
            # Contexto detalhado
            context = f"""
            🍔 ANÁLISE DOS DADOS (JSON):
            {json.dumps(analysis, indent=2, ensure_ascii=False)}
            
            INSTRUÇÕES:
            1. Use os dados PRÉ-ANALISADOS acima
            2. Responda em português claro
            3. Destaque números importantes
            4. Sugira ações quando relevante
            """
            
            # Chamada ao modelo
            response = self.model.generate_content(
                f"CONTEXTO: {context}\n\nPERGUNTA: {question}",
                generation_config={
                    "temperature": 0.3,
                    "max_output_tokens": 1500
                }
            )
            
            return response.text
            
        except Exception as e:
            return f"⚠️ Erro ao processar: {str(e)}"
