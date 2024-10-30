import streamlit as st
import requests 
import pandas as pd 
import numpy as np
import io
import plotly.express as px
from config import *
import plotly.graph_objects as go

# Defina o caminho da imagem
logo_path = 'dados/Logo Horizontal- Branca.png'  # Ajuste o caminho conforme necessário

st.set_page_config(
    page_title="Degradação",
    page_icon=":truck:",
    layout="wide",
)

# Sidebar logo tela
st.sidebar.image(logo_path, use_column_width=False, width=200)  # Ajusta o uso da largura da coluna

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

# Função que formata números
def formata_numero(valor, prefixo=''):
    for unidade in ['', 'mil']:
        if valor < 1000:
            return f'{prefixo} {valor:.2f} {unidade} '
        valor /= 1000
    return f'{prefixo} {valor:.2f} milhões'

col1, col2 = st.columns([3, 1])  # A primeira coluna é mais larga

with col1:
    st.title('Degradação')

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
    dados[col] = pd.to_datetime(dados[col], format='%d/%m/%Y')

# Adicionar coluna de aging
dados['Aging'] = dados['Data Última Ocorrência'].apply(classify_aging)


def regional(regional):
    if regional in regional_GRU:
        return 'Regional GRU'
    elif regional in regional_RJO:
        return 'Regional RJO'
    elif regional in regional_BHZ:
        return 'Regional BHZ'
    elif regional in regional_BR:
        return "Regional BR"

# Função que define a degradação com base na última ocorrência
def degradacao(ultima_ocorrencia):
    if ultima_ocorrencia in ocorrencias_agendamento_em_aberto:
        return 'Agendamento em Aberto'
    elif ultima_ocorrencia in aguardando_check_list:
        return 'Aguardando Check List'
    elif ultima_ocorrencia in cancelado_finalizado:
        return 'Cancelado/ Finalizado'
    elif ultima_ocorrencia in coleta_em_aberto:
        return 'Coleta em Aberto'
    elif ultima_ocorrencia in devolucao_em_aberto:
        return 'Devolução em Aberto'
    elif ultima_ocorrencia in devolvido:
        return 'Devolvido'
    elif ultima_ocorrencia in entrega_em_aberto:
        return 'Entrega em Aberto'
    elif ultima_ocorrencia in ocorrencias_insucesso_de_agendamento:
        return 'Insucesso de Agendamento'
    elif ultima_ocorrencia in correncia_insucesso_de_devolucao:
        return 'Insucesso de Devolução'
    elif ultima_ocorrencia in outros:
        return 'Outros'
    elif ultima_ocorrencia in pendecia:
        return 'Pendência'
    elif ultima_ocorrencia in ocorrencia_insucesso_de_coleta:
        return 'Insucesso de Coleta'
    else:
        return 'Desconhecido'

# Criação da coluna 'Degradação'
dados['Degradação'] = dados['Última Ocorrência'].apply(degradacao)
dados['Regional'] = dados['Agente de Coleta'].apply(regional)

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
aging_selecionado = st.sidebar.selectbox('Faixa Aging', aging_opcoes)

regional_opcoes = ['Todos'] + list(dados['Regional'].unique())
regional_selecionado = st.sidebar.selectbox('Regional',regional_opcoes)

# Filtro de degradação com opção de "Todos"
degradacao_tipo = ['Todos',  
                   'Agendamento em Aberto', 
                   'Aguardando Check List', 
                   'Cancelado/ Finalizado', 
                   'Coleta em Aberto',
                   'Devolução em Aberto',
                   'Devolvido',
                   'Entrega em Aberto',
                   'Insucesso de Agendamento',
                   'Insucesso de Devolução',
                   'Outros',
                   'Pendência',
                   'Insucesso de Coleta']

tipo_degradacao = st.sidebar.selectbox('Tipo Degradação', degradacao_tipo)

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

# Filtrar os dados com base no tipo de degradação
if tipo_degradacao != 'Todos':
    dados_filtrados = dados_filtrados[dados_filtrados['Degradação'] == tipo_degradacao]
    
if regional_selecionado != "Todos":
    dados_filtrados = dados_filtrados[dados_filtrados['Regional'] == regional_selecionado]

# Visualização no Streamlit
aba1, aba2, aba3, aba4, aba5, aba6, aba7, aba8, aba9, aba10 = st.tabs([
    'Em Aberto', 'Insucesso', 'Por Ocorrência', 'Por Agente', 
    'Data Coleta', '1ª Minuta', 'Relatório', 'STD', 'Pendência', 'Tentativas'
])

