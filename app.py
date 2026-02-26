
import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Entrada de Materiais", layout="wide")

# --- FUNÇÃO DE NORMALIZAÇÃO DE COLUNAS ---
def preparar_dataframe(df):
    # Remove espaços em branco dos nomes das colunas
    df.columns = [str(col).strip() for col in df.columns]
    
    # Dicionário para mapear as colunas encontradas para o padrão esperado
    mapeamento = {}
    for col in df.columns:
        if col.lower() in ['código', 'codigo', 'cod']:
            mapeamento[col] = 'Código'
        elif col.lower() in ['descrição', 'descricao', 'produto', 'item']:
            mapeamento[col] = 'Descrição'
        elif col.lower() in ['localização', 'localizacao', 'local']:
            mapeamento[col] = 'Localização'
    
    return df.rename(columns=mapeamento)

st.title("📦 Sistema de Entrada de Estoque")

uploaded_file = st.sidebar.file_uploader("1. Carregue a base de produtos (Excel)", type=["xlsx"])

if uploaded_file:
    # Carrega e normaliza o arquivo
    df_bruto = pd.read_excel(uploaded_file)
    df_produtos = preparar_dataframe(df_bruto)
    
    # Verifica se as 3 colunas vitais existem após a tentativa de mapeamento
    colunas_necessarias = ['Código', 'Descrição', 'Localização']
    colunas_faltando = [c for c in colunas_necessarias if c not in df_produtos.columns]

    if colunas_faltando:
        st.error(f"⚠️ Não encontramos as colunas: {', '.join(colunas_faltando)}")
        st.info(f"Colunas lidas no seu arquivo: {list(df_bruto.columns)}")
        st.stop()

    # Inicializa o carrinho de entradas
    if 'lista_entrada' not in st.session_state:
        st.session_state.lista_entrada = []

    # --- INTERFACE DE ENTRADA ---
    with st.container(border=True):
        st.subheader("➕ Nova Entrada")
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Opções combinando Código e Descrição para facilitar busca
            df_produtos['Display'] = df_produtos['Código'].astype(str) + " - " + df_produtos['Descrição']
            selecao = st.selectbox("Selecione o Produto", options=[""] + df_produtos['Display'].tolist())
        
        with col2:
            quantidade = st.number_input("Qtd", min_value=1, value=1, step=1)
        
        if st.button("Adicionar Item", use_container_width=True):
            if selecao:
                # Extrai o código da string selecionada
                codigo_extraido = selecao.split(" - ")[0]
                # Busca os dados originais
                linha = df_produtos[df_produtos['Código'].astype(str) == codigo_extraido].iloc[0]
                
                st.session_state.lista_entrada.append({
                    'Código': linha['Código'],
                    'Localização': linha['Localização'],
                    'Descrição': linha['Descrição'],
                    'Quantidade': quantidade
                })
                st.toast("Adicionado com sucesso!")
            else:
                st.warning("Selecione um produto primeiro.")

    # --- TABELA DE RESUMO E EXPORTAÇÃO ---
    if st.session_state.lista_entrada:
        st.divider()
        df_temp = pd.DataFrame(st.session_state.lista_entrada)
        
        # AGRUPAMENTO: Soma quantidades de itens iguais
        df_final = df_temp.groupby(['Código', 'Localização', 'Descrição'], as_index=False)['Quantidade'].sum()
        
        st.subheader("📋 Itens Registrados")
        st.dataframe(df_final, use_container_width=True)

        c1, c2 = st.columns(2)
        with c1:
            if st.button("🗑️ Limpar Tudo", type="secondary"):
                st.session_state.lista_entrada = []
                st.rerun()
        
        with c2:
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_final.to_excel(writer, index=False)
            
            st.download_button(
                label="📥 Baixar Relatório Final",
                data=output.getvalue(),
                file_name="relatorio_entrada.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary"
            )
else:
    st.info("💡 Para começar, carregue seu arquivo Excel na barra lateral.")
