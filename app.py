
import re
from decimal import Decimal, ROUND_HALF_UP
from html.parser import HTMLParser
from pathlib import Path

import requests
import streamlit as st


# ============================================================
# CONFIGURAÇÃO
# ============================================================

st.set_page_config(
    page_title="Reajuste de Aniversário de Contrato",
    page_icon="📄",
    layout="centered",
    initial_sidebar_state="collapsed",
)

IBGE_URL = "https://www.ibge.gov.br/explica/inflacao.php"
BRASIL_INDICADORES_URL = "https://brasilindicadores.com.br/ipca"

IPCA_PADRAO = "4,58"
COMPETENCIA_PADRAO = "Set/2026"


# ============================================================
# LOCALIZAÇÃO DA LOGOMARCA
# ============================================================

def localizar_logo():
    """
    Procura a logomarca em locais comuns do aplicativo.
    Para publicação no Streamlit Cloud, mantenha a imagem
    dentro do repositório junto ao app.py.
    """

    pasta_app = Path(__file__).resolve().parent
    pasta_execucao = Path.cwd()

    nomes = [
        "Consigaz.png",
        "Consigaz(1).png",
        "consigaz.png",
        "Logo_consigaz.png",
        "Logo_consigaz.webp",
        "Logo_consigaz",
    ]

    pastas = [pasta_app, pasta_execucao]

    for pasta in pastas:
        for nome in nomes:
            caminho = pasta / nome
            if caminho.is_file():
                return caminho

    # Última tentativa: procura arquivos de imagem com
    # "consigaz" no nome, sem diferenciar maiúsculas/minúsculas.
    for pasta in pastas:
        try:
            for caminho in pasta.iterdir():
                if (
                    caminho.is_file()
                    and "consigaz" in caminho.name.lower()
                    and caminho.suffix.lower() in {
                        ".png", ".jpg", ".jpeg", ".webp"
                    }
                ):
                    return caminho
        except OSError:
            continue

    return None


# ============================================================
# CONSULTA DO IPCA
# ============================================================

class TextoHTML(HTMLParser):
    def __init__(self):
        super().__init__()
        self.textos = []

    def handle_data(self, data):
        texto = data.strip()
        if texto:
            self.textos.append(texto)

    def obter_texto(self):
        return " ".join(self.textos)


@st.cache_data(ttl=3600, show_spinner=False)
def consultar_ipca_ibge():
    try:
        resposta = requests.get(
            IBGE_URL,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 Chrome/131.0 Safari/537.36"
                )
            },
            timeout=15,
        )
        resposta.raise_for_status()

        parser = TextoHTML()
        parser.feed(resposta.text)
        texto = re.sub(r"\s+", " ", parser.obter_texto())

        padroes = [
            r"IPCA.{0,100}?acumulad[oa].{0,40}?12\s+meses"
            r".{0,100}?(\d{1,2}[,.]\d{2})\s*%",
            r"acumulad[oa].{0,40}?12\s+meses.{0,100}?IPCA"
            r".{0,100}?(\d{1,2}[,.]\d{2})\s*%",
            r"(\d{1,2}[,.]\d{2})\s*%.{0,100}?12\s+meses",
        ]

        percentual = None

        for padrao in padroes:
            resultado = re.search(
                padrao,
                texto,
                flags=re.IGNORECASE,
            )
            if resultado:
                percentual = resultado.group(1).replace(".", ",")
                break

        if not percentual:
            return None, None, (
                "Não foi possível identificar o IPCA na página do IBGE."
            )

        competencia = None
        meses = (
            "jan", "fev", "mar", "abr", "mai", "jun",
            "jul", "ago", "set", "out", "nov", "dez",
        )

        posicao = texto.lower().find(percentual.lower())

        if posicao >= 0:
            contexto = texto[
                max(0, posicao - 250):posicao + 250
            ]

            comp = re.search(
                r"\b("
                + "|".join(meses)
                + r")[a-z]*[/\s-](20\d{2})\b",
                contexto,
                flags=re.IGNORECASE,
            )

            if comp:
                competencia = (
                    comp.group(1).capitalize()[:3]
                    + "/"
                    + comp.group(2)
                )

        return percentual, competencia, "Consulta ao IBGE realizada."

    except requests.RequestException:
        return None, None, "Não foi possível acessar o IBGE."
    except Exception as erro:
        return None, None, f"Falha ao interpretar a página: {erro}"


