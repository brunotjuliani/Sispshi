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
bn = 12
bnome = 'Foz_do_Areia_mod'
area = pd.read_csv(f'../PEQ/{bn:02d}_{bnome}_peq.csv', nrows=1, header=None).values[0][0]
dt = 0.25 # 6 hr
PEQ = pd.read_csv(f'../PEQ/{bn:02d}_{bnome}_peq.csv', skiprows=1,
                  parse_dates=True, index_col='datahora')
PEQ['Q0'] = 0
PME = PEQ['pme']
ETP = PEQ['etp']
Qobs = (PEQ['qjus'] - PEQ['qmon']).rename('qobs')
Qobs[Qobs < 0] = 0.1
Qmon = PEQ['Q0'].rename('qmon')
idx = PME.index

params = pd.read_csv(f'./param_macs/param_macs_{bn:02d}_{bnome}_incremental.csv',
                     index_col='Parametros')

Simul = pd.DataFrame()
Simul['MACS'] = sim(params['Par_MACS'])
Simul['NSE'] = pd.DataFrame(sim(params['Par_NSE']))
Simul['Incremental'] = PEQ['qjus'] - PEQ['qmon']

Simul['Qjus'] = PEQ['qjus']
Simul['Qmon'] = PEQ['qmon']
Simul['Qmacs'] = Simul['MACS'] + PEQ['qmon']
Simul['Qnse'] = Simul['NSE'] + PEQ['qmon']

Qsim_ant = pd.read_csv(f'../Simul_Antigo/{bn:02d}_{bnome}_sim_ant.csv',
                       parse_dates=True, index_col='datahora')
Qobs_ant = pd.read_csv(f'../PEQ_hr/{bn:02d}_{bnome}_peq_hr.csv', skiprows=1,
                       parse_dates=True, index_col='datahora')
Qsim_ant['Qobs'] = Qobs_ant['qjus']

PME = PME.loc['2020':]
Simul = Simul.loc['2020':]
Qsim_ant = Qsim_ant.loc['2020':].dropna()
# Simul_Inc = Simul.copy().loc['2015':'2021']
# PME_Inc = PME.copy().loc['2015':'2021']

fig = make_subplots(rows=3, cols=1, shared_xaxes=True, specs=[[{'rowspan': 1, 'colspan': 1}],[{'rowspan': 2, 'colspan': 1}],[{'rowspan': 0, 'colspan': 0}]])
fig.add_trace(go.Scatter(x=PME.index, y=PME, name="PME (mm)"), row=1, col=1)
fig['layout']['yaxis']['autorange'] = "reversed"
#fig.add_trace(go.Scatter(x=PEQ.index, y=ETP, name="ETP (mm)"), row=1, col=1)
fig.add_trace(go.Scatter(x=Simul.index, y=Simul['Incremental'], name="Incremental Obs. (m3/s)", marker_color='black'), row=2, col=1)
fig.add_trace(go.Scatter(x=Simul.index, y=Simul['MACS'], name='Calibração M.E.', marker_color='green'), row=2, col=1)
fig.add_trace(go.Scatter(x=Simul.index, y=Simul['NSE'], name='Calibração NSE', marker_color='red'), row=2, col=1)
fig.update_yaxes(title_text='Chuva [mm]', row=1, col=1)
fig.update_yaxes(title_text='Vazão [m3s-1]', row=2, col=1)
fig.update_layout(legend_title_text='Comparação Modelo Sacramento')
fig.update_layout(autosize=False,width=1000,height=500,margin=dict(l=30,r=30,b=10,t=10))
#fig.write_html(f'./param_macs/teste_calib_{bn:02d}_{bnome}_incremental.html')
fig.write_image(f'./param_macs/teste_calib_{bn:02d}_{bnome}_incremental.png')
fig.show()


