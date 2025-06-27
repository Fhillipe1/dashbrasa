# modules/gemini_integration.py
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
            st.error("Erro na conexão com a inteligência artificial")

    def _preparar_dados(self, df):
        """Prepara os dados para análise sem termos técnicos"""
        # Padroniza nomes dos canais
        df['Canal_Atualizado'] = df['Canal de venda'].replace(self.canais_mapeados)
        
        # Análise por dia da semana
        dias_analise = df.groupby('Dia da Semana', as_index=False).agg(
            Faturamento=('Total', 'sum'),
            Pedidos=('Pedido', 'count'),
            Horario_Pico=('Hora', lambda x: int(x.mode()[0]))
        
        return {
            "periodo": f"{df['Data'].min()} a {df['Data'].max()}",
            "faturamento_total": df['Total'].sum(),
            "analise_dias": dias_analise.to_dict('records'),
            "canais": df['Canal_Atualizado'].value_counts().to_dict()
        }

    def responder(self, df, pergunta, modo_tecnico=False):
        if not self.model:
            return "Sistema temporariamente indisponível"
        
        try:
            dados = self._preparar_dados(df)
            
            prompt = f"""
            CONTEXTO:
            - Você é o ORÁCULO DA LA BRASA BURGER
            - Canais atualizados: {self.canais_mapeados}
            - Dados reais (não mencione isso ao usuário):
              {dados}

            REGRAS:
            1. Linguagem natural e acessível
            2. Formate valores como R$ 1.234,56
            3. NUNCA mencione JSON, dados brutos ou estruturas técnicas
            4. Para perguntas técnicas use a palavra-chave [DEBUG]
            
            PERGUNTA: {pergunta}
            """
            
            if modo_tecnico:
                prompt += "\n\n[MODO TÉCNICO] Mostre detalhes da análise interna"
            
            response = self.model.generate_content(prompt)
            return response.text
            
        except Exception as e:
            return f"Erro no sistema. Código: ORACLE-{hash(str(e)) % 1000:03d}"
