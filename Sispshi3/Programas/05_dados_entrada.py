import pandas as pd
import numpy as np
import datetime as dt
from pathlib import Path

#Definicoes da hora da rodada
hora_att = open('../Dados/disparo.txt')
data_ant = hora_att.readline().strip()
disparo = hora_att.readline().strip()
hora_att.close()
rodada = dt.datetime.strptime(disparo, '%Y-%m-%d %H:%M:%S%z')
ano, mes, dia, hora = rodada.year, rodada.month, rodada.day, rodada.hour

#Definicao das sub-bacias
bacias_def = pd.read_csv('../Dados/bacias_def.csv')
#Definicao da grade padrao
grade_def = pd.read_csv('../Dados/grade_def.csv', index_col='idGrade')

#Cria pasta para exportar resultados de simulacao
Path(f'../Simulacoes/{ano:04d}_{mes:02d}_{dia:02d}_{hora:02d}').mkdir(parents=True,exist_ok=True)

#As series serao recortadas para periodo de aquecimento (2 anos)
inicio = rodada - dt.timedelta(days=730)
grade_chuva = pd.read_csv('../Dados/chuva_grade.csv', index_col='datahora',
                          parse_dates=True)
grade_chuva = grade_chuva.loc[inicio:]

for idx, info in bacias_def.iterrows():
    idBacia = info['idBacia']
    bacia = info['bacia']
    posto_nome = info['nome']

    # Inicia dataframe
    dados_peq = pd.DataFrame()

    #chuva
    selecao = grade_chuva[list(grade_def.loc[grade_def['bacia'] == bacia].index)]
    chuva_sub = pd.DataFrame(selecao.mean(axis=1), columns=['chuva_mm'])
    #combina com chuva ensemble de previsao
    #loop ensemble
    #chuva_comb = pd.concat([chuva_sub, chuva_membro])
    #chuva_comb = chuva_comb[~chuva_comb.index.duplicated(keep='last')]
    #chuva_comb = chuva_comb.rename(columns={'chuva_mm':'pme'})
    #dados_peq['pme_'+str(membro)] = chuva_comb['pme']

    #vazao
    vazao_sub = pd.read_csv(f'../Dados/Vazao/{idBacia}.csv',
                            index_col='datahora', parse_dates=True)
    vazao_sub = vazao_sub.loc[inicio:]
    dados_peq = pd.merge(dados_peq, vazao_sub, how = 'left',
                     left_index = True, right_index = True)

    #etp
    etp = pd.read_csv(f'../Dados/ETP/etpclim_{bacia:02d}.txt', header = None)
    etp['Mes'] = etp[0].str.slice(0,2)
    etp['Dia'] = etp[0].str.slice(3,5)
    etp['Hora'] = etp[0].str.slice(6,8)
    etp['etp'] = pd.to_numeric(etp[0].str.slice(9,17))
    etp = etp.drop([0], axis=1)
    etp.index = etp['Mes'] + '-' + etp['Dia'] + '-' + etp['Hora']
    dados_peq['data'] = dados_peq.index.strftime('%m-%d-%H')
    dados_peq['etp'] = dados_peq['data'].map(etp['etp'])
    dados_peq = dados_peq.drop(['data'], axis=1)


posto = postos_flu.loc[0]
posto
#Chuva
