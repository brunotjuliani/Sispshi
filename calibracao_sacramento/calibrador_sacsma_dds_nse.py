import pandas as pd
import sacsma2021
from sacsma2021 import Xnomes, Xmin, Xmax
import dds
import matplotlib.pyplot as plt

def fobj(X):
    params = X
    Qsim = sacsma2021.simulacao(area, dt, PME, ETP, params)
    Qsim = pd.Series(index=idx, data=Qsim, name='qsim')
    df = pd.concat([Qsim, Qobs], axis=1)
    df = df.loc[idx_cal]
    df = df.dropna()
    NSE = 1 - df.apply(lambda x:(x.qsim-x.qobs)**2,axis=1).sum()/df.apply(lambda x:(x.qobs-df.qobs.mean())**2,axis=1).sum()
    fmin = 1 - NSE
    return fmin

def sim(X):
    params = X
    Qsim = sacsma2021.simulacao(area, dt, PME, ETP, params)
    Qsim = pd.Series(index=idx, data=Qsim, name='qsim')
    return Qsim

if __name__ == '__main__':
    peq_nome = 'sispshi_01_Rio_Negro_peq.csv'
    area = pd.read_csv(peq_nome, nrows=1, header=None).values[0][0]
    dt = 0.25 # 6 hr
    PEQ = pd.read_csv(peq_nome, skiprows=1, parse_dates=True, index_col='datahora')
    PME = PEQ['pme']
    ETP = PEQ['etp']
    Qobs = PEQ['qjus'].rename('qobs')
    idx = PME.index
    idx_cal = idx[idx > '2014-01-01']
    Xmin = Xmin[:-3] # desconsidera os parametros de propagacao
    Xmax = Xmax[:-3] # desconsidera os parametros de propagacao
    Xbest, Fbest = dds.dds(Xmin, Xmax, fobj, r=0.2, m=100)
    Qsim_best = sim(Xbest)

    # Visualiza PEQ
    fig, ax = plt.subplots()
    PEQ['pme'].plot(ax=ax, color='blue')
    ax2 = ax.twinx()
    Qobs.plot(ax=ax2, color='black', label='Obs')
    Qsim_best.plot(ax=ax2, color='red', label='Sim')
    plt.legend()
    plt.show()
