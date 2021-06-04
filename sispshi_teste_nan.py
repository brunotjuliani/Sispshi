import pandas as pd
import numpy as np

### LEITURA FORÇANTES
bn = 1
bnome = 'Rio_Negro'
bacias = {
    1:'Rio_Negro',
    2:'Porto_Amazonas',
    3:'Sao_Bento',
    4:'Pontilhao',
    5:'Santa_Cruz_Timbo',
    10:'Madereira_Gavazzoni',
    11:'Jangada',
    13:'Solais_Novo',
    14:'Porto_Santo_Antonio',
    15:'Aguas_do_Vere'
    }
for bn, bnome in bacias.items():
    area = pd.read_csv(f'./PEQ/{bn:02d}_{bnome}_peq.csv', nrows=1, header=None).values[0][0]
    PEQ = pd.read_csv(f'./PEQ/{bn:02d}_{bnome}_peq.csv', skiprows=1,
                      parse_dates=True, index_col='datahora')
    tamanho = len(PEQ)
    s = PEQ.qjus.isna().groupby(PEQ.qjus.notna().cumsum()).sum()
    s = s[s!=0]
    soma = s.sum()
    maximo = s.max()

    len(PEQ)

    print(bn, ' - ', bnome)
    print('Tamanho da série: ', tamanho)
    print('Número de falhas: ', soma)
    print('Porcentagem de falhas: ', soma/tamanho*100)
    print('Comprimento da maior sequência de falhas: ', maximo)
    print('Maior sequência de falhas (em dias): ', maximo/4, '\n')
