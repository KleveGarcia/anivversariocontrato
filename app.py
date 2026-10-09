
import streamlit as st
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


# =====================================================
# CONFIGURAÇÃO
# =====================================================

st.set_page_config(
    page_title="Aniversário de contrato",
    page_icon="📄",
    layout="centered"
)


# =====================================================
# ESTADO DOS CAMPOS
# =====================================================

CAMPOS = ["ipca", "preco_anterior", "ci"]

for campo in CAMPOS:
    if campo not in st.session_state:
        st.session_state[campo] = ""

if "texto_final" not in st.session_state:
    st.session_state.texto_final = ""

if "preco_negociado" not in st.session_state:
    st.session_state.preco_negociado = ""


def limpar_para_proximo_cliente():
    """Limpa os campos e os resultados do cliente atual."""
    for campo in CAMPOS:
        st.session_state[campo] = ""

    st.session_state.texto_final = ""
    st.session_state.preco_negociado = ""


# =====================================================
# FUNÇÕES AUXILIARES
# =====================================================

def converter_decimal(valor):
    valor = valor.strip().replace("R$", "").replace(" ", "")

    if not valor:
        raise ValueError("Preencha o campo.")

    if "," in valor:
        valor = valor.replace(".", "").replace(",", ".")

    return Decimal(valor)


def formatar_decimal(valor, casas=4):
    valor = valor.quantize(
        Decimal("1").scaleb(-casas),
        rounding=ROUND_HALF_UP
    )

    parte_inteira, parte_decimal = f"{valor:.{casas}f}".split(".")
    parte_inteira = f"{int(parte_inteira):,}".replace(",", ".")

    return f"{parte_inteira},{parte_decimal}"


def formatar_ipca(valor):
    valor = valor.quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )
    return f"{valor:.2f}".replace(".", ",") + "%"


# =====================================================
# INTERFACE
# =====================================================

st.title("Aniversário de contrato")

st.write(
    "Informe o IPCA acumulado em 12 meses e o preço anterior. "
    "O sistema calculará o preço reajustado."
)

st.markdown(
    "[Consultar IPCA oficial no IBGE]"
    "(https://www.ibge.gov.br/explica/inflacao.php)"
)

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


# =====================================================
# CÁLCULO E GERAÇÃO DO TEXTO
# =====================================================

if st.button("Calcular reajuste e gerar texto", type="primary"):

    try:
        ipca_numero = converter_decimal(st.session_state.ipca)
        preco_numero = converter_decimal(st.session_state.preco_anterior)

        if not Decimal("0") <= ipca_numero <= Decimal("100"):
            raise ValueError("O IPCA deve estar entre 0% e 100%.")

        if preco_numero <= 0:
            raise ValueError("O preço anterior deve ser maior que zero.")

        preco_negociado = (
            preco_numero * (
                Decimal("1") + ipca_numero / Decimal("100")
            )
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

    except (ValueError, InvalidOperation):
        st.session_state.texto_final = ""
        st.session_state.preco_negociado = ""
        st.error(
            "Confira os valores informados. "
            "Exemplos: IPCA 4,58 e preço 6,9588."
        )


# =====================================================
# EXIBIÇÃO DO RESULTADO
# =====================================================

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

    st.caption(
        f"Reajuste aplicado: "
        f"{formatar_ipca(converter_decimal(st.session_state.ipca))}"
    )

if st.session_state.texto_final:
    st.subheader("Texto padrão gerado")

    st.text_area(
        "Texto pronto para copiar",
        value=st.session_state.texto_final,
        height=250,
        key="resultado_texto"
    )

    st.download_button(
        label="Baixar texto em TXT",
        data=st.session_state.texto_final,
        file_name="aniversario_contrato.txt",
        mime="text/plain"
    )


# =====================================================
# LIMPEZA PARA O PRÓXIMO CLIENTE
# =====================================================

st.divider()
st.subheader("Próximo cliente")

st.button(
    "Limpar para próximo cliente",
    on_click=limpar_para_proximo_cliente,
    use_container_width=True,
    type="secondary"
)
