
import re
from pathlib import Path

import requests
import streamlit as st
from bs4 import BeautifulSoup


# ============================================================
# CONFIGURAÇÕES
# ============================================================

URL_IBGE = "https://www.ibge.gov.br/explica/inflacao.php"
URL_SECUNDARIA = "https://brasilindicadores.com.br/ipca"

# Texto padrão: preservar redação, preços e formatação.
# Somente o percentual do IPCA é variável.
TEXTO_PADRAO = """**Aniversário de contrato**

**Reajuste de preço devido aniversário de contrato.**
**IPCA do mês em {ipca}**

**Preço Anterior: R$ 6,9588**
**Preço Negociado: R$ 7,2789&#x20;**

**CI -  ____________________ - Preço**"""

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/130.0.0.0 Safari/537.36"
    )
}


# ============================================================
# CONSULTA DAS FONTES
# ============================================================

def obter_texto_site(url):
    """Obtém e converte o conteúdo HTML em texto."""

    resposta = requests.get(
        url,
        headers=HEADERS,
        timeout=30
    )

    resposta.raise_for_status()

    soup = BeautifulSoup(
        resposta.content,
        "html.parser"
    )

    # Remove conteúdos que podem gerar correspondências falsas.
    for elemento in soup(
        ["script", "style", "noscript", "svg"]
    ):
        elemento.decompose()

    return re.sub(
        r"\s+",
        " ",
        soup.get_text(" ", strip=True)
    )


def extrair_ipca_12_meses(texto):
    """
    Procura um percentual próximo de uma referência explícita
    ao acumulado de 12 meses.

    Se não encontrar um resultado confiável, interrompe
    o processamento em vez de inventar um valor.
    """

    texto = re.sub(r"\s+", " ", texto)

    # Identifica possíveis referências ao acumulado de 12 meses.
    padroes_referencia = [
        r"IPCA.{0,100}?acumulad[oa].{0,50}?12\s+meses",
        r"acumulad[oa].{0,50}?12\s+meses.{0,100}?IPCA",
        r"IPCA.{0,100}?12\s+meses",
        r"12\s+meses.{0,100}?IPCA",
    ]

    referencias = []

    for padrao in padroes_referencia:
        for resultado in re.finditer(
            padrao, texto, re.IGNORECASE
        ):
            referencias.append(resultado)

    if not referencias:
        raise ValueError(
            "A página não apresentou uma referência "
            "identificável ao IPCA acumulado em 12 meses."
        )

    # Verifica os percentuais próximos das referências.
    candidatos = set()

    for referencia in referencias:
        inicio = max(0, referencia.start() - 180)
        fim = min(len(texto), referencia.end() + 250)

        trecho = texto[inicio:fim]

        percentuais = re.findall(
            r"(?<![\d,])(\d{1,2},\d{2})\s*%",
            trecho
        )

        for percentual in percentuais:
            valor = float(percentual.replace(",", "."))

            # Validação básica para evitar valores absurdos.
            if 0 <= valor <= 100:
                candidatos.add(percentual + "%")

    if len(candidatos) == 1:
        return candidatos.pop()

    if not candidatos:
        raise ValueError(
            "Não foi possível localizar um percentual "
            "junto à referência de 12 meses."
        )

    raise ValueError(
        "Foram encontrados vários percentuais próximos "
        "da referência de 12 meses. É necessária uma "
        "verificação manual para evitar um índice incorreto."
    )


def consultar_fonte(nome, url):
    """Consulta uma fonte e devolve o percentual identificado."""

    try:
        texto = obter_texto_site(url)
        percentual = extrair_ipca_12_meses(texto)

        return {
            "fonte": nome,
            "url": url,
            "ipca": percentual,
            "erro": None,
        }

    except requests.RequestException as erro:
        return {
            "fonte": nome,
            "url": url,
            "ipca": None,
            "erro": f"Falha de conexão: {erro}",
        }

    except ValueError as erro:
        return {
            "fonte": nome,
            "url": url,
            "ipca": None,
            "erro": str(erro),
        }


# ============================================================
# GERAÇÃO DO TEXTO
# ============================================================

def gerar_comunicado(ipca):
    """Substitui exclusivamente o campo variável do IPCA."""

    return TEXTO_PADRAO.format(ipca=ipca)


# ============================================================
# INTERFACE STREAMLIT
# ============================================================

st.set_page_config(
    page_title="Reajuste por Aniversário de Contrato",
    page_icon="📄",
    layout="centered"
)

st.title("Aniversário de contrato")
st.write(
    "Geração do texto padrão com consulta do IPCA "
    "acumulado em 12 meses."
)

st.info(
    "Fonte prioritária: IBGE. "
    "Fonte de conferência: Brasil Indicadores. "
    "O CI deve ser preenchido manualmente."
)

if st.button("Consultar IPCA e gerar texto", type="primary"):

    with st.spinner("Consultando as duas fontes..."):

        # O IBGE é sempre consultado primeiro.
        resultado_ibge = consultar_fonte(
            "IBGE",
            URL_IBGE
        )

        # Segunda fonte para conferência.
        resultado_secundario = consultar_fonte(
            "Brasil Indicadores",
            URL_SECUNDARIA
        )

    st.subheader("Resultado da consulta")

    st.write("**Fonte prioritária: IBGE**")

    if resultado_ibge["ipca"]:
        st.success(
            f"IPCA identificado no IBGE: "
            f"{resultado_ibge['ipca']}"
        )
    else:
        st.error(
            f"IBGE: {resultado_ibge['erro']}"
        )

    st.write("**Fonte secundária: Brasil Indicadores**")

    if resultado_secundario["ipca"]:
        st.write(
            "IPCA identificado: "
            f"{resultado_secundario['ipca']}"
        )
    else:
        st.warning(
            "Brasil Indicadores: "
            f"{resultado_secundario['erro']}"
        )

    # Não gera o comunicado se o IBGE não puder ser validado.
    if not resultado_ibge["ipca"]:

        st.error(
            "Texto não gerado. Não foi possível "
            "confirmar o índice na fonte prioritária."
        )

    # Exige conferência da segunda fonte.
    elif not resultado_secundario["ipca"]:

        st.error(
            "Texto não gerado. A segunda fonte não "
            "pôde confirmar o índice."
        )

    # Compara os percentuais identificados.
    elif (
        resultado_ibge["ipca"]
        != resultado_secundario["ipca"]
    ):

        st.error(
            "Divergência entre as fontes. "
            "Verifique os períodos de referência "
            "antes de utilizar o comunicado."
        )

    else:
        ipca_confirmado = resultado_ibge["ipca"]

        texto_final = gerar_comunicado(
            ipca_confirmado
        )

        st.success(
            "Índice coincidente nas duas fontes."
        )

        st.subheader("Texto padrão atualizado")

        st.code(
            texto_final,
            language="markdown"
        )

        st.download_button(
            label="Baixar texto em TXT",
            data=texto_final,
            file_name="reajuste_aniversario_contrato.txt",
            mime="text/plain"
        )

        st.caption(
            "O texto mantém os preços e a redação definidos. "
            "O campo CI permanece em branco."
        )

st.divider()

st.caption(
    "Fontes consultadas: IBGE e Brasil Indicadores. "
    "A extração depende da estrutura atual das páginas "
    "e deve ser validada antes do uso operacional."
)
