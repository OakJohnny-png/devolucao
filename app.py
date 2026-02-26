import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Entrada de Materiais", layout="wide")

# --- FUNÇÕES DE CARREGAMENTO ---
@st.cache_data
def carregar_dados(file):
    return pd.read_excel(file)

st.title("📦 Sistema de Entrada de Estoque")

# 1. Upload do arquivo mestre (Base de Produtos)
uploaded_file = st.sidebar.file_uploader("Carregue a base de produtos (Excel)", type=["xlsx"])

if uploaded_file:
    df_produtos = carregar_dados(uploaded_file)
    
    # Inicializar o estado da sessão para guardar as entradas
    if 'lista_entrada' not in st.session_state:
        st.session_state.lista_entrada = pd.DataFrame(columns=['Código', 'Localização', 'Descrição', 'Quantidade'])

    # --- FORMULÁRIO DE ENTRADA ---
    with st.expander("➕ Adicionar Novo Item", expanded=True):
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            # Busca por Código ou Descrição
            opcoes = df_produtos['Código'].astype(str) + " - " + df_produtos['Descrição']
            selecao = st.selectbox("Selecione o Produto", options=[""] + list(opcoes))
        
        with col2:
            quantidade = st.number_input("Quantidade", min_value=1, step=1)
            
        with col3:
            st.write("##")
            botao_adicionar = st.button("Adicionar à Lista")

    if botao_adicionar and selecao != "":
        # Extrair o código da seleção
        codigo_sel = selecao.split(" - ")[0]
        
        # Buscar dados do produto na base original
        info_produto = df_produtos[df_produtos['Código'].astype(str) == codigo_sel].iloc[0]
        
        # Criar nova linha
        nova_linha = {
            'Código': info_produto['Código'],
            'Localização': info_produto['Localização'],
            'Descrição': info_produto['Descrição'],
            'Quantidade': quantidade
        }
        
        # Adicionar ao DataFrame da sessão
        st.session_state.lista_entrada = pd.concat([st.session_state.lista_entrada, pd.DataFrame([nova_linha])], ignore_index=True)
        st.success(f"Item {codigo_sel} adicionado!")

    # --- EXIBIÇÃO E RELATÓRIO ---
    if not st.session_state.lista_entrada.empty:
        st.subheader("📋 Itens na Fila de Entrada")
        
        # Agrupar os itens para somar quantidades repetidas
        df_final = st.session_state.lista_entrada.groupby(['Código', 'Localização', 'Descrição'], as_index=False)['Quantidade'].sum()
        
        st.table(df_final)

        # Botão para Limpar Lista
        if st.button("Limpar Tudo"):
            st.session_state.lista_entrada = pd.DataFrame(columns=['Código', 'Localização', 'Descrição', 'Quantidade'])
            st.rerun()

        # Gerar Excel para Download
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_final.to_excel(writer, index=False, sheet_name='Entrada')
        
        st.download_button(
            label="📥 Gerar Relatório Final (Excel)",
            data=output.getvalue(),
            file_name="relatorio_entrada_estoque.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
else:
    st.info("Por favor, carregue o arquivo Excel de produtos na barra lateral para começar.")
