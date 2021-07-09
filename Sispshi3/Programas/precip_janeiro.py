import numpy as np
import pandas as pd
import datetime as dt
import csv


#Lista postos de precipitacao com as seguintes informacoes
# Nome : [codigo simepar, codigo ANA, latitude, longitute, altitude]
postos_precip = pd.read_csv('../Dados/Precip_Estacoes/postos_def.csv')

## COLETA DADOS PRECIPITACAO
for index, posto in postos_precip.iterrows():
    idPosto = posto['idPosto']
    posto_codigo = posto['codigo_simepar']
    posto_snirh = posto['codigo_snirh']
    posto_nome = posto['nome']
    posto_banco = posto['banco']
    posto_x = posto['x']
    posto_y = posto['y']
    posto_z = posto['z']

    sr_posto = pd.read_csv(f'../Dados/Precip_Estacoes/{idPosto}.csv',
                           parse_dates=True, index_col='datahora', skiprows=3)
    sr_posto = sr_posto.loc['2021-01']
    sr_posto = sr_posto[['chuva_mm']]

    #exporta dados horarios para csv
    with open(f'../Dados/Precip_Janeiro/{idPosto}.csv','w',newline='') as file:
        writer = csv.writer(file)
        writer.writerow([posto_snirh])
        writer.writerow([posto_nome])
        writer.writerow([posto_x, posto_y, posto_z])
    sr_posto.to_csv(f'../Dados/Precip_Janeiro/{idPosto}.csv',
                    mode = 'a', sep = ',', float_format='%.2f')

    print(posto_nome, ' acabou')
