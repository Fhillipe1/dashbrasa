# 1_🏠_Dashboard Principal.py (VERSÃO DE TESTE DE SINCRONIZAÇÃO)

import streamlit as st
from modules import visualization

st.set_page_config(layout="wide")
st.title("Página de Teste de Sincronização")
st.info("O objetivo desta página é verificar se os arquivos do projeto estão sendo atualizados corretamente na nuvem.")
st.markdown("---")

st.header("Resultado do Diagnóstico:")

try:
    # 1. Verifica a versão do módulo
    st.write(f"Versão do módulo 'visualization' encontrada: **{visualization.__version__}**")
    if visualization.__version__ == "2.0.0":
        st.success("✅ A versão do módulo `visualization.py` está CORRETA!")
    else:
        st.error(f"❌ VERSÃO ERRADA! A versão deveria ser 2.0.0, mas a que está rodando é {visualization.__version__}. O arquivo não foi atualizado.")

    st.markdown("---")
    
    # 2. Verifica se a função existe antes de chamar
    if hasattr(visualization, 'funcao_de_diagnostico_1'):
        visualization.funcao_de_diagnostico_1()
    else:
        st.error("❌ ERRO CRÍTICO: Função `funcao_de_diagnostico_1` NÃO encontrada!")

except AttributeError:
    st.error("❌ ERRO CRÍTICO: AttributeError!")
    st.error("Isso confirma que a versão do arquivo `modules/visualization.py` que está rodando é muito antiga e nem possui a variável de versão.")
    st.warning("AÇÃO RECOMENDADA: Verifique se o arquivo foi salvo e 'commitado' corretamente no seu GitHub. Após confirmar, vá ao menu 'Manage app' no canto inferior direito do seu app e clique em 'Reboot app' para forçar uma reinstalação completa.")
except Exception as e:
    st.error(f"Ocorreu um erro inesperado: {e}")