# ============================================================
# ESTADO DA APLICAÇÃO
# ============================================================

if "tema" not in st.session_state:
    st.session_state.tema = "Claro"

if "ipca" not in st.session_state:
    st.session_state.ipca = IPCA_PADRAO

if "competencia_ipca" not in st.session_state:
    st.session_state.competencia_ipca = COMPETENCIA_PADRAO

if "origem_ipca" not in st.session_state:
    st.session_state.origem_ipca = (
        "Valor de contingência. Confirme o índice oficial."
    )

if "preco_anterior" not in st.session_state:
    st.session_state.preco_anterior = 0.0

if "ci" not in st.session_state:
    st.session_state.ci = ""

if "texto_final" not in st.session_state:
    st.session_state.texto_final = ""

if "resultado_calculo" not in st.session_state:
    st.session_state.resultado_calculo = None

if "ipca_inicializado" not in st.session_state:
    st.session_state.ipca_inicializado = False


def atualizar_ipca():
    percentual, competencia, mensagem = consultar_ipca_ibge()

    if percentual is not None:
        st.session_state.ipca = percentual

        if competencia:
            st.session_state.competencia_ipca = competencia

        st.session_state.origem_ipca = "Consulta automática ao IBGE."
        return True, mensagem

    st.session_state.origem_ipca = mensagem
    return False, mensagem


if not st.session_state.ipca_inicializado:
    atualizar_ipca()
    st.session_state.ipca_inicializado = True


def limpar_para_proximo_cliente():
    st.session_state.preco_anterior = 0.0
    st.session_state.ci = ""
    st.session_state.texto_final = ""
    st.session_state.resultado_calculo = None


# ============================================================
# TEMA CLARO / ESCURO
# ============================================================

if st.session_state.tema == "Escuro":
    fundo = "#111827"
    superficie = "#1f2937"
    texto = "#f3f4f6"
    borda = "#4b5563"
    campo = "#374151"
else:
    fundo = "#ffffff"
    superficie = "#f8fafc"
    texto = "#111827"
    borda = "#d1d5db"
    campo = "#ffffff"

