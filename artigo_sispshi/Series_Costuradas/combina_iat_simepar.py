import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt
import datetime as dt
import pytz
import json
import psycopg2, psycopg2.extras


lista = []

postos_vazao = {
                'Rio_Negro':'26064948',
                'Porto_Amazonas':'25334953',
                'Pontilhao':'25555031',
                'Santa_Cruz_Timbo':'26125049',
                'Sao_Mateus_Sul':'25525023',
                'Fluviopolis':'26025035',
                #'Uniao_da_Vitoria':'26145104',
            }


## COLETA DADOS VAZAO

posto_nome = 'Porto_Amazonas'

#for posto_nome, posto_codigo in postos_vazao.items():
print('Iniciando',posto_nome)
t_ini = dt.datetime(1935, 1, 1,  0,  0) #AAAA, M, D, H, Min
t_fim = dt.datetime(2021, 1, 1,  0,  0)

# cria DFs padrão de data
date_rng_diario = pd.date_range(start=t_ini, end=t_fim, freq='D')
df = pd.DataFrame(date_rng_diario, columns=['data'])
df['data']= pd.to_datetime(df['data'])
df = df.set_index('data')
df

simepar = pd.read_csv(f'{posto_nome}_diario.csv', parse_dates=True, index_col=0)
simepar.columns = ['telemetrica']
simepar

df = pd.concat([df, simepar], axis=1)
df

iat = pd.read_csv(f'VazoesFluviometricas_{posto_nome}.txt',
                  delimiter='\s+', header = None, decimal=',')
iat.columns = ['Codigo', 'Ano', 'Mes', 'Dia', 'Hora', 'Minuto', 'Cota', 'Vazao']
iat.index = pd.to_datetime(dict(year=iat.Ano, month=iat.Mes, day=iat.Dia))
iat['convencional'] = iat['Vazao'].str.replace(',', '.')
iat['convencional'] = pd.to_numeric(iat['convencional'], errors='coerce')
iat['convencional'].isna().sum()

df = pd.concat([df, iat['convencional']], axis=1)
df['vazao'] = np.where((df.index < '2000'), df['convencional'], df['telemetrica'])

df['vazao'] = df['vazao'].interpolate(method='spline', order=3)
df.to_csv(f'./Series_Costuradas/{posto_nome}_diario.csv')
