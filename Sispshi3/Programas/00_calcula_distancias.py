'''
Essa funcao calcula as distancias entre os pontos de grade e os postos pluviometricos
Utilizam-se as informacoes em grade_def.csv e postos_def.csv
O resultado eh o arquivo distancias.csv
'''
from datetime import datetime
from math import radians, cos, sin, asin, sqrt
import pandas as pd

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
grade_def = pd.read_csv('../Dados/grade_def.csv', index_col='idGrade')
postos_def = pd.read_csv('../Dados/postos_def.csv', index_col='idPosto')

for idGrade in grade_def.index:
    lon1, lat1 = grade_def.loc[idGrade, ['x','y']]
    for idPosto in postos_def.index:
        lon2, lat2 = postos_def.loc[idPosto, ['x','y']]
        D.loc[idGrade, idPosto] = harvesine(lon1, lat1, lon2, lat2)
D.to_csv('../Dados/matriz_distancias.csv', index_label='idGrade', float_format='%.2f')

print(datetime.now(), '- Concluido.')
