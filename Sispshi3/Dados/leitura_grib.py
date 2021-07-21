import pandas as pd
import numpy as np
import datetime as dt
import pygrib

#hora arquivo ecmwf
data_ecmwf = dt.datetime(2021, 7, 15, 00, tzinfo=dt.timezone.utc)

#Definicao das sub-bacias
bacias_def = pd.read_csv('bacias_def.csv')
#Definicao da grade padrao
grade_def = pd.read_csv('grade_def.csv', index_col='idGrade')

print('Leitura gribfile')
grbfile = 'recorte_D1E.grb'
grbs = pygrib.open(grbfile)

#Dicionarios para dataframes de previsoes por membro
prev_membros = {}
prev_disc = {}

ens_n = 0
while ens_n <= 50:
    print('Espacializando membro ', ens_n)
    #seleciona todos os dados para determinado membro
    membro = grbs.select(perturbationNumber = ens_n)
    #inicializa dataframe unico para membro
    prev_membros[ens_n] = pd.DataFrame()
    #loop temporal p/ cada membro
    for previsao in membro:
        passo_tempo = data_ecmwf + dt.timedelta(hours=previsao.step)
        #retorna lista (todos os pontos) na respectiva ordem: lat,lon,p_acumulada
        valores = previsao.latLonValues
        lista = [valores[i * 3:(i + 1) * 3] for i in range((len(valores) + 3 - 1) // 3 )]
        df = pd.DataFrame(lista, columns=['y', 'x', 'value'])
        #transforma lon para padrao, e arredonda p/ correlacao
        df['x'] = df['x'] - 360
        df['x'] = df['x'].apply(lambda x: round(x,1))
        df['y'] = df['y'].apply(lambda x: round(x,1))
        #correlaciona com grade padrao das sub-bacias Sispshi
        prev_sispshi = pd.merge(df, grade_def, on=['x', 'y'])
        #precipitacao media em cada bacia
        for idx, info in bacias_def.iterrows():
            bacia = info['bacia']
            prev_bacia = prev_sispshi.loc[prev_sispshi['bacia']==bacia]['value'].mean()
            #armazena p/ passo de tempo e bacia
            prev_membros[ens_n].loc[passo_tempo,bacia] = prev_bacia
    #diferenciacao para cada passo de tempo isolado, comparacao do acumulado
    #exclui primeira linha - condicoes iniciais
    prev_disc[ens_n] = prev_membros[ens_n].diff().iloc[1:]
    #passa para proximo membro
    ens_n +=1
prev_disc[0]
