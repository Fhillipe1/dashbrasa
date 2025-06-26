# pages/2_🔥_Resultados São João.py (VERSÃO DE TESTE DE SINCRONIZAÇÃO)

import streamlit as st
from modules import sao_joao_handler

st.set_page_config(layout="wide", page_title="Teste Módulo São João")
st.title("Teste de Sincronização do Módulo `sao_joao_handler`")
st.info("Verificando se o novo módulo 'sao_joao_handler.py' foi atualizado no servidor.")
st.markdown("---")

st.header("Resultado do Diagnóstico:")

try:
    # 1. Verifica a versão do módulo
    st.markdown(f"**Versão do módulo detectada:** `{sao_joao_handler.__version__}`")
    
    if sao_joao_handler.__version__ == "SJ_1.0.0":
        st.success("✅ A versão do módulo `sao_joao_handler.py` está CORRETA!")
        
        # 2. Verifica se a função existe e a executa
        if hasattr(sao_joao_handler, 'check_sao_joao_module'):
            sao_joao_handler.check_sao_joao_module()
            st.balloons()
            st.markdown("---")
            st.write("Ótimo! Agora que a sincronização do novo módulo foi confirmada, me avise para eu poder te enviar o código final e completo da página de São João.")
        else:
            st.error("❌ ERRO: A função de diagnóstico NÃO foi encontrada, embora a versão esteja correta. Isso é muito estranho.")

    else:
        st.error(f"❌ VERSÃO ERRADA! A versão esperada era a 'SJ_1.0.0', mas a que está rodando é a '{sao_joao_handler.__version__}'.")

except AttributeError:
    st.error("❌ ERRO CRÍTICO: `AttributeError`!")
    st.warning("O arquivo `modules/sao_joao_handler.py` não existe ou está em uma versão antiga. Por favor, confirme que você salvou as alterações no GitHub e clique em 'Reboot app' no menu do seu app no Streamlit Cloud.")
except Exception as e:
    st.error(f"Ocorreu um erro inesperado: {e}")
