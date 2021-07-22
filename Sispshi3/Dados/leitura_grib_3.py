import pandas as pd
import numpy as np
import datetime as dt
import pygrib
import xarray as xr

#hora arquivo ecmwf
data_ecmwf = dt.datetime(2021, 7, 1, 00, tzinfo=dt.timezone.utc)

#Definicao das sub-bacias
bacias_def = pd.read_csv('bacias_def.csv')
#Definicao da grade padrao
grade_def = pd.read_csv('grade_def.csv', index_col='idGrade')

print('Leitura gribfile')
ds = xr.open_dataset('recorte_D1E_2021072200.grb', engine='cfgrib')
grbs = ds.to_dataframe()

#Lista membro ensemble
membros = grbs.index.unique('number')
#Lista passos de tempo
steps = grbs.index.unique('step')

#Dicionarios para dataframes de previsoes por membro
prev_membros = {}
prev_disc = {}

for ens_n in membros:
    print('Espacializando membro ', ens_n)
    #inicializa dataframe unico para membro
    prev_membros[ens_n] = pd.DataFrame()
    for passo in steps:
        idx_hora = data_ecmwf + passo
        #filtra dados para membro e tempo
        membro = grbs.loc[:,:,ens_n,passo].reset_index(level=['latitude','longitude'])
        #transforma lon para padrao, e arredonda p/ correlacao
        membro['x'] = (membro['longitude'] - 360).apply(lambda x: round(x,1))
        membro['y'] = membro['latitude'].apply(lambda x: round(x,1))
        #correlaciona com grade padrao das sub-bacias Sispshi
        prev_sispshi = pd.merge(membro, grade_def, on=['x', 'y'])
        #precipitacao media em cada bacia
        for idx, info in bacias_def.iterrows():
            bacia = info['bacia']
            prev_bacia = prev_sispshi.loc[prev_sispshi['bacia']==bacia]['unknown'].mean()
            #armazena p/ passo de tempo e bacia
            prev_membros[ens_n].loc[idx_hora,bacia] = prev_bacia
    #diferenciacao para cada passo de tempo isolado, comparacao do acumulado
    #exclui primeira linha - condicoes iniciais
    prev_disc[ens_n] = prev_membros[ens_n].diff().iloc[1:]

prev_disc[50]
