
import re
import requests
import streamlit as st

from html.parser import HTMLParser
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path


# =========================================================
# CONFIGURAÇÃO DA PÁGINA
# =========================================================

st.set_page_config(
    page_title="Reajuste de Aniversário de Contrato",
    page_icon="📄",
    layout="centered"
)

PASTA_APP = Path(__file__).parent
ARQUIVO_LOGO = PASTA_APP / "Consigaz.png"

URL_IBGE = "https://www.ibge.gov.br/explica/inflacao.php"
URL_SECUNDARIA = "https://brasilindicadores.com.br/ipca"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; ConsigazReajuste/1.0)"
}


# =========================================================
# LEITURA DE HTML SEM BEAUTIFULSOUP
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
        timeout=20
    )
    resposta.raise_for_status()

    extrator = ExtratorHTML()
    extrator.feed(resposta.text)

    return re.sub(r"\s+", " ", extrator.obter_texto())


# =========================================================
# CONSULTA AUTOMÁTICA DO IPCA NO IBGE
# =========================================================

def consultar_ipca_ibge():
    texto = obter_texto_site(URL_IBGE)

    # Procura o valor especificamente associado ao acumulado
    # de 12 meses, sem confundi-lo com o IPCA mensal.
    padrao = (
        r"IPCA\s+acumulado\s+de\s+12\s+meses"
        r"\s*[:\-]?\s*"
        r"(\d{1,2},\d{2})\s*%"
        r"\s*([A-Za-zÀ-ÿ]{3}/\d{4})?"
    )

    resultado = re.search(padrao, texto, re.IGNORECASE)

    if not resultado:
        raise ValueError(
            "Não foi possível identificar o IPCA acumulado "
            "em 12 meses na página oficial."
        )

    percentual = resultado.group(1)
    competencia = resultado.group(2) or ""

    return percentual, competencia


@st.cache_data(ttl=3600, show_spinner=False)
def consultar_ipca_ibge_cache():
    return consultar_ipca_ibge()


# =========================================================
# CONSULTA DA SEGUNDA FONTE PARA CONFERÊNCIA
# =========================================================

def consultar_ipca_secundario():
    texto = obter_texto_site(URL_SECUNDARIA)

    padroes = [
        (
            r"IPCA\s+acumulado\s+em\s+12\s+meses"
            r"\s*[:\-]?\s*(\d{1,2},\d{2})\s*%"
        ),
        (
            r"IPCA\s+acumulado\s+de\s+12\s+meses"
            r"\s*[:\-]?\s*(\d{1,2},\d{2})\s*%"
        ),
    ]

    for padrao in padroes:
        resultado = re.search(padrao, texto, re.IGNORECASE)
        if resultado:
            return resultado.group(1)

    raise ValueError(
        "Não foi possível identificar o acumulado de 12 meses "
        "na fonte secundária."
    )


# =========================================================
# FORMATAÇÃO E CÁLCULO
# =========================================================

def converter_decimal(valor):
    valor = valor.strip().replace("R$", "").replace(" ", "")

    if not valor:
        raise ValueError("Preencha o campo obrigatório.")

    if "," in valor:
        valor = valor.replace(".", "").replace(",", ".")

    return Decimal(valor)


def formatar_decimal(valor, casas=4):
    valor = valor.quantize(
        Decimal("1").scaleb(-casas),
        rounding=ROUND_HALF_UP
    )

    inteiro, decimal = f"{valor:.{casas}f}".split(".")
    inteiro = f"{int(inteiro):,}".replace(",", ".")

    return f"{inteiro},{decimal}"


def formatar_ipca(valor):
    valor = valor.quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )
    return f"{valor:.2f}".replace(".", ",") + "%"


# =========================================================
# ESTADO DA APLICAÇÃO
# =========================================================

if "ipca" not in st.session_state:
    st.session_state.ipca = ""

