import numpy as np
import pandas as pd
import os

bacia = int(input('Digite o codigo da sub-bacia Sispshi [1 a 21]'))
while bacia not in range(1,22):
    bacia = int(input('Código inválido. Digite o codigo da sub-bacia Sispshi [1 a 21]'))
serie_completa = pd.DataFrame()
os.chdir("../Dados/PME_Siprec")
for ano_df in ['2013', '2014', '2015', '2016', '2017', '2018', '2019', '2020', '2021']:
    serie_anual = pd.read_csv(f'{bacia:02d}_siprec_hist_{ano_df}.csv',
                              parse_dates=True, index_col='datahora')
    serie_completa = pd.concat([serie_completa, serie_anual])
    serie_completa = serie_completa[~serie_completa.index.duplicated(keep='last')]
    os.system(f'rm -r {bacia:02d}_siprec_hist_{ano_df}.csv')
serie_completa.to_csv(f'{bacia:02d}_siprec_hist.csv', sep=',', index_label='datahora',
                      date_format='%Y-%m-%dT%H:%M:%S+00:00', float_format='%.2f')
