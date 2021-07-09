from datetime import datetime, timedelta
import pandas as pd
import numpy as np

print('\n#####-----#####-----#####-----#####-----#####-----#####')
print(f'03 - Espacialização dos dados de precipitação\n')

# Definicoes inicias
dmax = 60
grade_def = pd.read_csv('../Dados/grade_def.csv', index_col='idGrade')
postos_def = pd.read_csv('../Dados/postos_def.csv', index_col='idPosto')
# matriz de distancias ponto de grade - posto pluviometrico
D = pd.read_csv('../Dados/matriz_distancias.csv', index_col='idGrade')

# Coleta as series de chuva dos postos
chuva_postos = pd.DataFrame()
for idPosto in postos_def.index:
    chuva_posto = pd.read_csv(f'../Dados/Chuva/Estacoes_Operacionais/{idPosto}.csv',
                              index_col='datahora', parse_dates=True,
                              squeeze=True, skiprows=3).rename(f'{idPosto}')
    chuva_postos = pd.concat([chuva_postos, chuva_posto], axis=1)

# Metodo Matricial
chuva_postos = chuva_postos[D.columns.tolist()] # Tem que ordenar
chuva_grade = pd.DataFrame(columns=grade_def.index) # Tem que ordenar
n = len(grade_def)
for row in chuva_postos.itertuples():
    t = row[0]
    chuva_postos_t = np.asarray(row[1:])
    print(datetime.now(), f'- Interpolando {t}')

    # Calcula a matriz de pesos W no tempo t com base nas premissas de distancia e disponibilidade
    chuva_postos_t = np.tile(chuva_postos_t, (n, 1))
    mascara_t = np.logical_or(D.values > dmax, np.isnan(chuva_postos_t))
    W_t = np.ma.array(1/D.values**2, mask = mascara_t)

    # Interpola
    chuva_grade_t = np.sum(W_t * chuva_postos_t, axis=1) / np.sum(W_t, axis=1)
    chuva_grade.loc[t,:] = chuva_grade_t.filled(np.nan)

print(datetime.now(), f'- Interpolacao concluida.')

chuva_grade = chuva_grade.applymap(lambda x: np.round(x, 1))

#Exporta rodada inicial - sem serie inicial
#chuva_grade.to_csv('../Dados/Chuva/chuva_grade.csv', index_label='datahora', na_rep='NA')

##EXPORTA SERIE ATUALIZADA
#Le serie historica antiga para grade
chuva_hist = pd.read_csv('../Dados/Chuva/chuva_grade.csv', index_col='datahora',
                         parse_dates=True)
chuva_hist.columns = chuva_hist.columns.astype(int)

#Atualiza serie da grade
chuva_att = pd.concat([chuva_hist,chuva_grade])
chuva_att = chuva_att[~chuva_att.index.duplicated(keep='last')]

#Recorta apenas para período de aquecimento
inicio = chuva_att.index[-1] - timedelta(days=700)
chuva_att = chuva_att.loc[inicio:]
# Salva a chuva interpolada nos pontos de grade
chuva_att.to_csv('../Dados/Chuva/chuva_grade.csv', index_label='datahora',
                 na_rep='NA')

print(f'\nEspacialização para grade finalizada')
print(f'Calculando chuva média por sub-bacia\n')
#Define numero de bacias do Sispshi (range até n+1)
b_sispshi = list(range(1,22))
for bacia in b_sispshi:
    #selecao dos pontos da grade por bacia
    selecao = chuva_att[list(grade_def.loc[grade_def['bacia'] == bacia].index)]
    chuva_sub = pd.DataFrame(selecao.mean(axis=1), columns=['chuva_mm'])
    #exporta chuva media por bacia
    chuva_sub.to_csv(f'../Dados/Chuva/chuva_b{bacia}.csv', index_label='datahora',
                     na_rep='NA')
    print(f'Chuva média na Bacia {bacia} calculada')

print('\nEspacialização da chuva finalizada')
print('#####-----#####-----#####-----#####-----#####-----#####\n')
