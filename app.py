import streamlit as st
import pandas as pd
import pdfplumber
import re
from io import BytesIO

st.set_page_config(page_title="Entrada de Materiais & EPIs", layout="wide")

# --- FUNÇÕES DE PROCESSAMENTO ---

def preparar_dataframe(df):
    df.columns = [str(col).strip() for col in df.columns]
    mapeamento = {}
    for col in df.columns:
        if col.lower() in ['código', 'codigo', 'cod', 'item']:
            mapeamento[col] = 'Código'
        elif col.lower() in ['descrição', 'descricao', 'produto']:
            mapeamento[col] = 'Descrição'
        elif col.lower() in ['localização', 'localizacao', 'local']:
            mapeamento[col] = 'Localização'
    return df.rename(columns=mapeamento)

def extrair_dados_pdf(pdf_file):
    itens_extraidos = []
    with pdfplumber.open(pdf_file) as pdf:
        texto_completo = ""
        for page in pdf.pages:
            texto_completo += page.extract_text()
        
        # Expressão regular para capturar o padrão do seu PDF:
        # Seq(01) -> Código(40939) -> Descrição(...) -> Un(PC/RL) -> Qtd(1,00)
        # O padrão busca: Sequencial, Código (5+ dígitos), Texto da descrição, Unidade, Quantidade
        padrao = re.compile(r'(\d{2})\s+(\d{5,})\s+(.*?)\s+(PC|RL|UN|KG)\s+([\d.,]+)')
        
        for match in padrao.finditer(texto_completo):
            itens_extraidos.append({
                'Código': match.group(2),
                'Descrição': match.group(3).strip(),
                'Localização': 'N/A', # PDF não costuma ter localização
                'Quantidade': float(match.group(5).replace(',', '.'))
            })
    return itens_extraidos

# --- INTERFACE ---

st.title("📦 Sistema de Entrada de Estoque")

# Sidebar para arquivos base
with st.sidebar:
    st.header("Configurações")
    uploaded_base = st.file_uploader("1. Carregue a base Excel (Produtos)", type=["xlsx"])
    st.divider()
    uploaded_pdf = st.file_uploader("2. Importar de PDF (EPIs)", type=["pdf"])

if 'lista_entrada' not in st.session_state:
    st.session_state.lista_entrada = []

# Processar PDF se enviado
if uploaded_pdf:
    if st.sidebar.button("Processar PDF"):
        novos_itens = extrair_dados_pdf(uploaded_pdf)
        if novos_itens:
            st.session_state.lista_entrada.extend(novos_itens)
            st.success(f"{len(novos_itens)} itens importados do PDF!")
        else:
            st.error("Não foi possível encontrar itens no padrão esperado dentro do PDF.")

# Lógica principal se tiver o Excel base
if uploaded_base:
    df_produtos = preparar_dataframe(pd.read_excel(uploaded_base))
    
    with st.container(border=True):
        st.subheader("➕ Entrada Manual")
        col1, col2 = st.columns([3, 1])
        with col1:
            df_produtos['Display'] = df_produtos['Código'].astype(str) + " - " + df_produtos['Descrição']
            selecao = st.selectbox("Busque o Produto", options=[""] + df_produtos['Display'].tolist())
        with col2:
            qtd_manual = st.number_input("Qtd", min_value=1.0, value=1.0, step=1.0)
        
        if st.button("Adicionar Manualmente"):
            if selecao:
                cod = selecao.split(" - ")[0]
                linha = df_produtos[df_produtos['Código'].astype(str) == cod].iloc[0]
                st.session_state.lista_entrada.append({
                    'Código': linha['Código'],
                    'Localização': linha['Localização'],
                    'Descrição': linha['Descrição'],
                    'Quantidade': qtd_manual
                })
                st.rerun()

    # Exibição dos dados acumulados
    if st.session_state.lista_entrada:
        df_temp = pd.DataFrame(st.session_state.lista_entrada)
        # Agrupar e somar quantidades
        df_final = df_temp.groupby(['Código', 'Localização', 'Descrição'], as_index=False)['Quantidade'].sum()
        
        st.subheader("📋 Relatório Consolidado")
        st.dataframe(df_final, use_container_width=True)

        c1, c2 = st.columns(2)
        with c1:
            if st.button("🗑️ Limpar Lista"):
                st.session_state.lista_entrada = []
                st.rerun()
        with c2:
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_final.to_excel(writer, index=False)
            st.download_button("📥 Baixar Excel Final", output.getvalue(), "entrada_estoque.xlsx", type="primary")
else:
    st.info("Por favor, carregue o arquivo Excel de produtos para habilitar a entrada manual.")
