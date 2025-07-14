# script_ecommerce.py

def analisar_dataframe(df):
    import pandas as pd
    import requests
    from bs4 import BeautifulSoup
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from urllib.parse import urljoin, urlparse
    import concurrent.futures
    import time

        # Palavras
    palavras_fortes = ['adicionar ao carrinho', 'finalizar compra', 'carrinho', 'checkout', 'loja online', 'meu carrinho', 'comprar', 'cart']
    palavras_indicadoras_de_link = ['loja', 'shop', 'store', 'produtos', 'collection']
    palavras_chave_icone = ['cart', 'sacola', 'minicart', 'bag', 'checkout', 'order', 'shopping']

    # Selenium config
    def iniciar_selenium():
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        driver = webdriver.Chrome(options=options)
        return driver

    def contem_qualquer(texto, lista):
        return any(p in texto for p in lista)

    def extrair_textos(soup):
        title = soup.title.string if soup.title else ''
        metas = [meta.get('content', '') for meta in soup.find_all('meta') if meta.get('content')]
        links = [a.get_text(strip=True).lower() for a in soup.find_all('a')]
        botoes = [btn.get_text(strip=True).lower() for btn in soup.find_all('button')]
        return ' '.join([title] + metas + links + botoes).lower()

    def analisar_html(html):
        soup = BeautifulSoup(html, 'html.parser')
        texto = extrair_textos(soup)
        palavras_detectadas = [p for p in palavras_fortes if p in texto]

        for tag in soup.find_all(['div', 'a', 'i', 'span', 'svg']):
            id_attr = tag.get('id', '').lower()
            class_attr = ' '.join(tag.get('class', [])).lower()
            if contem_qualquer(id_attr, palavras_chave_icone) or contem_qualquer(class_attr, palavras_chave_icone):
                palavras_detectadas.append("icone de carrinho")
                break

        for img in soup.find_all('img'):
            alt = img.get('alt', '').lower()
            src = img.get('src', '').lower()
            if contem_qualquer(alt, palavras_chave_icone) or contem_qualquer(src, palavras_chave_icone):
                palavras_detectadas.append("icone de carrinho por imagem")
                break

        return palavras_detectadas, soup

    def analisar_pagina(url, headers, usar_selenium=False):
        try:
            if not usar_selenium:
                response = requests.get(url, headers=headers, timeout=10)
                if response.status_code == 403:
                    return 'bloqueado', None
                if response.status_code != 200:
                    return 'erro', None
                html = response.text
            else:
                driver = iniciar_selenium()
                driver.get(url)
                time.sleep(5)  # Aguarda carregamento
                html = driver.page_source
                driver.quit()

            palavras_detectadas, _ = analisar_html(html)
            if palavras_detectadas:
                return True, ', '.join(set(palavras_detectadas))
            return False, None

        except Exception as e:
            return 'erro', str(e)

    def detectar_ecommerce_para_linha(row):
        url = row['site']
        headers = {'User-Agent': 'Mozilla/5.0'}
        print(f"[🔍 Analisando] {url}")

        resultado, palavras = analisar_pagina(url, headers)
        if resultado == True:
            return row.name, True, palavras

        if resultado == 'bloqueado' or resultado == 'erro':
            print(f"[⚠️ Tentando Selenium] {url}")
            resultado_selenium, palavras_selenium = analisar_pagina(url, headers, usar_selenium=True)
            if resultado_selenium == True:
                return row.name, True, palavras_selenium
            else:
                return row.name, False, palavras_selenium or 'não encontrado'

        return row.name, False, 'não encontrado'

    # Classificação
    def classificar_com_base_em_palavras(palavras):
        if not palavras or pd.isna(palavras):
            return "nao identificado"
        elif "icone de carrinho" in palavras.lower():
            return "possivel"
        elif "bloqueado" in palavras.lower():
            return "js necessário"
        else:
            return "confirmado"

    df['ecommerce_product'] = None
    df['ecommerce_keyword_match'] = None

    N_THREADS = 3
    with concurrent.futures.ThreadPoolExecutor(max_workers=N_THREADS) as executor:
        resultados = list(executor.map(detectar_ecommerce_para_linha, [row for _, row in df.iterrows()]))

    for idx, ecommerce, palavras in resultados:
        df.at[idx, 'ecommerce_product'] = ecommerce
        df.at[idx, 'ecommerce_keyword_match'] = palavras

    df['ecommerce_status'] = df['ecommerce_keyword_match'].apply(classificar_com_base_em_palavras)

    # Segunda rodada para os não identificados ou que falharam
    pendentes_df = df[df['ecommerce_product'].isna() | (df['ecommerce_product'] == False)]

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        resultados_pendentes = list(executor.map(detectar_ecommerce_para_linha, [row for _, row in pendentes_df.iterrows()]))

    for idx, ecommerce, palavras in resultados_pendentes:
        df.at[idx, 'ecommerce_product'] = ecommerce
        df.at[idx, 'ecommerce_keyword_match'] = palavras

    df['ecommerce_status'] = df['ecommerce_keyword_match'].apply(classificar_com_base_em_palavras)

    return df
