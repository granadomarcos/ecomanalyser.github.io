def analisar_dataframe(df):
    import pandas as pd
    import requests
    from bs4 import BeautifulSoup
    from urllib.parse import urljoin
    import concurrent.futures
    import time

    # Palavras e padrões
    palavras_fortes = ['adicionar ao carrinho', 'finalizar compra', 'carrinho', 'checkout', 'loja online', 'meu carrinho', 'comprar', 'cart', 'pagamento', 'produto']
    palavras_chave_icone = ['cart', 'sacola', 'minicart', 'bag', 'checkout', 'order', 'shopping', 'icon-cart', 'fa-cart', 'basket']

    # Headers otimizados
    headers = {
        'User-Agent': (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp',
        'Referer': 'https://www.google.com'
    }

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

        return palavras_detectadas

    def analisar_pagina(url):
        try:
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 403:
                return 'bloqueado', None
            if response.status_code != 200:
                return 'erro', f"status {response.status_code}"

            palavras_detectadas = analisar_html(response.text)
            if palavras_detectadas:
                return True, ', '.join(set(palavras_detectadas))
            return False, 'não encontrado'
        except Exception as e:
            return 'erro', str(e)

    def classificar_com_base_em_palavras(palavras):
        if not palavras or pd.isna(palavras):
            return "nao identificado"
        elif "icone de carrinho" in palavras.lower():
            return "possivel"
        elif "bloqueado" in palavras.lower():
            return "js necessário"
        else:
            return "confirmado"

    def detectar_ecommerce_para_linha(row):
        url = row['site']
        print(f"[🔍 Analisando] {url}")
        resultado, palavras = analisar_pagina(url)
        if resultado == True:
            return row.name, True, palavras
        else:
            return row.name, False, palavras or 'não encontrado'

    df['ecommerce_product'] = None
    df['ecommerce_keyword_match'] = None

    N_THREADS = 4
    with concurrent.futures.ThreadPoolExecutor(max_workers=N_THREADS) as executor:
        resultados = list(executor.map(detectar_ecommerce_para_linha, [row for _, row in df.iterrows()]))

    for idx, ecommerce, palavras in resultados:
        df.at[idx, 'ecommerce_product'] = ecommerce
        df.at[idx, 'ecommerce_keyword_match'] = palavras

    df['ecommerce_status'] = df['ecommerce_keyword_match'].apply(classificar_com_base_em_palavras)

    return df
