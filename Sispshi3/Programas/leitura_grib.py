import pandas as pd
import numpy as np
import datetime as dt
import pygrib
import time

print(dt.datetime.now(), 'Inicializando')
start1 = time.time()

#Definicoes da hora da rodada
hora_att = open('../Dados/disparo.txt')
data_ant = hora_att.readline().strip()
disparo = hora_att.readline().strip()
hora_att.close()
rodada = dt.datetime.strptime(disparo, '%Y-%m-%d %H:%M:%S%z')
data_ecmwf = dt.datetime(rodada.year, rodada.month, rodada.day, 00)
ano, mes, dia, hora = data_ecmwf.year, data_ecmwf.month, data_ecmwf.day, data_ecmwf.hour

#Definicao das sub-bacias
bacias_def = pd.read_csv('../Dados/bacias_def.csv')
#Definicao da grade padrao
grade_def = pd.read_csv('../Dados/grade_def.csv', index_col='idGrade')
bacias_dic = grade_def.groupby('bacia').apply(lambda x: x.index.tolist()).to_dict()



print(dt.datetime.now(), 'Leitura gribfile')

grbfile = '../Dados/recorte_D1E.grb'
grbs = pygrib.open(grbfile)

prev_membros = {}
prev_disc = {}
prev_pontos = {}



ens_n = 0
while ens_n <= 50:
    print(dt.datetime.now(), 'Membro ', ens_n)
    membro = grbs.select(perturbationNumber=ens_n)
    prev_membros[ens_n] = pd.DataFrame()
    prev_pontos[ens_n] = pd.DataFrame()
    previsao = membro[0]
    for previsao in membro:
        passo_tempo = data_ecmwf + dt.timedelta(hours=previsao.step)
        valores = previsao.latLonValues
        lista = [valores[i * 3:(i + 1) * 3] for i in range((len(valores) + 3 - 1) // 3 )]
        df = pd.DataFrame(lista, columns=['y','x','value'])
        df['x'] = df['x']-360
        df['x'] = df['x'].apply(lambda x: round(x,1))
        df['y'] = df['y'].apply(lambda x: round(x,1))
        df2 = pd.merge(grade_def,df,on=['x','y'], how='left')
        df2.index = grade_def.index
        for ponto in df2.index:
            prev_pontos[ens_n].loc[passo_tempo,ponto] = df2.loc[ponto,'value']
    prev_disc[ens_n] = prev_pontos[ens_n].diff().fillna(prev_pontos[ens_n].iloc[0])
    for idx, info in bacias_def.iterrows():
        bacia = info['bacia']
        prev_membros[ens_n][bacia] = prev_disc[ens_n][bacias_dic[bacia]].mean(axis=1)
    ens_n += 1

print(dt.datetime.now(), 'Finalizado')
prev_membros[1]
