import numpy as np
import pandas as pd
import datetime as dt
import csv
import psycopg2, psycopg2.extras
import requests
import xmltodict

postos_flu = pd.read_csv('../Dados/postos_flu.csv')
postos_flu = postos_flu.loc[postos_flu['tipo']=='estacao']

print('\n#####-----#####-----#####-----#####-----#####-----#####')
print(f'02 - Coleta de dados de vazão\n')

for index, posto in postos_flu.iterrows():
## COLETA DADOS PRECIPITACAO
    idPosto = posto['idPosto']
    posto_codigo = posto['codigo_banco']
    posto_bacia = posto['bacia']
    posto_nome = posto['nome']
    posto_tipo = posto['tipo']

    dados = pd.read_csv(f'../../Vazao_Horaria/{idPosto}_HR.csv', parse_dates=True,
                        index_col='datahora')
    table_hor = dados[['q_m3s']]
    table_hor = table_hor.loc[table_hor['q_m3s'].first_valid_index():]
    #exporta dados horarios para csv
    table_hor.to_csv(f'../Dados/Vazao/{idPosto}.csv', sep = ",", float_format='%.2f')

    #Estacoes com falha nos dados
    if dados.empty:
        print(f'{index+1}/{len(postos_flu)} - {idPosto} - FALHA NO DADO')
    else:
        print(f'{index+1}/{len(postos_flu)} - {idPosto} - ',
              table_hor['q_m3s'].first_valid_index(), ' - ',
              table_hor['q_m3s'].last_valid_index())

print(f'\nColeta finalizada')
print('#####-----#####-----#####-----#####-----#####-----#####\n')
