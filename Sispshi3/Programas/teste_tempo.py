import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta

postos_def = pd.read_csv('../Dados/postos_def.csv', index_col='idPosto')

hora_att = open('../Dados/disparo.txt')
data_ant = hora_att.readline().strip()
disparo = hora_att.readline().strip()
hora_att.close()
d_ini = datetime.strptime(data_ant, '%Y-%m-%d %H:%M:%S%z') - timedelta(days=3)



print('Iniciando parte 1')
start1 = time.time()
chuva_postos = pd.DataFrame()
for idPosto in postos_def.index:
    chuva_posto = pd.read_csv(f'../Dados/Chuva/Estacoes_Operacionais/{idPosto}.csv',
                              index_col='datahora', parse_dates=True,
                              squeeze=True, skiprows=3).rename(f'{idPosto}')
    chuva_posto = chuva_posto.loc[d_ini:]
    chuva_postos = pd.concat([chuva_postos, chuva_posto], axis=1)
end1 = time.time()
print(end1-start1)

print('Iniciando parte 2')
start2 = time.time()
chuva_postos = pd.DataFrame()
for idPosto in postos_def.index:
    chuva_posto = pd.read_csv(f'../Dados/Chuva/Dados_Rodada/{idPosto}_rodada.csv',
                              index_col='datahora', parse_dates=True,
                              squeeze=True, skiprows=3).rename(f'{idPosto}')
    chuva_postos = pd.concat([chuva_postos, chuva_posto], axis=1)
end2 = time.time()
print(end2-start2)
