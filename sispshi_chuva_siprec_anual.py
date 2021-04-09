#from netCDF4 import Dataset
import numpy as np
import pandas as pd
#from pathlib import Path
#from datetime import datetime
#import glob
#from time import time
import xarray as xr
import os

inicio='2013-01-01 00:00:00'
fim='2021-01-01 00:00:00'

#anos = ['2013', '2014', '2015', '2016', '2017', '2018', '2019']
anos = ['2020', '2021']

periodo=pd.date_range(start=inicio,end=fim,freq='1h',closed=None)
df_completo = pd.DataFrame(index=periodo)
bacia = int(input('Digite o codigo da sub-bacia Sispshi [1 a 21]'))
while bacia not in range(1,22):
    bacia = int(input('Código inválido. Digite o codigo da sub-bacia Sispshi [1 a 21]'))
arquivo_grade = f'../Grades/grade_b{bacia:02d}.csv'
df_grade = pd.read_csv(arquivo_grade, sep=',')

for ano_df in anos:
    df_resumo = df_completo.copy().loc[f'{ano_df}']
    for i in df_grade.index:
        df_resumo[i] = np.nan
    for tempo in df_resumo.index:
        print(tempo)
        try:
            hora=tempo.hour
            ano=tempo.year
            mes=tempo.month
            dia=tempo.day
            arquivo =f'/simepar/product/siprec/simepar/r1/hourly/{ano:04d}/{mes:02d}/{dia:02d}/siprec_v2_{ano:04d}_{mes:02d}_{dia:02d}_{hora:02d}.nc'
            da=xr.open_dataset(arquivo)
            for i in df_grade.index:
                lon = df_grade.loc[i,'x']
                lat = df_grade.loc[i,'y']
                try:
                    chuva_ponto=da['SIPREC'].sel(latitudes=lat,longitudes=lon,method='nearest',drop=True)[0].values
                except:
                    chuva_ponto=da['SIPREC'].sel(lat_sat=lat,lon_sat=lon,method='nearest',drop=True).values
                df_resumo.loc[tempo,i] = chuva_ponto
            da.close()
        except Exception as e:
            print(e)
    df_resumo['pme_mm'] = df_resumo.mean(axis=1)
    df_exporta = df_resumo[['pme_mm']]
    df_exporta.to_csv(f'../Dados/PME_Siprec/{bacia:02d}_siprec_hist_{ano_df}.csv', sep=',', index_label='datahora',
                     date_format='%Y-%m-%dT%H:%M:%S+00:00', float_format='%.2f')