# print('Nash MACS = ' + str(he.nse(Simul_Inc['MACS'],Simul_Inc['Incremental'])))
# print('Log-Nash MACS = ' + str(he.nse(np.log(Simul_Inc['MACS']),np.log(Simul_Inc['Incremental']))))
# print('PBIAS MACS = ' + str(hv.evaluator(hv.pbias,Simul_Inc['MACS'],Simul_Inc['Incremental'])))
#
# print('Nash NSE = ' + str(he.nse(Simul_Inc['NSE'],Simul_Inc['Incremental'])))
# print('Log-Nash NSE = ' + str(he.nse(np.log(Simul_Inc['NSE']),np.log(Simul_Inc['Incremental']))))
# print('PBIAS NSE = ' + str(hv.evaluator(hv.pbias,Simul_Inc['NSE'],Simul_Inc['Incremental'])))




# fig = make_subplots(rows=3, cols=1, shared_xaxes=True, specs=[[{'rowspan': 1, 'colspan': 1}],[{'rowspan': 2, 'colspan': 1}],[{'rowspan': 0, 'colspan': 0}]])
# fig.add_trace(go.Scatter(x=PME.index, y=PME, name="PME (mm)"), row=1, col=1)
# fig['layout']['yaxis']['autorange'] = "reversed"
# #fig.add_trace(go.Scatter(x=PEQ.index, y=ETP, name="ETP (mm)"), row=1, col=1)
# fig.add_trace(go.Scatter(x=Simul.index, y=Simul['Qjus'], name="Q Obs. (m3/s)", marker_color='black'), row=2, col=1)
# fig.add_trace(go.Scatter(x=Simul.index, y=Simul['Qmacs'], name='Calibração M.E.', marker_color='green'), row=2, col=1)
# fig.add_trace(go.Scatter(x=Simul.index, y=Simul['Qnse'], name='Calibração NSE', marker_color='red'), row=2, col=1)
# fig.add_trace(go.Scatter(x=Qsim_ant.index, y=Qsim_ant['qsim_antigo'], name='Operacional', marker_color='purple'), row=2, col=1)
# fig.add_trace(go.Scatter(x=Simul.index, y=Simul['Qmon'], name='Q UVA (m3/s)', marker_color='navy'), row=2, col=1)
# fig.update_yaxes(title_text='Chuva [mm]', row=1, col=1)
# fig.update_yaxes(title_text='Vazão [m3s-1]', row=2, col=1)
# fig.update_layout(legend_title_text='Comparação Modelo Sacramento')
# fig.update_layout(autosize=False,width=1000,height=500,margin=dict(l=30,r=30,b=10,t=10))
# #fig.write_html(f'./param_macs/teste_calib_{bn:02d}_{bnome}_total.html')
# fig.write_image(f'./param_macs/teste_calib_{bn:02d}_{bnome}_total.png')
# fig.show()



# print('Nash MACS = ' + str(he.nse(Simul_Inc['Qmacs'],Simul_Inc['Qjus'])))
# print('Log-Nash MACS = ' + str(he.nse(np.log(Simul_Inc['Qmacs']),np.log(Simul_Inc['Qjus']))))
# print('PBIAS MACS = ' + str(hv.evaluator(hv.pbias,Simul_Inc['Qmacs'],Simul_Inc['Qjus'])))
#
# print('Nash NSE = ' + str(he.nse(Simul_Inc['Qnse'],Simul_Inc['Qjus'])))
# print('Log-Nash NSE = ' + str(he.nse(np.log(Simul_Inc['Qnse']),np.log(Simul_Inc['Qjus']))))
# print('PBIAS NSE = ' + str(hv.evaluator(hv.pbias,Simul_Inc['Qnse'],Simul_Inc['Qjus'])))
#
# Ant_6hrs = (Qsim_ant.resample("6H", closed='right', label = 'right').
#               agg({'qsim_antigo':np.mean, 'Qobs':np.mean}))
# print('Nash Antigo = ' + str(he.nse(Ant_6hrs['qsim_antigo'],Ant_6hrs['Qobs'])))
# print('Log-Nash Antigo = ' + str(he.nse(np.log(Ant_6hrs['qsim_antigo']),np.log(Ant_6hrs['Qobs']))))
# print('PBIAS Antigo = ' + str(hv.evaluator(hv.pbias,Ant_6hrs['qsim_antigo'],Ant_6hrs['Qobs'])))
