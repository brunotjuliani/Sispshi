import pandas as pd
import numpy as np

serie = pd.read_csv('vazao_12.txt', delimiter='\s+', header=None)
serie.columns = ['Year', 'Month', 'Day', 'Hora', 'Q1', 'Q2']
serie.index = pd.to_datetime(serie[['Year', 'Month', 'Day']]) + pd.to_timedelta(serie['Hora'], unit = 'h')
serie2 = serie.loc['2021-02-02':]
serie2

datas = serie2.index
cliente = serie2[['Q2']]
cliente.columns = ['qobs']

Q0, i = cliente.qobs[datas[0]], 0
Q0
Q0.isna()
Q0 == None or Q0 == 'NaN'
while Q0 == None or Q0 == 'NaN':
    i += 1
    Q0 = cliente.qobs[datas[i]]

Q0
i