st.markdown(
    f"""
    <style>
    .stApp,
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"] {{
        background-color: {fundo};
        color: {texto};
    }}

    [data-testid="stHeader"] {{
        background-color: {fundo};
    }}

    [data-testid="stMarkdownContainer"],
    [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] li,
    label {{
        color: {texto} !important;
    }}

    [data-testid="stTextInput"] input,
    [data-testid="stNumberInput"] input,
    [data-testid="stTextArea"] textarea {{
        background-color: {campo} !important;
        color: {texto} !important;
        border-color: {borda} !important;
    }}

    [data-baseweb="select"] > div {{
        background-color: {campo} !important;
        color: {texto} !important;
        border-color: {borda} !important;
    }}

    [data-testid="stAlert"] {{
        background-color: {superficie};
        color: {texto};
    }}

    div.stButton > button,
    div.stDownloadButton > button {{
        border: 1px solid {borda};
        border-radius: 8px;
    }}

    div.stButton > button:hover,
    div.stDownloadButton > button:hover {{
        border-color: #dc2626;
    }}

    a {{
        color: #3b82f6 !important;
    }}

    hr {{
        border-color: {borda};
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# CABEÇALHO: LOGO À ESQUERDA E BOTÃO DE TEMA À DIREITA
# ============================================================

col_logo, col_espaco, col_tema = st.columns(
    [2.2, 1.3, 1.2],
    vertical_alignment="center",
)

with col_logo:
    logo = localizar_logo()

    if logo:
        try:
            st.image(str(logo), width=220)
        except Exception as erro:
            st.error(f"Não foi possível abrir a logomarca: {erro}")
    else:
        st.error(
            "Logomarca não encontrada. Adicione o arquivo "
            "'Consigaz.png' à mesma pasta do app.py e ao repositório "
            "do Streamlit Cloud."
        )

with col_tema:
    rotulo_tema = (
        "☾ Modo escuro"
        if st.session_state.tema == "Claro"
        else "☀ Modo claro"
    )

    if st.button(
        rotulo_tema,
        key="alternar_tema",
        use_container_width=True,
    ):
        st.session_state.tema = (
            "Escuro"
            if st.session_state.tema == "Claro"
            else "Claro"
        )
        st.rerun()


st.divider()
st.title("Reajuste de Aniversário de Contrato")


# ============================================================
# IPCA E FONTES
# ============================================================

st.subheader("Índice de reajuste")

col_ipca, col_atualizar = st.columns([3, 1])

with col_ipca:
    st.text_input(
        "IPCA acumulado em 12 meses (%)",
        key="ipca",
        help="Percentual editável. Confira a competência antes de usar.",
    )

with col_atualizar:
    st.write("")
    st.write("")
    if st.button("Atualizar IPCA", use_container_width=True):
        consultar_ipca_ibge.clear()
        sucesso, mensagem = atualizar_ipca()

        if sucesso:
            st.success(mensagem)
        else:
            st.warning(mensagem)

        st.rerun()

st.caption(
    f"Competência informada: {st.session_state.competencia_ipca}"
)
st.caption(f"Situação: {st.session_state.origem_ipca}")

st.markdown(f"Fonte oficial: [IBGE — Inflação]({IBGE_URL})")
st.markdown(
    "Referência secundária: "
    f"[Brasil Indicadores — IPCA]({BRASIL_INDICADORES_URL})"
)

with st.expander("Consultar referência secundária"):
    st.write(
        "Abra a referência secundária e confira se o índice e a "
        "competência coincidem com os dados oficiais do IBGE."
    )
    st.link_button(
        "Abrir Brasil Indicadores",
        BRASIL_INDICADORES_URL,
    )

st.divider()


# ============================================================
# DADOS DO CLIENTE
# ============================================================

st.subheader("Dados do cliente")

st.number_input(
    "Preço Anterior (R$)",
    min_value=0.0,
    step=0.01,
    format="%.4f",
    key="preco_anterior",
)

st.text_input(
    "CI",
    key="ci",
    placeholder="Informe o CI do cliente",
)


# ============================================================
# CÁLCULO
# ============================================================

def formatar_moeda(valor):
    valor_formatado = f"{valor:,.4f}"
    return (
        valor_formatado
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


col_calcular, col_limpar = st.columns(2)

with col_calcular:
    calcular = st.button(
        "Calcular reajuste",
        type="primary",
        use_container_width=True,
    )

with col_limpar:
    st.button(
        "Limpar para próximo cliente",
        on_click=limpar_para_proximo_cliente,
        use_container_width=True,
    )


if calcular:
    try:
        ipca_limpo = (
            str(st.session_state.ipca)
            .strip()
            .replace("%", "")
            .replace(",", ".")
        )

        ipca_decimal = Decimal(ipca_limpo)
        preco_anterior_decimal = Decimal(
            str(st.session_state.preco_anterior)
        )

        if ipca_decimal < 0:
            st.error("O IPCA não pode ser negativo.")
            st.stop()

        preco_negociado = (
            preco_anterior_decimal
            * (
                Decimal("1")
                + ipca_decimal / Decimal("100")
            )
        ).quantize(
            Decimal("0.0001"),
            rounding=ROUND_HALF_UP,
        )

        preco_anterior_formatado = formatar_moeda(
            preco_anterior_decimal
        )
        preco_negociado_formatado = formatar_moeda(
            preco_negociado
        )
        ipca_formatado = str(ipca_decimal).replace(".", ",") + "%"

        ci_texto = (
            st.session_state.ci.strip()
            if st.session_state.ci.strip()
            else "____________________"
        )

        st.session_state.texto_final = (
            "Aniversário de contrato\n\n"
            "Reajuste de preço devido aniversário de contrato.\n"
            f"IPCA do mês em {ipca_formatado}\n\n"
            f"Preço Anterior: R$ {preco_anterior_formatado}\n"
            f"Preço Negociado: R$ {preco_negociado_formatado} \n\n"
            f"CI -  {ci_texto} - Preço"
        )

        st.session_state.resultado_calculo = preco_negociado

    except Exception:
        st.error(
            "Não foi possível calcular. Verifique o percentual do IPCA."
        )


# ============================================================
# RESULTADO E DOWNLOAD
# ============================================================

if st.session_state.resultado_calculo is not None:
    st.divider()
    st.subheader("Resultado")

    st.metric(
        "Preço Negociado",
        f"R$ {formatar_moeda(st.session_state.resultado_calculo)}",
    )

    st.text_area(
        "Comunicado para copiar ou revisar",
        value=st.session_state.texto_final,
        height=230,
    )

    st.download_button(
        "Baixar comunicado em TXT",
        data=st.session_state.texto_final,
        file_name="aniversario_contrato.txt",
        mime="text/plain",
        use_container_width=True,
    )
