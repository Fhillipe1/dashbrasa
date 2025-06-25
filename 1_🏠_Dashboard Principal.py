# 1_🏠_Dashboard Principal.py (VERSÃO DE TESTE)

import streamlit as st
from modules import visualization

st.set_page_config(layout="wide")

st.title("Página de Teste de Sincronização de Arquivos")

st.info("O objetivo desta página é verificar se os arquivos estão sendo atualizados corretamente na nuvem.")

st.markdown("---")

st.header("Resultado do Teste:")

# Tentamos chamar a função de teste do nosso módulo
try:
    # Verificamos se a função de teste existe no módulo que foi carregado
    if hasattr(visualization, 'funcao_de_teste'):
        st.write("A função `funcao_de_teste` foi encontrada no módulo. Executando...")
        
        # Chamamos a função
        visualization.funcao_de_teste()

        st.markdown("---")
        st.write("Agora que confirmamos que a sincronização está funcionando, podemos prosseguir.")
        st.write("Por favor, me informe que você viu a mensagem de sucesso acima para eu poder te enviar o código final e completo do dashboard.")

    else:
        st.error("❌ ERRO CRÍTICO: A função `funcao_de_teste` NÃO foi encontrada.")
        st.error("Isso confirma que o arquivo `modules/visualization.py` que está no servidor é uma versão antiga.")
        st.warning("AÇÃO RECOMENDADA: Vá ao menu 'Manage app' no canto inferior direito e clique em 'Reboot app'. Se o erro persistir, verifique seu repositório GitHub.")

except Exception as e:
    st.error(f"Ocorreu um erro inesperado ao tentar importar ou executar o módulo: {e}")