if "competencia_ipca" not in st.session_state:
    st.session_state.competencia_ipca = ""

if "origem_ipca" not in st.session_state:
    st.session_state.origem_ipca = ""

if "preco_anterior" not in st.session_state:
    st.session_state.preco_anterior = ""

if "ci" not in st.session_state:
    st.session_state.ci = ""

if "texto_final" not in st.session_state:
    st.session_state.texto_final = ""

if "preco_negociado" not in st.session_state:
    st.session_state.preco_negociado = ""

if "erro_calculo" not in st.session_state:
    st.session_state.erro_calculo = ""


def atualizar_ipca():
    """Atualiza o campo com o dado oficial mais recente."""

    try:
        percentual, competencia = consultar_ipca_ibge_cache()

        # Atribui antes da criação dos widgets.
        st.session_state.ipca = percentual
        st.session_state.competencia_ipca = competencia
        st.session_state.origem_ipca = "IBGE — consulta online"

        st.session_state.texto_final = ""
        st.session_state.preco_negociado = ""
        st.session_state.erro_calculo = ""

    except Exception as erro:
        st.session_state.origem_ipca = (
            "Falha na consulta ao IBGE: " + str(erro)
        )


def limpar_para_proximo_cliente():
    # Mantém o IPCA oficial preenchido para o próximo cliente.
    st.session_state.preco_anterior = ""
    st.session_state.ci = ""
    st.session_state.texto_final = ""
    st.session_state.preco_negociado = ""
    st.session_state.erro_calculo = ""


# =========================================================
# CABEÇALHO E LOGOMARCA
# =========================================================

if ARQUIVO_LOGO.exists():
    st.image(str(ARQUIVO_LOGO), width=300)
else:
    st.warning(
        "Logomarca não encontrada. Adicione Consigaz.png "
        "à mesma pasta do app.py."
    )

st.title("Reajuste de Aniversário de Contrato")

st.markdown(
    "[IBGE — inflação oficial]"
    "(https://www.ibge.gov.br/explica/inflacao.php)"
)

st.markdown(
    "[Brasil Indicadores — IPCA]"
    "(https://brasilindicadores.com.br/ipca)"
)


# =========================================================
# BUSCA INICIAL DO IPCA
# =========================================================

if not st.session_state.ipca:
    atualizar_ipca()

st.subheader("IPCA oficial acumulado em 12 meses")

if st.session_state.ipca:
    st.metric(
        label="IPCA acumulado",
        value=f"{st.session_state.ipca}%"
    )

    if st.session_state.competencia_ipca:
        st.caption(
            f"Competência identificada: "
            f"{st.session_state.competencia_ipca}"
        )

    st.caption(st.session_state.origem_ipca)

else:
    st.warning(
        "Não foi possível carregar o IPCA automaticamente. "
        "Consulte o IBGE e informe o valor manualmente."
    )
    st.caption(st.session_state.origem_ipca)


if st.button("Atualizar IPCA pelo IBGE"):
    st.cache_data.clear()
    atualizar_ipca()
    st.rerun()


# =========================================================
# CONFERÊNCIA COM A SEGUNDA FONTE
# =========================================================

with st.expander("Conferir Brasil Indicadores"):
    if st.button("Consultar segunda fonte"):
        try:
            ipca_secundario = consultar_ipca_secundario()

            st.write(
                f"Brasil Indicadores: **{ipca_secundario}%**"
            )

            if st.session_state.ipca:
                oficial = st.session_state.ipca.replace(",", ".")

                if Decimal(oficial) == Decimal(
                    ipca_secundario.replace(",", ".")
                ):
                    st.success(
                        "Os percentuais são iguais. "
                        "Confira também a competência."
                    )
                else:
                    st.warning(
                        "Os percentuais são diferentes. "
                        "Confira as competências e os dados "
                        "publicados antes de aplicar o reajuste."
                    )

        except Exception as erro:
            st.error(
                f"Não foi possível consultar a segunda fonte: {erro}"
            )


