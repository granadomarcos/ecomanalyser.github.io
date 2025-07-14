import streamlit as st
import pandas as pd
import tempfile
import os
from script_ecommerce import analisar_dataframe

st.set_page_config(page_title="Detector de E-commerce", layout="centered")

st.title("🛒 Verificador de Sites com E-commerce")
st.markdown("Envie um arquivo CSV contendo uma coluna chamada `site` com os domínios para verificar se possuem e-commerce.")

uploaded_file = st.file_uploader("📤 Enviar arquivo CSV", type=["csv"])

if uploaded_file:
    df_input = pd.read_csv(uploaded_file)
    
    if 'site' not in df_input.columns:
        st.error("⚠️ O arquivo precisa conter uma coluna chamada `site`.")
    else:
        st.success("✅ Arquivo carregado com sucesso!")
        if st.button("🔍 Iniciar análise"):
            with st.spinner("Analisando os sites, isso pode levar alguns minutos..."):
                df_resultado = analisar_dataframe(df_input)

                tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
                df_resultado.to_csv(tmp_file.name, index=False)

                st.success("✅ Análise finalizada!")
                st.download_button(
                    label="📥 Baixar resultado CSV",
                    data=open(tmp_file.name, "rb").read(),
                    file_name="resultado_ecommerce.csv",
                    mime="text/csv"
                )
