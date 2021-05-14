import pandas as pd
import numpy as np
import math
import sacsma2021
import datetime
from sacsma2021 import Xnomes, Xmin, Xmax
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import HydroErr as he
import hydroeval as hv

def sim(X):
    params = X
    Qsim = sacsma2021.simulacao(area, dt, PME, ETP, params)
    Qsim = pd.Series(index=idx, data=Qsim, name='qsim')
    return Qsim

### LEITURA FORÇANTES
bn = 15
bnome = 'Aguas_do_Vere'
area = pd.read_csv(f'../PEQ/{bn:02d}_{bnome}_peq.csv', nrows=1, header=None).values[0][0]
dt = 0.25 # 6 hr
PEQ = pd.read_csv(f'../PEQ/{bn:02d}_{bnome}_peq.csv', skiprows=1,
                  parse_dates=True, index_col='datahora')
PME = PEQ['pme']
ETP = PEQ['etp']
Qobs = PEQ['qjus'].rename('qobs')
idx = PME.index

params = pd.read_csv(f'./param_macs/param_macs_{bn:02d}_{bnome}.csv',
                     index_col='Parametros')

Simul = pd.DataFrame()
Simul['MACS'] = sim(params['Par_MACS'])
Simul['NSE'] = pd.DataFrame(sim(params['Par_NSE']))
Qsim_ant = pd.read_csv(f'../Simul_Antigo/{bn:02d}_{bnome}_sim_ant.csv',
                       parse_dates=True, index_col='datahora')
Qobs_ant = pd.read_csv(f'../PEQ_hr/{bn:02d}_{bnome}_peq_hr.csv', skiprows=1,
                       parse_dates=True, index_col='datahora')

fig = make_subplots(rows=3, cols=1, shared_xaxes=True, specs=[[{'rowspan': 1, 'colspan': 1}],[{'rowspan': 2, 'colspan': 1}],[{'rowspan': 0, 'colspan': 0}]])
fig.add_trace(go.Scatter(x=PME.index, y=PME, name="PME (mm)"), row=1, col=1)
fig['layout']['yaxis']['autorange'] = "reversed"
#fig.add_trace(go.Scatter(x=PEQ.index, y=ETP, name="ETP (mm)"), row=1, col=1)
fig.add_trace(go.Scatter(x=Qobs.index, y=Qobs, name="Qobs (m3/s)", marker_color='black'), row=2, col=1)
fig.add_trace(go.Scatter(x=Simul.index, y=Simul['MACS'], name='Calibração MACS', marker_color='green'), row=2, col=1)
fig.add_trace(go.Scatter(x=Simul.index, y=Simul['NSE'], name='Calibração NSE', marker_color='red'), row=2, col=1)
fig.add_trace(go.Scatter(x=Qsim_ant.index, y=Qsim_ant['qsim_antigo'], name='Operacional', marker_color='purple'), row=2, col=1)
fig.update_yaxes(title_text='Chuva [mm]', row=1, col=1)
fig.update_yaxes(title_text='Vazão [m3s-1]', row=2, col=1)
fig.update_layout(legend_title_text='Comparação Modelo Sacramento')
fig.update_layout(autosize=False,width=800,height=450,margin=dict(l=30,r=30,b=10,t=10))
fig.write_html(f'./param_macs/teste_calib_{bn:02d}_{bnome}.html')
fig.show()

Simul = Simul.loc['2018':'2021']
Qobs = Qobs.loc['2018':'2021']
Qsim_ant = Qsim_ant.loc['2018':'2021']
Qobs_ant = Qobs_ant.loc['2018':'2021']
PME = PME.loc['2018':'2021']

print('Nash MACS = ' + str(he.nse(Simul['MACS'],Qobs)))
print('Log-Nash MACS = ' + str(he.nse(np.log(Simul['MACS']),np.log(Qobs))))
print('PBIAS MACS = ' + str(hv.evaluator(hv.pbias,Simul['MACS'],Qobs)))

print('Nash NSE = ' + str(he.nse(Simul['NSE'],Qobs)))
print('Log-Nash NSE = ' + str(he.nse(np.log(Simul['NSE']),np.log(Qobs))))
print('PBIAS NSE = ' + str(hv.evaluator(hv.pbias,Simul['NSE'],Qobs)))

print('Nash Antigo = ' + str(he.nse(Qsim_ant['qsim_antigo'],Qobs_ant['qjus'])))
print('Log-Nash Antigo = ' + str(he.nse(np.log(Qsim_ant['qsim_antigo']),np.log(Qobs_ant['qjus']))))
print('PBIAS Antigo = ' + str(hv.evaluator(hv.pbias,Qsim_ant['qsim_antigo'],Qobs_ant['qjus'])))