# =========================================================
# CAMPOS DO REAJUSTE
# =========================================================

st.divider()
st.subheader("Dados do contrato")

st.text_input(
    "IPCA acumulado em 12 meses (%) — editável",
    key="ipca",
    help="Preenchido pelo IBGE. Você pode alterar manualmente."
)

st.text_input(
    "Preço Anterior (R$)",
    key="preco_anterior",
    placeholder="Ex.: 6,9588"
)

st.text_input(
    "CI (preenchimento manual)",
    key="ci",
    placeholder="Digite o número do CI"
)


# =========================================================
# CÁLCULO E GERAÇÃO DO TEXTO
# =========================================================

if st.button(
    "Calcular reajuste e gerar texto",
    type="primary",
    use_container_width=True
):
    st.session_state.texto_final = ""
    st.session_state.preco_negociado = ""
    st.session_state.erro_calculo = ""

    try:
        ipca_numero = converter_decimal(st.session_state.ipca)
        preco_numero = converter_decimal(
            st.session_state.preco_anterior
        )

        if not Decimal("0") <= ipca_numero <= Decimal("100"):
            raise ValueError("O IPCA deve estar entre 0% e 100%.")

        if preco_numero <= 0:
            raise ValueError(
                "O preço anterior deve ser maior que zero."
            )

        preco_negociado = (
            preco_numero
            * (Decimal("1") + ipca_numero / Decimal("100"))
        ).quantize(
            Decimal("0.0001"),
            rounding=ROUND_HALF_UP
        )

        ipca_formatado = formatar_ipca(ipca_numero)
        anterior_formatado = formatar_decimal(preco_numero)
        negociado_formatado = formatar_decimal(preco_negociado)

        ci_formatado = (
            st.session_state.ci.strip()
            if st.session_state.ci.strip()
            else "____________________"
        )

        # TEXTO PADRÃO DEFINIDO PELO USUÁRIO.
        texto_final = (
            "Aniversário de contrato\n"
            "\n"
            "Reajuste de preço devido aniversário de contrato.\n"
            f"IPCA do mês em {ipca_formatado}\n"
            "\n"
            f"Preço Anterior: R$ {anterior_formatado}\n"
            f"Preço Negociado: R$ {negociado_formatado} \n"
            "\n"
            f"CI -  {ci_formatado} - Preço"
        )

        st.session_state.texto_final = texto_final
        st.session_state.preco_negociado = negociado_formatado

    except (ValueError, InvalidOperation) as erro:
        st.session_state.erro_calculo = str(erro)


# =========================================================
# RESULTADO DO REAJUSTE
# =========================================================

if st.session_state.erro_calculo:
    st.error(st.session_state.erro_calculo)

if st.session_state.preco_negociado:
    st.success("Reajuste calculado com sucesso.")

    col1, col2 = st.columns(2)

    col1.metric(
        "Preço anterior",
        f"R$ {formatar_decimal(converter_decimal(st.session_state.preco_anterior))}"
    )

    col2.metric(
        "Preço negociado",
        f"R$ {st.session_state.preco_negociado}"
    )


# =========================================================
# TEXTO FINAL E DOWNLOAD
# =========================================================

if st.session_state.texto_final:
    st.subheader("Texto padrão gerado")

    st.text_area(
        "Comunicado pronto para copiar",
        value=st.session_state.texto_final,
        height=250
    )

    st.download_button(
        label="Baixar comunicado em TXT",
        data=st.session_state.texto_final,
        file_name="aniversario_contrato.txt",
        mime="text/plain",
        use_container_width=True
    )


# =========================================================
# LIMPEZA PARA O PRÓXIMO CLIENTE
# =========================================================

st.divider()
st.subheader("Próximo cliente")

st.button(
    "Limpar para próximo cliente",
    on_click=limpar_para_proximo_cliente,
    use_container_width=True
)
