
import re
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
# CABEÇALHO
# =====================================================

st.title("Aniversário de contrato")

st.write(
    "Informe o IPCA acumulado em 12 meses, conforme "
    "publicado pelo IBGE. O texto será gerado no "
    "padrão definido."
)

st.markdown(
    "[Consultar IPCA oficial no IBGE]"
    "(https://www.ibge.gov.br/explica/inflacao.php)"
)

st.caption(
    "Use como referência o campo 'IPCA acumulado de 12 meses'. "
    "Exemplo: 4,58% — Set/2026."
)


# =====================================================
# CAMPOS PARA PREENCHIMENTO
# =====================================================

st.subheader("Dados do comunicado")

ipca = st.text_input(
    "IPCA acumulado em 12 meses (%)",
    placeholder="Ex.: 4,58"
)

ci = st.text_input(
    "CI (preenchimento manual)",
    placeholder="Digite o número do CI"
)


# =====================================================
# VALIDAÇÃO E GERAÇÃO DO TEXTO
# =====================================================

if st.button("Gerar texto padrão", type="primary"):

    ipca_limpo = ipca.strip().replace("%", "").replace(",", ".")

    if not ipca_limpo:
        st.error("Informe o percentual do IPCA.")

    elif not re.fullmatch(r"\d{1,2}(?:\.\d{1,2})?", ipca_limpo):
        st.error(
            "Percentual inválido. Digite, por exemplo, 4,58."
        )

    elif not 0 <= float(ipca_limpo) <= 100:
        st.error("Informe um percentual entre 0 e 100.")

    else:
        # Padroniza o percentual com vírgula decimal.
        ipca_formatado = f"{float(ipca_limpo):.2f}".replace(".", ",") + "%"

        # Se o CI ficar vazio, mantém uma lacuna manual.
        ci_formatado = ci.strip() if ci.strip() else "____________________"

        # TEXTO PADRÃO: manter redação, preços e estrutura.
        texto_final = (
            "Aniversário de contrato\n"
            "\n"
            "Reajuste de preço devido aniversário de contrato.\n"
            f"IPCA do mês em {ipca_formatado}\n"
            "\n"
            "Preço Anterior: R$ 6,9588\n"
            "Preço Negociado: R$ 7,2789 \n"
            "\n"
            f"CI -  {ci_formatado} - Preço"
        )

        st.subheader("Texto gerado")

        # Exibe o texto sem aplicar formatação Markdown.
        st.text_area(
            "Selecione e copie o texto abaixo, se necessário:",
            value=texto_final,
            height=250
        )

        st.download_button(
            label="Baixar texto em TXT",
            data=texto_final,
            file_name="aniversario_contrato.txt",
            mime="text/plain"
        )

        st.success("Texto gerado com sucesso.")
