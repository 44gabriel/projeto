import streamlit as st
import requests
import pandas as pd
import numpy as np
import io
import plotly.express as px
from config import *
import plotly.graph_objects as go

st.set_page_config(
    page_title="Conecta Cargo",
    page_icon=":truck:",
    layout="wide",
)

st.title('Monitor Geração a Faturamento :truck:')

def classify_aging(date):
    aging_days = (pd.Timestamp.now() - date).days
    if aging_days == 0:
        return "24h"
    elif 1 <= aging_days <= 2:
        return "1 a 2 dias"
    elif 3 <= aging_days <= 5:
        return "3 a 5 dias"
    elif 6 <= aging_days <= 10:
        return "6 a 10 dias"
    elif 11 <= aging_days <= 15:
        return "11 a 15 dias"
    elif 16 <= aging_days <= 20:
        return "16 a 20 dias"
    elif 21 <= aging_days <= 24:
        return "21 a 24 dias"
    elif 25 <= aging_days <= 30:
        return "25 a 30 dias"
    elif 31 <= aging_days <= 60:
        return "31 a 60 dias"
    elif aging_days > 60:
        return "> 60 dias"
    else:
        return "> 30 dias"

# Função que define o cliente com base no CNPJ
def define_clientes_df(df_base: pd.DataFrame, clientes: list):
    df_base['Pagador do frete/Documento'] = df_base['Pagador do frete/Documento'].fillna('').astype(str)
    df_base['Cliente'] = ''
    
    for cliente in clientes:
        df_base['Cliente'] = np.where(
            df_base['Pagador do frete/Documento'].str.startswith(cliente['raiz_cnpj']),
            cliente['nome'], df_base['Cliente']
        )
    
    df_base['Cliente'] = np.where(
        (
            df_base['Cliente'].str.startswith('MULTI B2C')
        ) & (
            df_base['Frete/N° Referência'].str.contains('B2B', na=False)
        ), 'MULTI B2B', df_base['Cliente']
    )
    
    df_base['Cliente'] = np.where(df_base['Cliente'] == '', 'OUTROS', df_base['Cliente'])
    
    return df_base

# Carregar dados em cache
@st.cache_data
def load_data():
    return pd.read_excel('https://rpa.devinectar.com.br/scripts/pre_grade/relatorios_base/agendamento-2023-FULL_2024_10_29_14_52.xlsx')

dados = load_data()

# Definir clientes com base em CNPJ
dados = define_clientes_df(dados, clientes)

# Tratamento de datas
date_columns = [
    'Data do frete', 'Previsão Coleta', 'Data Finalização Performance', 
    'Data Coleta', 'Data Última Tratativa', 'Data Última Ocorrência', 
    'Previsão de Entrega'
]
for col in date_columns:
    dados[col] = pd.to_datetime(dados[col], format='%d/%m/%Y', errors='coerce')

# Adicionar coluna de aging
dados['Aging'] = dados['Data do frete'].apply(classify_aging)

# Sidebar com filtros
st.sidebar.title('Filtros')

# Opção para selecionar todos os clientes
clientes_opcoes = ['Todos os Clientes'] + list(dados['Cliente'].unique())
embarcador_multi = st.sidebar.selectbox('Cliente', clientes_opcoes)

ano_checkbox = st.sidebar.checkbox('Mostrar todos os anos', value=True)
ano = '' if ano_checkbox else st.sidebar.selectbox('Ano', [2022, 2023, 2024])

meses = ['Todos os Meses', 'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 
         'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
mes_selecionado = st.sidebar.selectbox('Mês', meses)

# Filtro de Aging
aging_opcoes = ['Todos'] + list(dados['Aging'].unique())
aging_selecionado = st.sidebar.selectbox('Aging', aging_opcoes)

# Filtrar os dados com base no cliente selecionado, ano (se aplicável) e aging
dados_filtrados = dados.copy()

if embarcador_multi != 'Todos os Clientes':
    dados_filtrados = dados_filtrados[dados_filtrados['Cliente'] == embarcador_multi]

if mes_selecionado != 'Todos os Meses':
    mes_numero = meses.index(mes_selecionado)  # Pega o índice que corresponde ao mês
    dados_filtrados = dados_filtrados[dados_filtrados['Data do frete'].dt.month == mes_numero]

if ano:
    dados_filtrados = dados_filtrados[dados_filtrados['Data do frete'].dt.year == ano]

if aging_selecionado != 'Todos':
    dados_filtrados = dados_filtrados[dados_filtrados['Aging'] == aging_selecionado]

# Exibir as colunas disponíveis para seleção
st.write("Colunas disponíveis:")
columns = dados.columns.tolist()
selected_columns = st.multiselect("Escolha as colunas para exibir", columns)

# Exibir a tabela com as colunas selecionadas
if selected_columns:
    st.write("Dados do arquivo Excel (colunas selecionadas):")
    st.dataframe(dados_filtrados[selected_columns])
else:
    st.write("Selecione pelo menos uma coluna para exibir.")
