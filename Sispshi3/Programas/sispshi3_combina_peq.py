import pandas as pd
import numpy as np
import csv
import datetime as dt
import plotly.graph_objects as go


bacia_nome = 'Sao_Mateus_do_Sul'
cod_bacia = '06'
area_inc = '2411'
area_tot = '6035'

precip = pd.read_csv(f'../Dados/Chuva/Historico_Bacias/hist_precip_{cod_bacia}_{bacia_nome}.csv',
                     index_col = 0, parse_dates=True)
precip.columns = ['pme']
data_inicial = precip.index[0]
data_final = precip.index[-1]


vazao = pd.read_csv(f'../Dados/Vazao/{cod_bacia}_{bacia_nome}.csv',
                    index_col = 0, parse_dates=True)
vazao.columns = ['qjus']
if vazao.index[0] > data_inicial:
    data_inicial = vazao.index[0]
if vazao.index[-1] < data_final:
    data_final = vazao.index[-1]

dados_peq = pd.merge(precip, vazao, how = 'outer',
                 left_index = True, right_index = True)


#Leitura das vazoes de montante. Faz o preenchimento de cada uma das vazoes
#Depois limita vazao em zero.
#Posteiormente, soma todas as vazoes de montante.
dados_mont1 = pd.read_csv(f'../Dados/Vazao/02_Porto_Amazonas.csv',index_col = 0, parse_dates=True)
dados_mont1['qmon'] = dados_mont1['q_m3s'].interpolate(method='spline', order=3)
dados_mont1 = dados_mont1.clip(lower=0)

#soma as diversas vazoes de montante (entre 1 e 4 valores p/ sispshi)
dados_mont = pd.DataFrame()
dados_mont['qmon'] = dados_mont1['qmon']

if dados_mont.index[0] > data_inicial:
    data_inicial = dados_mont.index[0]
if dados_mont.index[-1] < data_final:
    data_final = dados_mont.index[-1]

dados_peq = pd.merge(dados_peq, dados_mont['qmon'], how = 'outer',
                 left_index = True, right_index = True)
dados_peq = dados_peq.loc[data_inicial:data_final]

etp = pd.read_csv(f'../Dados/ETP/etpclim_{cod_bacia}.txt', header = None)
etp['Mes'] = etp[0].str.slice(0,2)
etp['Dia'] = etp[0].str.slice(3,5)
etp['Hora'] = etp[0].str.slice(6,8)
etp['etp'] = pd.to_numeric(etp[0].str.slice(9,17))
etp = etp.drop([0], axis=1)
etp.index = etp['Mes'] + '-' + etp['Dia'] + '-' + etp['Hora']

dados_peq['data'] = dados_peq.index.strftime('%m-%d-%H')
dados_peq['etp'] = dados_peq['data'].map(etp['etp'])
dados_peq = dados_peq.drop(['data'], axis=1)

dados_6hrs = (dados_peq.resample("6H", closed='right', label = 'right').
              agg({'pme':np.sum, 'etp':np.sum, 'qjus':np.mean, 'qmon':np.mean}))
dados_6hrs = dados_6hrs.iloc[1:-1]

with open(f'../../PEQ/peq_6h_{cod_bacia}_{bacia_nome}.csv', 'w', newline = '') as file:
    writer = csv.writer(file)
    writer.writerow([area_inc, area_tot])
dados_6hrs.to_csv(f'../../PEQ/peq_6h_{cod_bacia}_{bacia_nome}.csv', mode = 'a',
                  index_label='datahora', float_format='%.3f')
print('Finalizado PEQ - ' + cod_bacia + ' - ' + bacia_nome)
