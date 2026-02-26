import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Entrada de Materiais", layout="wide")

# --- FUNÇÕES DE CARREGAMENTO ---
@st.cache_data
def carregar_dados(file):
    df = pd.read_excel(file)
    # Remove espaços em branco antes/depois do nome das colunas e normaliza
    df.columns = df.columns.str.strip()
    return df

st.title("📦 Sistema de Entrada de Estoque")

# 1. Upload do arquivo mestre
uploaded_file = st.sidebar.file_uploader("Carregue a base de produtos (Excel)", type=["xlsx"])

if uploaded_file:
    df_produtos = carregar_dados(uploaded_file)
    
    # --- VERIFICAÇÃO DE SEGURANÇA ---
    # Verifica se as colunas esperadas existem (independente de maiúsculas/minúsculas)
    colunas_esperadas = ['Código', 'Localização', 'Descrição']
    colunas_reais = df_produtos.columns.tolist()
    
    # Se as colunas não forem encontradas exatamente, tentamos avisar o usuário
    if not all(col in colunas_reais for col in colunas_reais if col in colunas_esperadas):
        st.error(f"Erro: As colunas do seu Excel precisam ser: {colunas_esperadas}")
        st.info(f"Colunas detectadas no seu arquivo: {colunas_reais}")
        st.stop()

    if 'lista_entrada' not in st.session_state:
        st.session_state.lista_entrada = pd.DataFrame(columns=['Código', 'Localização', 'Descrição', 'Quantidade'])

    # --- FORMULÁRIO DE ENTRADA ---
    with st.expander("➕ Adicionar Novo Item", expanded=True):
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            # Criamos a lista de opções
            opcoes = df_produtos['Código'].astype(str) + " - " + df_produtos['Descrição']
            selecao = st.selectbox("Busque o Produto (Código ou Nome)", options=[""] + list(opcoes))
        
        with col2:
            quantidade = st.number_input("Quantidade", min_value=1, step=1)
            
        with col3:
            st.write("##")
            botao_adicionar = st.button("Adicionar à Lista")

    if botao_adicionar and selecao != "":
        codigo_sel = selecao.split(" - ")[0]
        
        # Filtra a linha correspondente
        info_produto = df_produtos[df_produtos['Código'].astype(str) == codigo_sel].iloc[0]
        
        nova_linha = {
            'Código': info_produto['Código'],
            'Localização': info_produto['Localização'],
            'Descrição': info_produto['Descrição'],
            'Quantidade': quantidade
        }
        
        st.session_state.lista_entrada = pd.concat([st.session_state.lista_entrada, pd.DataFrame([nova_linha])], ignore_index=True)
        st.toast(f"✅ Item {codigo_sel} adicionado!")

    # --- EXIBIÇÃO E RELATÓRIO ---
    if not st.session_state.lista_entrada.empty:
        st.divider()
        st.subheader("📋 Resumo da Entrada")
        
        # Agrupamento (Somatória de itens iguais)
        df_final = st.session_state.lista_entrada.groupby(['Código', 'Localização', 'Descrição'], as_index=False)['Quantidade'].sum()
        
        st.dataframe(df_final, use_container_width=True)

        col_limpar, col_baixar = st.columns(2)
        
        with col_limpar:
            if st.button("🗑️ Limpar Lista Atual"):
                st.session_state.lista_entrada = pd.DataFrame(columns=['Código', 'Localização', 'Descrição', 'Quantidade'])
                st.rerun()

        with col_baixar:
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_final.to_excel(writer, index=False)
            
            st.download_button(
                label="📥 Baixar Relatório (Excel)",
                data=output.getvalue(),
                file_name="entrada_estoque_final.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary"
            )
else:
    st.info("Aguardando carregamento do arquivo de produtos...")
