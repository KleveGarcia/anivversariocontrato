
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

PASTA_APP = Path(__file__).parent
ARQUIVO_LOGO = PASTA_APP / "Consigaz.png"


# =========================================================
# FUNÇÕES DE ESTADO
# =========================================================

def inicializar_estado():
    valores_iniciais = {
        "ipca": "",
        "preco_anterior": "",
        "ci": "",
        "texto_final": "",
        "preco_negociado": "",
        "ipca_calculado": "",
        "preco_anterior_calculado": "",
        "erro_calculo": ""
    }

    for chave, valor in valores_iniciais.items():
        if chave not in st.session_state:
            st.session_state[chave] = valor


def limpar_para_proximo_cliente():
    """Limpa os campos e resultados do cliente atual."""

    for campo in [
        "ipca",
        "preco_anterior",
        "ci",
        "texto_final",
        "preco_negociado",
        "ipca_calculado",
        "preco_anterior_calculado",
        "erro_calculo"
    ]:
        st.session_state[campo] = ""


inicializar_estado()


# =========================================================
# FUNÇÕES DE CONVERSÃO E FORMATAÇÃO
# =========================================================

def converter_decimal(valor):
    """
    Aceita números no padrão brasileiro:
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

    try:
        return Decimal(valor)
    except InvalidOperation:
        raise ValueError("Valor numérico inválido.")


def formatar_decimal(valor, casas=4):
    """Formata valores com vírgula decimal."""

    valor = valor.quantize(
        Decimal("1").scaleb(-casas),
        rounding=ROUND_HALF_UP
    )

    parte_inteira, parte_decimal = f"{valor:.{casas}f}".split(".")

    parte_inteira = f"{int(parte_inteira):,}".replace(",", ".")

    return f"{parte_inteira},{parte_decimal}"


def formatar_ipca(valor):
    """Formata o percentual com duas casas decimais."""

    valor = valor.quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )

    return f"{valor:.2f}".replace(".", ",") + "%"


# =========================================================
# CABEÇALHO E LOGOMARCA
# =========================================================

if ARQUIVO_LOGO.exists():
    st.image(str(ARQUIVO_LOGO), width=300)
else:
    st.warning(
        "Logomarca não encontrada. "
        "Adicione o arquivo Consigaz.png à pasta do aplicativo."
    )

st.title("Reajuste de Aniversário de Contrato")

st.write(
    "Informe o IPCA acumulado em 12 meses e o preço anterior "
    "para calcular o reajuste e gerar o comunicado."
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
    "O IBGE é a fonte prioritária. Consulte o IPCA acumulado "
    "em 12 meses e informe o percentual manualmente."
)


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
# CÁLCULO E GERAÇÃO DO TEXTO
# =========================================================

if st.button(
    "Calcular reajuste e gerar texto",
    type="primary",
    use_container_width=True
):

    # Apaga resultados anteriores antes de calcular novamente.
    st.session_state.texto_final = ""
    st.session_state.preco_negociado = ""
    st.session_state.ipca_calculado = ""
    st.session_state.preco_anterior_calculado = ""
    st.session_state.erro_calculo = ""

    try:
        ipca_numero = converter_decimal(
            st.session_state.ipca
        )

        preco_numero = converter_decimal(
            st.session_state.preco_anterior
        )

        # Validação do percentual.
        if not Decimal("0") <= ipca_numero <= Decimal("100"):
            raise ValueError(
                "O IPCA deve estar entre 0% e 100%."
            )

        # Validação do preço anterior.
        if preco_numero <= 0:
            raise ValueError(
                "O preço anterior deve ser maior que zero."
            )

        # Fórmula:
        # Preço negociado = preço anterior x (1 + IPCA / 100)
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

        # CI permanece manual.
        ci_formatado = (
            st.session_state.ci.strip()
            if st.session_state.ci.strip()
            else "____________________"
        )

        # =================================================
        # TEXTO PADRÃO ORIGINAL
        # Redação preservada; somente os valores variáveis
        # são preenchidos.
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

        # Armazena os resultados.
        st.session_state.texto_final = texto_final
        st.session_state.preco_negociado = negociado_formatado
        st.session_state.ipca_calculado = ipca_formatado
        st.session_state.preco_anterior_calculado = (
            anterior_formatado
        )

    except (ValueError, InvalidOperation) as erro:
        st.session_state.erro_calculo = str(erro)


# =========================================================
# MENSAGENS DE ERRO
# =========================================================

if st.session_state.erro_calculo:
    st.error(
        "Não foi possível calcular o reajuste: "
        + st.session_state.erro_calculo
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
        "Percentual aplicado: "
        + st.session_state.ipca_calculado
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
# LIMPEZA PARA O PRÓXIMO CLIENTE
# =========================================================

st.divider()

st.subheader("Próximo cliente")

st.button(
    "Limpar para próximo cliente",
    on_click=limpar_para_proximo_cliente,
    use_container_width=True
)
