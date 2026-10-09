
import re
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

import streamlit as st


# =====================================================
# CONFIGURAÇÕES
# =====================================================

st.set_page_config(
    page_title="Aniversário de contrato",
    page_icon="📄",
    layout="centered"
)


# =====================================================
# FUNÇÕES AUXILIARES
# =====================================================

def converter_decimal(valor):
    """Converte números com vírgula decimal para Decimal."""
    valor = valor.strip().replace("R$", "").replace(" ", "")

    if not valor:
        raise ValueError("Preencha o campo.")

    # Aceita formatos como 6,9588 ou 1.234,5678.
    if "," in valor:
        valor = valor.replace(".", "").replace(",", ".")

    return Decimal(valor)


def formatar_decimal(valor, casas=4):
    """Formata número com vírgula decimal e casas definidas."""
    quantizacao = Decimal("1").scaleb(-casas)
    valor = valor.quantize(
        quantizacao,
        rounding=ROUND_HALF_UP
    )

    parte_inteira, parte_decimal = f"{valor:.{casas}f}".split(".")
    parte_inteira = f"{int(parte_inteira):,}".replace(",", ".")

    return f"{parte_inteira},{parte_decimal}"


def formatar_ipca(valor):
    """Formata o percentual com duas casas decimais."""
    return f"{valor.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):.2f}".replace(".", ",") + "%"


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

ipca = st.text_input(
    "IPCA acumulado em 12 meses (%)",
    value="4,58",
    help="Informe o índice acumulado publicado pelo IBGE."
)

preco_anterior = st.text_input(
    "Preço Anterior (R$)",
    value="6,9588",
    help="Informe o preço atual antes da aplicação do reajuste."
)

ci = st.text_input(
    "CI (preenchimento manual)",
    placeholder="Digite o número do CI"
)


# =====================================================
# GERAÇÃO DO TEXTO
# =====================================================

if st.button("Calcular reajuste e gerar texto", type="primary"):

    try:
        ipca_numero = converter_decimal(ipca)
        preco_numero = converter_decimal(preco_anterior)

        if not Decimal("0") <= ipca_numero <= Decimal("100"):
            raise ValueError(
                "O IPCA deve estar entre 0% e 100%."
            )

        if preco_numero <= 0:
            raise ValueError(
                "O preço anterior deve ser maior que zero."
            )

        # Calcula o preço reajustado e arredonda para 4 casas.
        preco_negociado = (
            preco_numero * (Decimal("1") + ipca_numero / Decimal("100"))
        ).quantize(
            Decimal("0.0001"),
            rounding=ROUND_HALF_UP
        )

        ipca_formatado = formatar_ipca(ipca_numero)
        anterior_formatado = formatar_decimal(preco_numero)
        negociado_formatado = formatar_decimal(preco_negociado)

        ci_formatado = (
            ci.strip()
            if ci.strip()
            else "____________________"
        )

        # Texto padrão preservado.
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

        st.success("Reajuste calculado com sucesso.")

        st.subheader("Resultado do cálculo")

        col1, col2 = st.columns(2)

        col1.metric(
            "Preço anterior",
            f"R$ {anterior_formatado}"
        )

        col2.metric(
            "Preço negociado",
            f"R$ {negociado_formatado}"
        )

        st.caption(
            f"Reajuste aplicado: {ipca_formatado}"
        )

        st.subheader("Texto padrão gerado")

        st.text_area(
            "Texto pronto para copiar",
            value=texto_final,
            height=250
        )

        st.download_button(
            label="Baixar texto em TXT",
            data=texto_final,
            file_name="aniversario_contrato.txt",
            mime="text/plain"
        )

    except (ValueError, InvalidOperation):
        st.error(
            "Confira os valores informados. "
            "Utilize, por exemplo, IPCA 4,58 e preço 6,9588."
        )
