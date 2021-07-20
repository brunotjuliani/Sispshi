from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import time

print('\n#####-----#####-----#####-----#####-----#####-----#####')
print(f'03 - Espacialização dos dados de precipitação\n')


start1 = time.time()

# Definicoes inicias
dmax = 50
grade_def = pd.read_csv('../Dados/grade_def.csv', index_col='idGrade')
postos_def = pd.read_csv('../Dados/postos_def.csv', index_col='idPosto')
# matriz de distancias ponto de grade - posto pluviometrico
D = pd.read_csv('../Dados/matriz_distancias.csv', index_col='idGrade')

hora_att = open('../Dados/disparo.txt')
data_ant = hora_att.readline().strip()
disparo = hora_att.readline().strip()
hora_att.close()
d_ini = datetime.strptime(data_ant, '%Y-%m-%d %H:%M:%S%z') - timedelta(days=3)

# Coleta as series de chuva dos postos
chuva_postos = pd.DataFrame()
for idPosto in postos_def.index:
    chuva_posto = pd.read_csv(f'../Dados/Chuva/Estacoes_Operacionais/{idPosto}.csv',
                              index_col='datahora', parse_dates=True,
                              squeeze=True, skiprows=3).rename(f'{idPosto}')
    chuva_posto = chuva_posto.loc[d_ini:]
    chuva_postos = pd.concat([chuva_postos, chuva_posto], axis=1)

# Metodo Matricial
chuva_postos = chuva_postos[D.columns.tolist()] # Tem que ordenar
chuva_grade = pd.DataFrame(columns=grade_def.index) # Tem que ordenar
n = len(grade_def)
for row in chuva_postos.itertuples():
    t = row[0]
    chuva_postos_t = np.asarray(row[1:])
    #print(datetime.now(), f'- Interpolando {t}')

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
chuva_att.to_csv('../Dados/Chuva/chuva_grade.csv', index_label='datahora',
                 na_rep='NA')

#Recorta apenas para período de aquecimento
inicio = chuva_att.index[-1] - timedelta(days=730)
chuva_aquecimento = chuva_att.loc[inicio:]
#Salva a interpolacao para periodo da rodada
chuva_aquecimento.to_csv('../Dados/Chuva/chuva_grade_730.csv',
                         index_label='datahora', na_rep='NA')

print('\nEspacialização da chuva finalizada')
print('#####-----#####-----#####-----#####-----#####-----#####\n')

end1 = time.time()
print('Tempo decorrido ', end1-start1)
