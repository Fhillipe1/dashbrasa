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
        """Configuração à prova de falhas"""
        try:
            genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        except Exception as e:
            st.error(f"Erro na inicialização: {str(e)}")

    def _generate_analysis(self, df: pd.DataFrame) -> dict:
        """Transforma os dados em formato JSON seguro"""
        if df.empty:
            return {}
        
        # Análise por dia da semana (evitando multi-index)
        dias_analise = df.groupby('Dia da Semana', as_index=False).agg(
            Faturamento_Total=('Total', 'sum'),
            Ticket_Medio=('Total', 'mean'),
            Total_Pedidos=('Pedido', 'count'),
            Horario_Pico=('Hora', lambda x: x.mode()[0])
        )
        
        # Convertemos para dicionário seguro
        analysis = {
            "periodo": {
                "inicio": str(df['Data'].min()),
                "fim": str(df['Data'].max())
            },
            "metricas_gerais": {
                "faturamento_total": float(df['Total'].sum()),
                "ticket_medio": float(df['Total'].mean()),
                "total_pedidos": int(len(df))
            },
            "analise_dias_semana": dias_analise.to_dict(orient='records'),
            "top_canais": df['Canal de venda'].value_counts().head(3).to_dict()
        }
        
        return analysis

    def ask_question(self, df: pd.DataFrame, question: str) -> str:
        """Processa perguntas com tratamento robusto de erros"""
        if self.model is None:
            return "🔴 Erro: Modelo não inicializado"
        
        try:
            analysis = self._generate_analysis(df)
            
            prompt = f"""
            CONTEXTO (ANÁLISE DE DADOS):
            {json.dumps(analysis, indent=2, ensure_ascii=False)}
            
            PERGUNTA:
            {question}
            
            INSTRUÇÕES:
            1. Responda em português (Brasil)
            2. Formate números como R$ 1.234,56
            3. Destaque os 3 principais insights
            4. Sugira ações práticas quando aplicável
            """
            
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.2,  # Menos criativo, mais factual
                    "max_output_tokens": 2000
                }
            )
            return response.text
            
        except Exception as e:
            st.error(f"Erro detalhado: {str(e)}")
            return "⚠️ Erro ao gerar resposta. Verifique os logs."
