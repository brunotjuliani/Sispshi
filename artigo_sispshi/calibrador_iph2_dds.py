import pandas as pd
import numpy as np
import math
import iph2
from iph2 import Xnomes, Xmin, Xmax
import dds
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import HydroErr as he
import hydroeval as hv

### DEFINICAO FUNÇÕES OBJETIVO E SIMULAÇÃO
def fobj_nse(X):
    params = X
    Qsim = iph2.IPH2(area, dt, PME, ETP, params)
    Qsim = pd.Series(index=idx, data=Qsim, name='qsim')
    df = pd.concat([Qsim, Qobs], axis=1)
    df = df.loc[idx_cal]
    df = df.dropna()
    NSE = 1 - df.apply(lambda x:(x.qsim-x.qobs)**2,axis=1).sum()/df.apply(lambda x:(x.qobs-df.qobs.mean())**2,axis=1).sum()
    fmin = 1 - NSE
    return fmin

def fobj_log(X):
    params = X
    Qsim = iph2.IPH2(area, dt, PME, ETP, params)
    Qsim = pd.Series(index=idx, data=Qsim, name='qsim')
    df = pd.concat([Qsim, Qobs], axis=1)
    df = df.loc[idx_cal]
    df = df.dropna()
    df['log_min'] = df.apply(lambda x: (np.log(x['qsim']) - np.log(x['qobs']))**2, axis=1)
    fmin = df['log_min'].sum()
    return fmin

def fobj_drms(X):
    params = X
    Qsim = iph2.IPH2(area, dt, PME, ETP, params)
    Qsim = pd.Series(index=idx, data=Qsim, name='qsim')
    df = pd.concat([Qsim, Qobs], axis=1)
    df = df.loc[idx_cal]
    df = df.dropna()
    df['drms_min'] = df.apply(lambda x: (x['qsim'] - x['qobs'])**2, axis=1)
    fmin = math.sqrt(df['drms_min'].sum())/len(df)
    return fmin

def sim(X):
    params = X
    Qsim = iph2.IPH2(area, dt, PME, ETP, params)
    Qsim = pd.Series(index=idx, data=Qsim, name='qsim')
    return Qsim

### GUIA DE ORDEM DE PARÂMETROS
##### 'RMAX'    : 0
##### 'Io'      : 1
##### 'fIb'     : 2
##### 'H'       : 3
##### 'alfa'    : 4
##### 'Ksup'    : 5
##### 'Ksub'    : 6
##### 'Aimp'    : 7
##### 'NH'      : 8


### LEITURA FORÇANTES
bn = '05'
bnome = 'Santa_Cruz_Timbo'
area = pd.read_csv(f'./PEQ/{bn}_{bnome}_peq_diario.csv', nrows=1, header=None).values[0][0]
dt = 24 # 24 horas / 1 dia
PEQ = pd.read_csv(f'./PEQ/{bn}_{bnome}_peq_diario.csv', skiprows=1,
                  parse_dates=True, index_col='datahora')

PME = PEQ['pme']
ETP = PEQ['etp']
Qobs = PEQ['qjus'].rename('qobs')
idx = PME.index
idx_cal = idx[idx > '2016-01-01']

### PRIMEIRA CALIBRAÇÃO -> NSE P/ TODOS OS PARAMETROS
Xmin_1 = Xmin.copy()
Xmax_1 = Xmax.copy()
X1, F1 = dds.dds(Xmin_1, Xmax_1, fobj_nse, r=0.2, m=1000)
Qsim_1 = sim(X1)


Simul = pd.DataFrame()
Simul['PME'] = PME
Simul['Qobs'] = Qobs
Simul['I_NSE'] = Qsim_1

fig = make_subplots(rows=3, cols=1, shared_xaxes=True, specs=[[{'rowspan': 1, 'colspan': 1}],[{'rowspan': 2, 'colspan': 1}],[{'rowspan': 0, 'colspan': 0}]])
fig.add_trace(go.Scatter(x=Simul.index, y=Simul['PME'], name="PME (mm)"), row=1, col=1)
fig['layout']['yaxis']['autorange'] = "reversed"
#fig.add_trace(go.Scatter(x=PEQ.index, y=ETP, name="ETP (mm)"), row=1, col=1)
fig.add_trace(go.Scatter(x=Simul.index, y=Simul['Qobs'], name="Qobs (m3/s)", marker_color='black'), row=2, col=1)
fig.add_trace(go.Scatter(x=Simul.index, y=Simul['I_NSE'], name='Qsim - NSE', marker_color='green'), row=2, col=1)
fig.update_yaxes(title_text='Chuva [mm]', row=1, col=1)
fig.update_yaxes(title_text='Vazão [m3s-1]', row=2, col=1)
fig.update_layout(legend_title_text='Comparação Modelo IPH2')
fig.update_layout(autosize=False,width=800,height=450,margin=dict(l=30,r=30,b=10,t=10))
fig.show()

df_params = pd.DataFrame()
df_params['Parametros'] = Xnomes
df_params['Par_NSE'] = X1


df_params.to_csv(f'./Parametros/param_iph2_{bn}_{bnome}.csv', index=False)

Simul = Simul.loc['2018':'2019']

print('Nash I_NSE = ' + str(he.nse(Simul['I_NSE'],Simul['Qobs'])))
print('Log-Nash I_NSE = ' + str(he.nse(np.log(Simul['I_NSE']),np.log(Simul['Qobs']))))
print('PBIAS I_NSE = ' + str(hv.evaluator(hv.pbias,Simul['I_NSE'],Simul['Qobs'])))