# Informações da aba "Em Aberto"
with aba1:
    
    dados_aba = dados_filtrados
    agendamentos = dados_aba[dados_aba['Última Ocorrência'].isin(ocorrencias_agendamento_em_aberto)]
    coletas = dados_aba[dados_aba['Última Ocorrência'].isin(ocorrencias_coleta_em_aberto)]
    devolucoes = dados_aba[dados_aba['Última Ocorrência'].isin(ocorrencia_devolucao_em_aberto)]
    
    coluna1, coluna2 = st.columns(2)

    with coluna1:
        st.metric(
            'Valor Agendamento em Aberto', 
            formata_numero(agendamentos['Nota Fiscal/Valor NF'].sum(), 'R$')
        )
    with coluna2:
        st.metric(
            'Agendamento em Aberto', 
            formata_numero(agendamentos.shape[0])
        )

    coluna3, coluna4 = st.columns(2)

    with coluna3:
        st.metric(
            'Valor Coleta em Aberto', 
            formata_numero(coletas['Nota Fiscal/Valor NF'].sum(), 'R$')
        )
    with coluna4:
        st.metric(
            'Coleta em Aberto', 
            formata_numero(coletas.shape[0])
        )

    coluna5, coluna6 = st.columns(2)

    with coluna5:
        st.metric(
            'Valor Devolução em Aberto', 
            formata_numero(devolucoes['Nota Fiscal/Valor NF'].sum(), 'R$')
        )
    with coluna6:
        st.metric(
            'Devolução em Aberto', 
            formata_numero(devolucoes.shape[0])
        )
        
    coluna7, coluna8, coluna9 = st.columns(3)
    
    with coluna7:
        count_aging = agendamentos['Aging'].value_counts()
       
        if not count_aging.empty:
            fig_bar = px.bar(x=count_aging.index, y=count_aging.values, title='Agendamento em Aberto')
            st.plotly_chart(fig_bar)
            fig = px.pie(names=count_aging.index, values=count_aging.values, title='Agendamento em Aberto')
            st.plotly_chart(fig)
        else:
             st.warning("Nenhum dado disponível para Agendamentos em Aberto.")

    with coluna8:
        count_aging = coletas['Aging'].value_counts()
          
        if not count_aging.empty:
            fig_bar = px.bar(x=count_aging.index, y=count_aging.values, title='Coleta em Aberto')
            st.plotly_chart(fig_bar)
            fig = px.pie(names=count_aging.index, values=count_aging.values, title='Coleta em Aberto')
            st.plotly_chart(fig)
        else:
           st.warning("Nenhum dado disponível para Coletas em Aberto.")
   
    with coluna9:
        count_aging = devolucoes['Aging'].value_counts()

        if not count_aging.empty:
            fig_bar = px.bar(x=count_aging.index, y=count_aging.values, title='Devolução em Aberto')
            st.plotly_chart(fig_bar)
            fig = px.pie(names=count_aging.index, values=count_aging.values, title='Devolução em Aberto')
            st.plotly_chart(fig)
        else:
            st.warning("Nenhum dado disponível para Devoluções em Aberto.")

# Informações da aba "Insucesso"
with aba2:
    dados_aba = dados_filtrados
    insucesso_agendamento = dados_aba[dados_aba['Última Ocorrência'].isin(ocorrencias_insucesso_de_agendamento)]
    insucesso_coleta = dados_aba[dados_aba['Última Ocorrência'].isin(ocorrencia_insucesso_de_coleta)]
    insuceso_devolucao = dados_aba[dados_aba['Última Ocorrência'].isin(correncia_insucesso_de_devolucao)]
    
    coluna_agendamento, coluna_coleta, coluna_devolucao = st.columns(3)

    with coluna_agendamento:
        st.metric(
            'Insucesso de Agendamento', 
            formata_numero(insucesso_agendamento.shape[0])
        )

    with coluna_coleta:
        st.metric(
            'Insucesso de Coleta', 
            formata_numero(insucesso_coleta.shape[0])
        )

    with coluna_devolucao:
        st.metric(
            'Insucesso de Devolução', 
            formata_numero(insuceso_devolucao.shape[0])
        )

    coluna10, coluna11, coluna12 = st.columns(3)
    
    with coluna10:
        count_aging = insucesso_agendamento['Aging'].value_counts()

        if not count_aging.empty:
            fig_bar = px.bar(x=count_aging.index, y=count_aging.values, title='Insucesso de Agendamento')
            st.plotly_chart(fig_bar)
            fig = px.pie(names=count_aging.index, values=count_aging.values, title='Insucesso de Agendamento')
            st.plotly_chart(fig)
        else:
            st.warning("Nenhum dado disponível para Insucesso de Agendamento.")
            
    with coluna11:
        count_aging = insucesso_coleta['Aging'].value_counts()

        if not count_aging.empty:
            fig_bar = px.bar(x=count_aging.index, y=count_aging.values, title='Insucesso de Coleta')
            st.plotly_chart(fig_bar)
            fig = px.pie(names=count_aging.index, values=count_aging.values, title='Insucesso de Coleta')
            st.plotly_chart(fig)
        else:
            st.warning("Nenhum dado disponível para Insucesso de Coleta.")
            
    with coluna12:
        count_aging = insuceso_devolucao['Aging'].value_counts()

        if not count_aging.empty:
            fig_bar = px.bar(x=count_aging.index, y=count_aging.values, title='Insucesso de Devolução')
            st.plotly_chart(fig_bar)
            fig = px.pie(names=count_aging.index, values=count_aging.values, title='Insucesso de Devolução')
            st.plotly_chart(fig)
        else:
            st.warning("Nenhum dado disponível para Insucesso de Devolução.")
