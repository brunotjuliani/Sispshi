import pandas as pd
import numpy as np
import datetime as dt

print('\n#####-----#####-----#####-----#####-----#####-----#####')

#Definicao das sub-bacias
bacias_def = pd.read_csv('../Dados/bacias_def.csv')
#Definicao da grade padrao
grade_def = pd.read_csv('../Dados/grade_def.csv', index_col='idGrade')

#Abre serie gradeada de chuva do periodo de aquecimento para toda a area
grade_chuva = pd.read_csv('../Dados/Chuva/chuva_grade.csv', index_col='datahora',
                          parse_dates=True)
grade_chuva.columns = grade_chuva.columns.astype(int)
grade_chuva = grade_chuva.loc['2013':'2021']

#Organizacao dos arquivos de entrada para cada bacia
aq_bacias = {}
for idx, info in bacias_def.iterrows():
    idBacia = info['idBacia']
    bacia = info['bacia']
    posto_nome = info['nome']

    #chuva media na bacia
    selecao = grade_chuva[list(grade_def.loc[grade_def['bacia'] == bacia].index)]
    chuva_sub = pd.DataFrame(selecao.mean(axis=1), columns=['chuva_mm'])
    chuva_sub.to_csv(f'../Dados/Chuva/Historico_Bacias/hist_precip_{idBacia}.csv',
                     index_label='datahora', float_format='%.3f')
