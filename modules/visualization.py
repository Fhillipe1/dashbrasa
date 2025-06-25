# modules/visualization.py
import streamlit as st
import pandas as pd

def formatar_moeda(valor):
    """
    Formata um número para o padrão monetário brasileiro (R$).
    Exemplo: 1234.56 -> R$ 1.234,56
    """
    if valor is None:
        return "R$ 0,00"
    return f"R$ {valor:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")

def criar_cards_dias_semana(df):
    """
    Cria 7 cards, um para cada dia da semana, com métricas específicas.
    """
    st.subheader("Análise por Dia da Semana")

    dias_semana = ['1. Segunda', '2. Terça', '3. Quarta', '4. Quinta', '5. Sexta', '6. Sábado', '7. Domingo']
    
    # Usamos 7 colunas para os 7 dias
    cols = st.columns(7)

    for i, dia in enumerate(dias_semana):
        # Extrai o nome do dia sem o prefixo numérico (ex: "Segunda")
        nome_dia_semana = dia.split('. ')[1]
        
        with cols[i]:
            st.markdown(f"<h5 style='text-align: center;'>{nome_dia_semana}</h5>", unsafe_allow_html=True)
            
            # Filtra o dataframe para o dia da semana atual
            df_dia = df[df['Dia da Semana'] == dia]

            if df_dia.empty:
                st.text("Sem dados no período")
                continue

            # 1. Ticket Médio
            total_vendas_dia = df_dia['Total'].sum()
            num_pedidos_dia = len(df_dia)
            ticket_medio = total_vendas_dia / num_pedidos_dia if num_pedidos_dia > 0 else 0
            
            # 2. Horário de Pico
            horario_pico = df_dia['Hora'].mode()
            if not horario_pico.empty:
                horario_pico = int(horario_pico.iloc[0])
                horario_pico_str = f"{horario_pico}:00 - {horario_pico+1}:00"
                
                # 3. Valor Médio no Horário de Pico
                df_horario_pico = df_dia[df_dia['Hora'] == horario_pico]
                valor_medio_pico = df_horario_pico['Total'].mean() if not df_horario_pico.empty else 0
            else:
                horario_pico_str = "N/A"
                valor_medio_pico = 0

            # 4. Média de Pedidos por Dia
            num_dias_unicos = df_dia['Data'].nunique()
            media_pedidos_dia = num_pedidos_dia / num_dias_unicos if num_dias_unicos > 0 else 0

            # Exibição das métricas no card
            st.metric(label="Ticket Médio", value=formatar_moeda(ticket_medio))
            st.metric(label="Média de Pedidos", value=f"{media_pedidos_dia:.1f}")
            st.metric(label="Horário de Pico", value=horario_pico_str)
            st.metric(label="Média por Pedido (Pico)", value=formatar_moeda(valor_medio_pico))