with aba3:
    # Data Tratada
    dados['Data do frete'] = pd.to_datetime(dados['Data do frete'])
    dados['Data Última Ocorrência'] = pd.to_datetime(dados['Data Última Ocorrência'])
    dados['Data Coleta'] = pd.to_datetime(dados['Data Coleta'])
    dados['Data Checklist'] = pd.to_datetime(dados['Data Checklist'])
    dados['Data Última Tratativa'] = pd.to_datetime(dados['Data Última Tratativa'])
    dados['Data Finalização Performance'] = pd.to_datetime(dados['Data Finalização Performance'])
    dados['Nota Fiscal/Valor NF'] = dados['Nota Fiscal/Valor NF'].replace({'\$':'',',':''},regex=True).astype(float)

    # Data tratada
    dados_filtrados = dados.copy()
    dados_filtrados['Data Última Ocorrência'] = dados_filtrados['Data Última Ocorrência'].dt.strftime('%d/%m/%Y')
    dados_filtrados['Data do frete'] = dados_filtrados['Data do frete'].dt.strftime('%d/%m/%Y')
    dados_filtrados['Data Coleta'] = dados_filtrados['Data Coleta'].dt.strftime('%d/%m/%Y')
    dados_filtrados['Data Checklist'] = dados_filtrados['Data Checklist'].dt.strftime('%d/%m/%Y')
    dados_filtrados['Data Última Tratativa'] = dados_filtrados['Data Última Tratativa'].dt.strftime('%d/%m/%Y')
    dados_filtrados['Data Finalização Performance'] = dados_filtrados['Data Finalização Performance'].dt.strftime('%d/%m/%Y')
    dados_filtrados['Nota Fiscal/Valor NF'] = dados['Nota Fiscal/Valor NF'].replace({'\$':'',',':''},regex=True).astype(float)
    # Aplicar a formatação na coluna 'N° Minuta' em dados_filtrados
    if 'N° Minuta' in dados_filtrados.columns:
        dados_filtrados['N° Minuta'] = dados_filtrados['N° Minuta'].apply(lambda x: str(int(x)).replace(",", "") if pd.notna(x) and x != "" else "")
    
    # Verifique se as colunas 'Agente de Coleta', 'N° Minuta' e 'Aging' estão no DataFrame
    colunas_desejadas = []
    
    if 'Degradação' in dados.columns:
        colunas_desejadas.append('Degradação')
    
    if 'N° Minuta' in dados.columns:
        colunas_desejadas.append('N° Minuta')
    
    if 'Aging' in dados.columns:
        colunas_desejadas.append('Aging')
    
    if 'Nota Fiscal/Valor NF' in dados.columns:
        colunas_desejadas.append('Valor NF')
    
    if colunas_desejadas:
        df_agentes = dados_filtrados[colunas_desejadas]
          
        st.write("Tabela por Ocorrência:")
        st.dataframe(df_agentes) 
    else:
        st.warning("Nenhuma das colunas 'Agente de Coleta' ou 'Aging' está disponível no DataFrame.")


with aba4:
    # Verifique se as colunas 'Agente de Coleta' e 'Aging' estão no DataFrame
    colunas_desejadas = []
    
    if 'Agente de Coleta' in dados.columns:
        colunas_desejadas.append('Agente de Coleta')
    
    if 'N° Minuta' in dados.columns:
        # Aplicar a formatação na coluna 'N° Minuta'
        dados['N° Minuta'] = dados['N° Minuta'].apply(lambda x: str(int(x)).replace(",", "") if pd.notna(x) and x != "" else "")
        colunas_desejadas.append('N° Minuta')
    
    if 'Aging' in dados.columns:
        colunas_desejadas.append('Aging')

    if colunas_desejadas:
        df_agentes = dados[colunas_desejadas].drop_duplicates()  # Remove duplicatas, se necessário
        
        # Exibir a tabela com as colunas desejadas
        st.write("Tabela Agente de Coleta:")
        st.dataframe(df_agentes)  # Exibe o DataFrame de forma interativa
    else:
        st.warning("Nenhuma das colunas 'Agente de Coleta' ou 'Aging' está disponível no DataFrame.")

