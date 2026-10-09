
import re
import html
import requests
import streamlit as st

from html.parser import HTMLParser


# =========================================================
# CONFIGURAÇÕES
# =========================================================

URL_IBGE = "https://www.ibge.gov.br/explica/inflacao.php"
URL_SECUNDARIA = "https://brasilindicadores.com.br/ipca"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; IPCAApp/1.0)"
}

# TEXTO PADRÃO ORIGINAL.
# Somente o percentual do IPCA será substituído.
TEXTO_PADRAO = """**Aniversário de contrato**

**Reajuste de preço devido aniversário de contrato.**
**IPCA do mês em {ipca}**

**Preço Anterior: R$ 6,9588**
**Preço Negociado: R$ 7,2789&#x20;**

**CI -  ____________________ - Preço**"""


# =========================================================
# EXTRAÇÃO DO TEXTO HTML SEM BEAUTIFULSOUP
# =========================================================

class ExtratorHTML(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.partes = []

    def handle_data(self, data):
        if data.strip():
            self.partes.append(data.strip())

    def obter_texto(self):
        return " ".join(self.partes)


def obter_texto_site(url):
    resposta = requests.get(
        url,
        headers=HEADERS,
        timeout=30
    )
    resposta.raise_for_status()

    extrator = ExtratorHTML()
    extrator.feed(resposta.text)

    texto = extrator.obter_texto()
    texto = html.unescape(texto)
    texto = re.sub(r"\s+", " ", texto)

    return texto


# =========================================================
# IDENTIFICAÇÃO DO IPCA ACUMULADO EM 12 MESES
# =========================================================

def extrair_ipca(texto):
    """
    Procura o percentual próximo de uma referência ao
    IPCA acumulado em 12 meses.

    Não escolhe arbitrariamente entre vários percentuais.
    """

    texto = re.sub(r"\s+", " ", texto)

    referencias = [
        r"IPCA.{0,120}?acumulad[oa].{0,60}?12\s+meses",
        r"acumulad[oa].{0,60}?12\s+meses.{0,120}?IPCA",
        r"IPCA.{0,100}?12\s+meses",
        r"12\s+meses.{0,100}?IPCA",
    ]

    candidatos = set()

    for padrao in referencias:
        for referencia in re.finditer(
            padrao, texto, re.IGNORECASE
        ):
            inicio = max(0, referencia.start() - 150)
            fim = min(len(texto), referencia.end() + 200)

            trecho = texto[inicio:fim]

            valores = re.findall(
                r"(?<![\d,])(\d{1,2},\d{2})\s*%",
                trecho
            )

            for valor in valores:
                numero = float(valor.replace(",", "."))

                if 0 <= numero <= 100:
                    candidatos.add(valor + "%")

    if len(candidatos) == 1:
        return candidatos.pop()

    if not candidatos:
        raise ValueError(
            "Não foi possível localizar o IPCA acumulado "
            "em 12 meses. A estrutura do site pode ter mudado."
        )

    raise ValueError(
        "Foram encontrados vários percentuais possíveis. "
        "O índice precisa ser conferido manualmente."
    )


# =========================================================
# CONSULTA DAS FONTES
# =========================================================

def consultar_fonte(nome, url):
    try:
        texto = obter_texto_site(url)
        percentual = extrair_ipca(texto)

        return {
            "fonte": nome,
            "ipca": percentual,
            "erro": None
        }

    except requests.RequestException as erro:
        return {
            "fonte": nome,
            "ipca": None,
            "erro": f"Falha de conexão: {erro}"
        }

    except ValueError as erro:
        return {
            "fonte": nome,
            "ipca": None,
            "erro": str(erro)
        }


# =========================================================
# TEXTO FINAL
# =========================================================

def gerar_texto(ipca):
    # Substitui somente o campo variável.
    return TEXTO_PADRAO.format(ipca=ipca)


# =========================================================
# APLICATIVO STREAMLIT
# =========================================================

st.set_page_config(
    page_title="Aniversário de contrato",
    page_icon="📄",
    layout="centered"
)

st.title("Aniversário de contrato")

st.write(
    "Consulte o IPCA acumulado em 12 meses e gere "
    "o texto padrão para reajuste contratual."
)

st.info(
    "Fonte prioritária: IBGE. "
    "Fonte secundária: Brasil Indicadores. "
    "O campo CI permanece disponível para preenchimento manual."
)

if st.button("Consultar IPCA e gerar texto", type="primary"):

    with st.spinner("Consultando as fontes..."):

        # Prioridade: IBGE
        ibge = consultar_fonte(
            "IBGE",
            URL_IBGE
        )

        # Conferência: Brasil Indicadores
        secundario = consultar_fonte(
            "Brasil Indicadores",
            URL_SECUNDARIA
        )

    st.subheader("Resultado das consultas")

    st.write("**IBGE — fonte prioritária**")

    if ibge["ipca"]:
        st.success(f"Percentual identificado: {ibge['ipca']}")
    else:
        st.error(ibge["erro"])

    st.write("**Brasil Indicadores — conferência**")

    if secundario["ipca"]:
        st.write(
            f"Percentual identificado: {secundario['ipca']}"
        )
    else:
        st.warning(secundario["erro"])

    # Exige confirmação das duas fontes.
    if not ibge["ipca"] or not secundario["ipca"]:

        st.error(
            "Texto não gerado: não foi possível confirmar "
            "o índice nas duas fontes."
        )

    elif ibge["ipca"] != secundario["ipca"]:

        st.error(
            "Os percentuais identificados são diferentes. "
            "Confira os períodos de referência antes de "
            "utilizar o reajuste."
        )

    else:
        texto_final = gerar_texto(ibge["ipca"])

        st.success("Percentuais coincidentes nas duas fontes.")

        st.subheader("Texto padrão atualizado")

        st.code(texto_final, language="markdown")

        st.download_button(
            label="Baixar texto em TXT",
            data=texto_final,
            file_name="reajuste_aniversario_contrato.txt",
            mime="text/plain"
        )

        st.caption(
            "Redação e preços preservados. "
            "Preencha o campo CI manualmente."
        )

st.divider()

st.caption(
    "Fonte prioritária: IBGE | Conferência: Brasil Indicadores. "
    "A extração automática deve ser validada contra os dados "
    "e períodos publicados nas páginas."
)
