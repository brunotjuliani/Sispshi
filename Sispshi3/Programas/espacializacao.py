from datetime import datetime, timedelta
import pandas as pd
import numpy as np

def harvesine(lon1, lat1, lon2, lat2):
    '''
    Calcula a distancia de circulo maximo dois pontos na superficie da Terra
    '''
    # Converte graus em radianos pela funcao 'radians' do math
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    # Formula de haversine
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371 # Raio da Terra em km. Usar 3956 para milhas
    return c * r

print(datetime.now(), ' - Processando distancias postos-grade')
D = pd.DataFrame()
grade_def = pd.read_csv('grade_def.csv', index_col='idGrade')
postos_def = pd.read_csv('postos_def.csv', index_col='idPosto')

for idGrade in grade_def.index:
    lon1, lat1 = grade_def.loc[idGrade, ['x','y']]
    for idPosto in postos_def.index:
        lon2, lat2 = postos_def.loc[idPosto, ['x','y']]
        D.loc[idGrade, idPosto] = harvesine(lon1, lat1, lon2, lat2)
D.to_csv('matriz_distancias.csv', index_label='idGrade', float_format='%.2f')
print(datetime.now(), '- Concluido.')

# Definicoes inicias
dmax = 50
# matriz de distancias ponto de grade - posto pluviometrico
#D = pd.read_csv('matriz_distancias.csv', index_col='idGrade')

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
    #print(datetime.now(), f'- Interpolando {t}')

    # Calcula a matriz de pesos W no tempo t com base nas premissas de distancia e disponibilidade
    chuva_postos_t = np.tile(chuva_postos_t, (n, 1))
    mascara_t = np.logical_or(D.values > dmax, np.isnan(chuva_postos_t))
    W_t = np.ma.array(1/D.values**2, mask = mascara_t)

    # Interpola
    chuva_grade_t = np.sum(W_t * chuva_postos_t, axis=1) / np.sum(W_t, axis=1)
    chuva_grade.loc[t,:] = chuva_grade_t.filled(np.nan)

chuva_grade = chuva_grade.applymap(lambda x: np.round(x, 1))
