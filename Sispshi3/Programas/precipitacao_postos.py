import numpy as np
import pandas as pd
import datetime as dt
import csv
import psycopg2, psycopg2.extras
import requests
import xmltodict


def coletar_dados(t_ini,t_fim,posto_codigo,sensores):
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
    dados_lista = dados_dicio['DataTable']['diffgr:diffgram']['DocumentElement']['DadosHidrometereologicos']
    df = pd.DataFrame(dados_lista)
    df.set_index('DataHora', inplace=True)
    return df



postos_precip = pd.read_csv('../Dados/postos_def.csv')
postos_precip
hora_att = open('../Dados/disparo.txt')
data_ant = hora_att.readline().strip()
disparo = hora_att.readline().strip()
hora_att.close()

t_fim = dt.datetime.strptime(disparo, '%Y-%m-%d %H:%M:%S%z')
t_ini = t_fim - dt.timedelta(days=3)

postos_precip
posto = postos_precip.loc[44]
posto

# Teste - UVA
t_fim = dt.datetime(2021,6,28, tzinfo=dt.timezone.utc)
t_ini = dt.datetime(2021,6,27, tzinfo=dt.timezone.utc)
df = coleta_ana(99999999, t_ini, t_fim)
df = df[['Chuva']]
df.columns = ['chuva_mm']
#Localiza dados em BRT e converte para UTC, no formato padrao
df.index = pd.to_datetime(df.index).tz_localize('America/Sao_Paulo').rename('datahora')
df.index = df.index.tz_convert('utc')
df["chuva_mm"] = pd.to_numeric(df["chuva_mm"], downcast = "float")
df = df.sort_index()


#for index, posto in postos_precip.iterrows():
## COLETA DADOS PRECIPITACAO
idPosto = posto['idPosto']
posto_codigo = posto['codigo_simepar']
posto_snirh = posto['codigo_snirh']
posto_nome = posto['nome']
posto_banco = posto['banco']
posto_x = posto['x']
posto_y = posto['y']
posto_z = posto['z']



#Coleta dados de precipitacao
dados = coletar_dados(t_ini,t_fim, posto_codigo, '(7)')
dados.columns = ['chuva_mm', 'sensor']
dados = dados[['chuva_mm']]

#Converte indice para formato padrao
dados.index = pd.to_datetime(dados.index, utc=True).rename('datahora')
dados["chuva_mm"] = pd.to_numeric(dados["chuva_mm"], downcast = "float")
dados


#Remove valores registrados como negativos na serie bruta
dados['chuva_mm'] = np.where((dados['chuva_mm'] < 0), np.nan, dados['chuva_mm'])

#Agrupa em serie horaria, com intervalo fechado à direita (acumulado 0:01 a 1:00)
dados_hor = (dados.resample("H", closed='right', label='right').agg({'chuva_mm' : np.sum}))

#Remove a ocorrencia de valores horarios superiores a 90mm
dados_hor['chuva_mm'] = np.where((dados_hor['chuva_mm'] > 90), np.nan, dados_hor['chuva_mm'])

#Cria DF padrao horario para ser preenchido
date_rng_horario = pd.date_range(start=t_ini, end=t_fim, freq='H', closed='right')
table_hor = pd.DataFrame(date_rng_horario, columns=['date'])
table_hor['datahora']= pd.to_datetime(table_hor['date'])
table_hor = table_hor.set_index('datahora')
table_hor = table_hor[[]]


#Unifica dados horarios no DF padrao
table_hor = pd.merge(table_hor, dados_hor, left_index = True,
                     right_index = True, how = 'left')
table_hor = table_hor[~table_hor.index.duplicated(keep='first')]


table_hor



#exporta dados horarios para csv
with open(f'../Dados/Chuva/Estacoes_Operacionais/{idPosto}.csv','w',newline='') as file:
    writer = csv.writer(file)
    writer.writerow([posto_snirh])
    writer.writerow([posto_nome])
    writer.writerow([posto_x, posto_y, posto_z])
table_hor.to_csv(f'../Dados/Chuva/Estacoes_Operacionais/{idPosto}.csv',
                 mode = 'a', sep = ",", float_format='%.2f')

#Estacoes com falha nos dados
if dados.empty:
    print(f'{index+1}/{len(postos_precip)} - {posto_nome} - FALHA NA TELEMETRIA')
else:
    if table_hor['chuva_mm'].last_valid_index() == t_fim:
        print(f'{index+1}/{len(postos_precip)} - {posto_nome} - Coleta efetuada sem falhas')
    else:
        print(f'{index+1}/{len(postos_precip)} - {posto_nome} - Coleta efetuada até', table_hor['chuva_mm'].last_valid_index())

print(table_hor['chuva_mm'].last_valid_index())

#Le serie historica antiga para grade
chuva_hist = pd.read_csv('../Dados/Chuva/chuva_grade.csv', index_col='datahora',
                         parse_dates=True)
chuva_hist