with aba5:
      # Data Tratada
    dados['Data do frete'] = pd.to_datetime(dados['Data do frete'])
    dados['Data Última Ocorrência'] = pd.to_datetime(dados['Data Última Ocorrência'])
    dados['Data Coleta'] = pd.to_datetime(dados['Data Coleta'])
    dados['Data Checklist'] = pd.to_datetime(dados['Data Checklist'])
    dados['Data Última Tratativa'] = pd.to_datetime(dados['Data Última Tratativa'])
    dados['Data Finalização Performance'] = pd.to_datetime(dados['Data Finalização Performance'])
    dados['Nota Fiscal/Valor NF'] = dados['Nota Fiscal/Valor NF'].replace({'\$':'',',':''},regex=True).astype(float)
    
    dados_filtrados = dados.copy()
    
    dados_filtrados['Data Última Ocorrência'] = dados_filtrados['Data Última Ocorrência'].dt.strftime('%d/%m/%Y')
    dados_filtrados['Data do frete'] = dados_filtrados['Data do frete'].dt.strftime('%d/%m/%Y')
    dados_filtrados['Data Coleta'] = dados_filtrados['Data Coleta'].dt.strftime('%d/%m/%Y')
    dados_filtrados['Data Checklist'] = dados_filtrados['Data Checklist'].dt.strftime('%d/%m/%Y')
    dados_filtrados['Data Última Tratativa'] = dados_filtrados['Data Última Tratativa'].dt.strftime('%d/%m/%Y')
    dados_filtrados['Data Finalização Performance'] = dados_filtrados['Data Finalização Performance'].dt.strftime('%d/%m/%Y')
    dados_filtrados['Nota Fiscal/Valor NF'] = dados['Nota Fiscal/Valor NF'].replace({'\$':'',',':''},regex=True).astype(float)
    
    colunas_desejadas = []
    
    if 'Data Coleta' in dados.columns:
        colunas_desejadas.append('Data Coleta')
        
    if colunas_desejadas:
        df_agentes = dados[colunas_desejadas].drop_duplicates()  # Remove duplicatas, se necessário
        
        # Exibir a tabela com as colunas desejadas
        st.write("Tabela Agente de Coleta:")
        st.dataframe(df_agentes)  # Exibe o DataFrame de forma interativa
    else:
        st.warning("Nenhuma das colunas 'Agente de Coleta' ou 'Aging' está disponível no DataFrame.")
    
with aba7:
    
     dados_aba = dados_filtrados
     agendamentos = dados_aba[dados_aba['Última Ocorrência'].isin(ocorrencias_agendamento_em_aberto)]
     coletas = dados_aba[dados_aba['Última Ocorrência'].isin(ocorrencias_coleta_em_aberto)]
     checklist = dados_aba[dados_aba['Última Ocorrência'].isin(aguardando_check_list)]
     insucesso_agendamento = dados_aba[dados_aba['Última Ocorrência'].isin(insucesso_agendamento)]
     coleta_em_aberto =  dados_aba[dados_aba['Última Ocorrência'].isin(coleta_em_aberto)]
     insucesso_coleta = dados_aba[dados_aba['Última Ocorrência'].isin(insucesso_coleta)]
     devolucao = dados_aba[dados_aba['Última Ocorrência'].isin(devolvido)]
     insuceso_devolucao = dados_aba[dados_aba['Última Ocorrência'].isin(correncia_insucesso_de_devolucao)]
     pendencia_em_aberto = dados_aba[dados_aba['Última Ocorrência'].isin(pendecia)]
     
   


     coluna13, coluna14, coluna15,coluna16 = st.columns(4)
     
     with coluna13:
         st.metric(
             'Aguardando Check List',
             formata_numero(checklist.shape[0])
         ) 
     
     with coluna14:
        st.metric(
            'Agendamento em Aberto', 
            formata_numero(agendamentos.shape[0])
        )
      
     with coluna15:
        st.metric(
            'Insucesso de Agendamento', 
            formata_numero(insucesso_agendamento.shape[0])
        )
      
     with coluna16:
        st.metric(
            'Coleta em Aberto', 
            formata_numero(coleta_em_aberto.shape[0])
        )
      
     coluna17, coluna18, coluna19,coluna20 = st.columns(4) 
     
     with coluna17:
         st.metric(
             'Insucesso de Coleta',
             formata_numero(insucesso_coleta.shape[0])
         )
     
     with coluna18:
         st.metric(
             'Devolução',
             formata_numero(devolucao.shape[0])
         )
     
      
     with coluna19:
         st.metric(
             'Insucesso de Devolução',
             formata_numero(insuceso_devolucao.shape[0])
         )
        
     
     with coluna20:
         st.metric(
             'Pendência em Aberto',
             formata_numero(insuceso_devolucao.shape[0])
         )
        