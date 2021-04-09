import pandas as pd
import numpy as np
import csv

bacias_cab = {
    'Rio_Negro':['01','3461'],
    'Porto_Amazonas':['02','3624'],
    'Sao_Bento':['03','2003'],
    'Pontilhao':['04','2209'],
    'Santa_Cruz_Timbo':['05','2605'],
    'Madereira_Gavazzoni':['10','978'],
    'Jangada':['11','1004'],
    'Solais_Novo':['13','1654'],
    'Porto_Santo_Antonio':['14','1083'],
    'Aguas_do_Vere':['15','6694'],
           }
bacias_inc = {
    'Sao_Mateus_Sul':['06','2411'],
    'Divisa':['07','2590'],
    'Fluviopolis':['08','2287'],
    'Uniao_da_Vitoria':['09','3029'],
    'Porto_Capanema':['20','6801'],
    'Hotel_Cataratas':['21','2981'],
              }

for bacia_nome, bacia_informacoes in bacias_cab.items():
    cod_bacia = bacia_informacoes[0]
    area_inc = bacia_informacoes[1]

    precip = pd.read_csv(f'../Dados/PME_Haversine/{cod_bacia}_{bacia_nome}_PME.csv',
                         index_col = 0, parse_dates=True)
    precip.columns = ['pme']
    data_inicial = precip.index[0]
    data_final = precip.index[-1]

    vazao = pd.read_csv(f'../Dados/Vazao_Horaria/{cod_bacia}_{bacia_nome}_HR.csv',
                        index_col = 0, parse_dates=True)
    vazao = pd.DataFrame(vazao['q_m3s'].rename('qjus'))
    if vazao.index[0] > data_inicial:
        data_inicial = vazao.index[0]
    if vazao.index[-1] < data_final:
        data_final = vazao.index[-1]

    dados_peq = pd.merge(precip, vazao, how = 'outer',
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

    try:
        siprec = pd.read_csv(f'../Dados/PME_Siprec/{cod_bacia}_siprec_hist.csv',
                             index_col = 0, parse_dates=True)
        siprec.columns = ['siprec']
        if siprec.index[0] > data_inicial:
            data_inicial = siprec.index[0]
        if siprec.index[-1] < data_final:
            data_final = siprec.index[-1]
        dados_peq = pd.merge(dados_peq, siprec, how = 'outer',
                         left_index = True, right_index = True)
        dados_peq = dados_peq.loc[data_inicial:data_final]
    except:
        dados_peq['siprec'] = np.nan

    dados_peq['qmon'] = 0
    dados_peq = dados_peq[['pme', 'siprec', 'etp', 'qjus', 'qmon']]

    dados_6hrs = (dados_peq.resample("6H", closed='right', label = 'right').
                  agg({'pme':np.sum, 'siprec':np.sum, 'etp':np.sum,
                       'qjus':np.mean, 'qmon':np.mean}))
    dados_6hrs = dados_6hrs.iloc[1:]

    dados_6hrs['pme'] = dados_6hrs['pme'].apply('{:.2f}'.format)
    dados_6hrs['siprec'] = dados_6hrs['siprec'].apply('{:.2f}'.format)
    dados_6hrs['qjus'] = dados_6hrs['qjus'].apply('{:.3f}'.format)
    dados_6hrs['etp'] = dados_6hrs['etp'].apply('{:.3f}'.format)
    dados_6hrs['qmon'] = dados_6hrs['qmon'].apply('{:.3f}'.format)

    with open(f'../Dados/PEQ/{cod_bacia}_{bacia_nome}_peq.csv', 'w', newline = '') as file:
        writer = csv.writer(file)
        writer.writerow([area_inc])
    dados_6hrs.to_csv(f'../Dados/PEQ/{cod_bacia}_{bacia_nome}_peq.csv', mode = 'a',
                     date_format='%Y-%m-%dT%H:%M:%S+00:00', sep = ",")
    print('Finalizado PEQ - ' + cod_bacia + ' - ' + bacia_nome)
