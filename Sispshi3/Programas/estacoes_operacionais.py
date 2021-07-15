import numpy as np
import pandas as pd
import datetime as dt
import csv
import psycopg2, psycopg2.extras
import requests
import xmltodict

def coleta_simepar(t_ini,t_fim,posto_codigo,sensores):
        # Montagem do texto
    t_ini_string = t_ini.strftime('%Y-%m-%d %H:%M')
    t_fim_string = t_fim.strftime('%Y-%m-%d %H:%M')
    texto_psql = "select hordatahora at time zone 'UTC' as hordatahora, \
                  horleitura, horsensor \
                  from horaria where hordatahora >= '{}' and hordatahora <= '{}' \
                  and horestacao in ({}) \
                  and horsensor in {} \
                  order by horestacao, horsensor, hordatahora; \
                  ".format(t_ini_string, t_fim_string, posto_codigo,sensores)
    # Execução da consulta no banco do Simepar
    conn = psycopg2.connect(dbname='clim', user='hidro', password='hidrologia',
                            host='tornado', port='5432')
    consulta = conn.cursor(cursor_factory = psycopg2.extras.DictCursor)
    consulta.execute(texto_psql)
    consulta_lista = consulta.fetchall()
    df_consulta =pd.DataFrame(consulta_lista,columns=['tempo','valor','sensor'])
    df_consulta.set_index('tempo', inplace=True)
    return df_consulta

def coleta_ana(codEstacao, dataInicio, dataFim):
    url = 'http://telemetriaws1.ana.gov.br//ServiceANA.asmx/DadosHidrometeorologicos'
    params = dict(codEstacao=codEstacao, dataInicio=dataInicio, dataFim=dataFim)
    response = requests.get(url, params=params)
    decoded = response.content.decode('utf-8')
    dados_dicio = xmltodict.parse(decoded)
    try:
        dados_lista = dados_dicio['DataTable']['diffgr:diffgram']['DocumentElement']['DadosHidrometereologicos']
        df = pd.DataFrame(dados_lista)
        df.set_index('DataHora', inplace=True)
    except:
        df = pd.DataFrame(columns=['Chuva'])
        df.index.name = 'DataHora'
    return df

lista_simepar = pd.read_csv('../Dados/selecao_1_simepar.csv')
lista_ana = pd.read_csv('../Dados/selecao_3_ana.csv')
operacionais = pd.DataFrame()

# ##COLETA DADOS PRECIPITACAO SIMEPAR
# for index, posto in lista_simepar.iterrows():
#     posto_codigo = posto['estcodigo']
#     posto_nome = posto['estnome']
#     posto_banco = posto['orgsigla']
#     posto_x = posto['estlongitude']
#     posto_y = posto['estlatitude']
#     posto_z = posto['estaltitude']
#
#     ########## SERIES 15 MIN ##########
#     #print('Coletando dados brutos',posto_nome)
#     t_ini = dt.datetime.utcnow() - dt.timedelta(days = 1)
#     t_fim = dt.datetime.utcnow()
#     # t_ini = dt.datetime(1997, 1, 1,  0,  0) #AAAA, M, D, H, Min
#     # t_fim = dt.datetime(2021, 7, 4, 0, 0)
#
#     #coleta dados de precipitacao
#     dados = coleta_simepar(t_ini,t_fim, posto_codigo, '(7)')
#     dados.columns = ['chuva_mm', 'sensor']
#     dados = dados[['chuva_mm']]
#     if dados.empty:
#         print(f'{posto_nome} não operacional')
#         continue
#     else:
#         operacionais = operacionais.append(posto)


for index, posto in lista_ana.iterrows():
    posto_codigo = int(posto['CodEstacao'])
    posto_nome = posto['NomeEstacao']
    t_ini = dt.datetime.utcnow() - dt.timedelta(days = 1)
    t_fim = dt.datetime.utcnow()
    #coleta dados de precipitacao
    dados = coleta_ana(posto_codigo, t_ini, t_fim)
    dados = dados[['Chuva']]
    if dados.empty:
        print(f'{posto_nome} não operacional')
        continue
    else:
        operacionais = operacionais.append(posto)

# df = coleta_ana(65310001,t_ini, t_fim)
# df[['Chuva']]

operacionais

lista_ana
#operacionais.to_csv('../Dados/selecao_4_ana.csv')
# #
# operacionais['Operadora'].value_counts()

lista_simepar1 = pd.read_csv('../Dados/selecao_1_simepar.csv')
lista_simepar1
lista_simepar1['orgsigla'].value_counts()
lista_simepar1[lista_simepar1['orgsigla'] == 'PCH Cavernoso II'].sort_values(by=['estnome'])

dataInicio = dt.datetime.utcnow() - dt.timedelta(days = 1)
dataFim = dt.datetime.utcnow()
for estacao in lista_ana['CodEstacao']:
    codEstacao = int(estacao)
    url = 'http://telemetriaws1.ana.gov.br//ServiceANA.asmx/DadosHidrometeorologicos'
    params = dict(codEstacao=codEstacao, dataInicio=dataInicio, dataFim=dataFim)
    response = requests.get(url, params=params)
    decoded = response.content.decode('utf-8')
    dados_dicio = xmltodict.parse(decoded)
    dados_lista = dados_dicio['DataTable']['diffgr:diffgram']['DocumentElement']['DadosHidrometereologicos']
    df = pd.DataFrame(dados_lista)
    df.set_index('DataHora', inplace=True)
estacao

codEstacao = 64619000
url = 'http://telemetriaws1.ana.gov.br//ServiceANA.asmx/DadosHidrometeorologicos'
params = dict(codEstacao=codEstacao, dataInicio=dataInicio, dataFim=dataFim)
response = requests.get(url, params=params)
decoded = response.content.decode('utf-8')
dados_dicio = xmltodict.parse(decoded)
try:
    dados_lista = dados_dicio['DataTable']['diffgr:diffgram']['DocumentElement']['DadosHidrometereologicos']
    df = pd.DataFrame(dados_lista)
    df.set_index('DataHora', inplace=True)
except:
    df = pd.DataFrame()
    df.index.name = 'DataHora'
df = pd.DataFrame(columns=['Chuva'])
df.index.name = 'DataHora'
df

ana = pd.read_csv('../Dados/postos_def_ana.csv')
simepar = pd.read_csv('../Dados/postos_def_simepar.csv')
df = pd.concat([simepar,ana])
df.to_csv('../Dados/postos_def.csv', index=False)
df2 = pd.read_csv('../Dados/postos_def.csv')
df2
df2['codigo_snirh'] = pd.to_numeric(df2['codigo_snirh'], downcast='integer')
df2['codigo_snirh']
df2.to_csv('../Dados/postos_def.csv', index=False)

datas = pd.read_csv('../Dados/inicio_serie_postos.csv', parse_dates=True)

datas['inicio_serie'] = pd.to_datetime(datas['inicio_serie'])
datas

len(datas.loc[datas['inicio_serie']<='2021'])
