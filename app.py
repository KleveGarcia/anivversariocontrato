
import streamlit as st
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


# =========================================================
# LOGOMARCA CONSIGAZ
# =========================================================

PASTA_APP = Path(__file__).parent
ARQUIVO_LOGO = PASTA_APP / "Consigaz.png"

if ARQUIVO_LOGO.exists():
    st.image(str(ARQUIVO_LOGO), width=300)
else:
    st.warning(
        "Logomarca não encontrada. "
        "Adicione o arquivo Consigaz.png à pasta do aplicativo."
    )


# =========================================================
# TÍTULO E ORIENTAÇÕES
# =========================================================

st.title("Reajuste de Aniversário de Contrato")

st.write(
    "Informe o IPCA acumulado em 12 meses, o preço anterior "
    "e o CI para calcular o reajuste e gerar o comunicado."
)

st.markdown(
    "[Consultar IPCA oficial no IBGE]"
    "(https://www.ibge.gov.br/explica/inflacao.php)"
)

st.markdown(
    "[Conferir IPCA no Brasil Indicadores]"
    "(https://brasilindicadores.com.br/ipca)"
)

st.info(
    "Consulte o acumulado em 12 meses no IBGE, "
    "fonte prioritária. Informe o percentual manualmente."
)


# =========================================================
# ESTADO INICIAL DOS CAMPOS
# =========================================================

CAMPOS = ["ipca", "preco_anterior", "ci"]

for campo in CAMPOS:
    if campo not in st.session_state:
        st.session_state[campo] = ""

if "texto_final" not in st.session_state:
    st.session_state.texto_final = ""

if "preco_negociado" not in st.session_state:
    st.session_state.preco_negociado = ""

if "ipca_calculado" not in st.session_state:
    st.session_state.ipca_calculado = ""

if "preco_anterior_calculado" not in st.session_state:
    st.session_state.preco_anterior_calculado = ""


# =========================================================
# LIMPEZA PARA O PRÓXIMO CLIENTE
# =========================================================

def limpar_para_proximo_cliente():
    for campo in CAMPOS:
        st.session_state[campo] = ""

    st.session_state.texto_final = ""
    st.session_state.preco_negociado = ""
    st.session_state.ipca_calculado = ""
    st.session_state.preco_anterior_calculado = ""


# =========================================================
# FUNÇÕES DE CONVERSÃO E FORMATAÇÃO
# =========================================================

def converter_decimal(valor):
    """
    Aceita números no padrão brasileiro, por exemplo:
    4,58
    6,9588
    1.234,5678
    """

    valor = valor.strip()
    valor = valor.replace("R$", "").replace(" ", "")

    if not valor:
        raise ValueError("Preencha todos os campos obrigatórios.")

    if "," in valor:
        valor = valor.replace(".", "").replace(",", ".")

    return Decimal(valor)


def formatar_decimal(valor, casas=4):
    """Formata valores no padrão brasileiro."""

    valor = valor.quantize(
        Decimal("1").scaleb(-casas),
        rounding=ROUND_HALF_UP
    )

    parte_inteira, parte_decimal = f"{valor:.{casas}f}".split(".")

    parte_inteira = f"{int(parte_inteira):,}".replace(",", ".")

    return f"{parte_inteira},{parte_decimal}"


def formatar_ipca(valor):
    """Formata o IPCA com duas casas decimais."""

    valor = valor.quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )

    return f"{valor:.2f}".replace(".", ",") + "%"


# =========================================================
# CAMPOS DE PREENCHIMENTO
# =========================================================

st.subheader("Dados do reajuste")

st.text_input(
    "IPCA acumulado em 12 meses (%)",
    key="ipca",
    placeholder="Ex.: 4,58"
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
# CÁLCULO DO REAJUSTE E GERAÇÃO DO TEXTO
# =========================================================

if st.button(
    "Calcular reajuste e gerar texto",
    type="primary",
    use_container_width=True
):

    try:
        # Conversão dos campos informados.
        ipca_numero = converter_decimal(
            st.session_state.ipca
        )

        preco_numero = converter_decimal(
            st.session_state.preco_anterior
        )

        # Validação dos valores.
        if not Decimal("0") <= ipca_numero <= Decimal("100"):
            raise ValueError(
                "O IPCA deve estar entre 0% e 100%."
            )

        if preco_numero <= 0:
            raise ValueError(
                "O preço anterior deve ser maior que zero."
            )

        # Fórmula do reajuste:
        # Preço negociado = preço anterior x (1 + IPCA/100)
        preco_negociado = (
            preco_numero
            * (
                Decimal("1")
                + ipca_numero / Decimal("100")
            )
        ).quantize(
            Decimal("0.0001"),
            rounding=ROUND_HALF_UP
        )

        # Formatação dos valores.
        ipca_formatado = formatar_ipca(ipca_numero)

        anterior_formatado = formatar_decimal(
            preco_numero
        )

        negociado_formatado = formatar_decimal(
            preco_negociado
        )

        # CI manual. Se vazio, mantém uma lacuna.
        ci_formatado = (
            st.session_state.ci.strip()
            if st.session_state.ci.strip()
            else "____________________"
        )

        # =================================================
        # TEXTO PADRÃO
        # Mantém a redação original e os preços formatados.
        # =================================================

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

        # Armazena os resultados na sessão.
        st.session_state.texto_final = texto_final
        st.session_state.preco_negociado = negociado_formatado
        st.session_state.ipca_calculado = ipca_formatado
        st.session_state.preco_anterior_calculado = (
            anterior_formatado
        )

    except (ValueError, InvalidOperation):
        st.session_state.texto_final = ""
        st.session_state.preco_negociado = ""
        st.session_state.ipca_calculado = ""
        st.session_state.preco_anterior_calculado = ""

        st.error(
            "Não foi possível calcular o reajuste. "
            "Confira os campos. Exemplos: IPCA 4,58 "
            "e preço anterior 6,9588."
        )


# =========================================================
# EXIBIÇÃO DOS RESULTADOS
# =========================================================

if st.session_state.preco_negociado:

    st.success("Reajuste calculado com sucesso.")

    col1, col2 = st.columns(2)

    col1.metric(
        "Preço anterior",
        f"R$ {st.session_state.preco_anterior_calculado}"
    )

    col2.metric(
        "Preço negociado",
        f"R$ {st.session_state.preco_negociado}"
    )

    st.caption(
        f"Percentual de reajuste aplicado: "
        f"{st.session_state.ipca_calculado}"
    )


# =========================================================
# TEXTO GERADO E DOWNLOAD
# =========================================================

if st.session_state.texto_final:

    st.subheader("Texto padrão gerado")

    st.text_area(
        "Comunicado pronto para copiar",
        value=st.session_state.texto_final,
        height=250
    )

    st.download_button(
        label="Baixar texto em TXT",
        data=st.session_state.texto_final,
        file_name="aniversario_contrato.txt",
        mime="text/plain",
        use_container_width=True
    )


# =========================================================
# BOTÃO PARA O PRÓXIMO CLIENTE
# =========================================================

st.divider()

st.subheader("Próximo cliente")

st.button(
    "Limpar para próximo cliente",
    on_click=limpar_para_proximo_cliente,
    use_container_width=True
)
