import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup

st.set_page_config(page_title="Detector de E-commerce", layout="wide")
st.title("🛒 Detector de E-commerce")

KEYWORDS = [
    "comprar", "produto", "cart", "carrinho", "pagamento", "loja online",
    "meu carrinho", "finalizar compra", "icone de carrinho"
]

def check_ecommerce(url):
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return False, "erro: resposta inválida ({})".format(response.status_code), "confirmado"

        soup = BeautifulSoup(response.text, "html.parser")
        text = soup.get_text(separator=' ', strip=True).lower()
        keyword_hits = [kw for kw in KEYWORDS if kw.lower() in text]

        if keyword_hits:
            return True, ", ".join(keyword_hits), "possível"
        else:
            return False, "não encontrado", "confirmado"

    except Exception as e:
        return False, "erro interno ao processar site", "confirmado"

uploaded_file = st.file_uploader("📄 Faça upload do CSV com os sites", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    if 'site' not in df.columns:
        st.error("O CSV deve conter uma coluna chamada 'site'.")
    else:
        ecommerce_list = []
        keywords_list = []
        status_list = []

        with st.spinner("🔍 Verificando os sites..."):
            for site in df['site']:
                ecommerce, keywords, status = check_ecommerce(site)
                ecommerce_list.append(ecommerce)
                keywords_list.append(keywords)
                status_list.append(status)

        df['ecommerce_product'] = ecommerce_list
        df['ecommerce_keyword_match'] = keywords_list
        df['ecommerce_status'] = status_list

        st.success("✅ Verificação concluída!")
        st.dataframe(df)

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Baixar resultado CSV", csv, "resultado_ecommerce.csv", "text/csv")
