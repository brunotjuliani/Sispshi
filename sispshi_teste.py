import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sispshi_sacsma2021 as sacsma2021
import sispshi_gr5i as gr5i
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import HydroErr as he

n_bacia = 5
nome = 'Santa_Cruz_Timbo'

# FORCANTES
area = float(pd.read_csv(f'sispshi_{n_bacia:02d}_{nome}_peq.csv', nrows=0).columns[0])
#area = float(pd.read_csv(f'../Dados/PEQ/{n_bacia:02d}_{nome}_peq.csv', nrows=0).columns[0])
dt = 0.25
PEQ = pd.read_csv(f'sispshi_{n_bacia:02d}_{nome}_peq.csv', skiprows=1, index_col='datahora', parse_dates=True)
#PEQ = pd.read_csv(f'../Dados/PEQ/{n_bacia:02d}_{nome}_peq.csv', skiprows=1, index_col='datahora', parse_dates=True)
idx = PEQ.index
PME  = PEQ['pme']
ETP  = PEQ['etp']
Qjus = PEQ['qjus']
Qmon = PEQ['qmon']

#CALIBRAÇÃO LOG
dt = 0.25
params1 = pd.read_csv(f'sispshi_parsac_{n_bacia:02d}.csv', index_col='parNome').to_dict('dict')['parLOG']
Qsim1, Qbfp1, Qbfs1, Qtci1, Qtco1 = sacsma2021.simulacao(area, dt, PME, ETP, params1, Qmon=None, estados=None)

#CALIBRAÇÃO MACS
dt = 0.25
params3 = pd.read_csv(f'sispshi_parsac_{n_bacia:02d}.csv', index_col='parNome').to_dict('dict')['parMACS']
Qsim3, Qbfp3, Qbfs3, Qtci3, Qtco3 = sacsma2021.simulacao(area, dt, PME, ETP, params3, Qmon=None, estados=None)

#CALIBRAÇÃO NASH
dt = 0.25
params4 = pd.read_csv(f'sispshi_parsac_{n_bacia:02d}.csv', index_col='parNome').to_dict('dict')['parNSE']
Qsim4, Qbfp4, Qbfs4, Qtci4, Qtco4 = sacsma2021.simulacao(area, dt, PME, ETP, params4, Qmon=None, estados=None)

#CALIBRAÇÃO GR5i - NASH
dt = 6
paramsgr = pd.read_csv(f'sispshi_pargr5_{n_bacia:02d}.csv', index_col='parNome').to_dict('dict')['parValor']
Qsimgr = gr5i.gr5i(area, dt, PME, ETP, paramsgr, Qmon=None, Estados=None)

#CALIBRAÇÃO GR5i - MANUAL
dt = 6
# paramsgr2 = paramsgr.copy()
# paramsgr2
# paramsgr2['x1'] = 300
# paramsgr2['x2'] = -0.01
# paramsgr2['x3'] = 200
# paramsgr2['x4'] = 8
# paramsgr2['x5'] = 0.80
paramsgr2 = pd.read_csv(f'sispshi_pargr5_{n_bacia:02d}.csv', index_col='parNome').to_dict('dict')['parManual']
Qsimgr2 = gr5i.gr5i(area, dt, PME, ETP, paramsgr2, Qmon=None, Estados=None)

#AVALIAÇÃO
simul = pd.DataFrame(data=[Qsim1, Qsim3, Qsim4, Qsimgr, Qsimgr2]).T
simul.index = idx
simul.columns = ['Qsim1', 'Qsim3', 'Qsim4', 'Qsimgr', 'Qsimgr2']

##CORTE DE TEMPO PARA NASH E PLOTAGEM##
df = pd.merge(PEQ['qjus'], simul, how = 'outer',
              left_index = True, right_index = True)
df = pd.merge(df, PEQ['pme'], how = 'outer',
              left_index = True, right_index = True)
df2 = df.loc['2019':'2020']
#print('Período: 01/2014 - 06/2014')


nash_log = he.nse(df2['qjus'],df2['Qsim1'])
print('Nash Sac LOG = ' + str(nash_log))

nash_macs = he.nse(df2['qjus'],df2['Qsim3'])
print('Nash Sac MACS = ' + str(nash_macs))

nash_nse = he.nse(df2['qjus'],df2['Qsim4'])
print('Nash Sac NSE = ' + str(nash_nse))

nash_gr_nse = he.nse(df2['qjus'],df2['Qsimgr'])
print('Nash GR5i NSE = ' + str(nash_gr_nse))

nash_gr_manual = he.nse(df2['qjus'],df2['Qsimgr2'])
print('Nash GR5i MANUAL = ' + str(nash_gr_manual))

fig = make_subplots(rows=3, cols=1, shared_xaxes=True, specs=[[{'rowspan': 1, 'colspan': 1}],[{'rowspan': 2, 'colspan': 1}],[{'rowspan': 0, 'colspan': 0}]])
fig.add_trace(go.Scatter(x=df2.index, y=df2['pme'], name="PME (mm)"), row=1, col=1)
fig['layout']['yaxis']['autorange'] = "reversed"
#fig.add_trace(go.Scatter(x=PEQ.index, y=ETP, name="ETP (mm)"), row=1, col=1)
fig.add_trace(go.Scatter(x=df2.index, y=df2['qjus'], name="Qobs (m3/s)", marker_color='black'), row=2, col=1)
#fig['data'][2]['line']['color']="black"
fig.add_trace(go.Scatter(x=df2.index, y=df2['Qsim1'], name='SAC - LOG', marker_color='green'), row=2, col=1)
fig.add_trace(go.Scatter(x=df2.index, y=df2['Qsim3'], name='SAC - MACS', marker_color='purple'), row=2, col=1)
fig.add_trace(go.Scatter(x=df2.index, y=df2['Qsim4'], name='SAC - NSE', marker_color='orange'), row=2, col=1)
fig.add_trace(go.Scatter(x=df2.index, y=df2['Qsimgr'], name='GR5i - NSE', marker_color='blue'), row=2, col=1)
fig.add_trace(go.Scatter(x=df2.index, y=df2['Qsimgr2'], name='GR5i - MANUAL', marker_color='red'), row=2, col=1)
fig.update_yaxes(title_text='Chuva [mm]', row=1, col=1)
fig.update_yaxes(title_text='Vazão [m3s-1]', row=2, col=1)
fig.update_layout(autosize=False,width=800,height=450,margin=dict(l=30,r=30,b=10,t=10))
fig.show()



# n_bacia = 1
# nome = 'Rio_Negro'
#
# # FORCANTES
# area = float(pd.read_csv(f'sispshi_{n_bacia:02d}_{nome}_peq.csv', nrows=0).columns[0])
# #area = float(pd.read_csv(f'../Dados/PEQ/{n_bacia:02d}_{nome}_peq.csv', nrows=0).columns[0])
# dt = 0.25
# PEQ = pd.read_csv(f'sispshi_{n_bacia:02d}_{nome}_peq.csv', skiprows=1, index_col='datahora', parse_dates=True)
# #PEQ = pd.read_csv(f'../Dados/PEQ/{n_bacia:02d}_{nome}_peq.csv', skiprows=1, index_col='datahora', parse_dates=True)
# idx = PEQ.index
# PME  = PEQ['siprec']
# ETP  = PEQ['etp']
# Qjus = PEQ['qjus']
# Qmon = PEQ['qmon']
#
# #CALIBRAÇÃO LOG
# dt = 0.25
# params1 = pd.read_csv('sispshi_params1.csv', index_col='parNome').to_dict('dict')['parValor']
# Qsim1, Qbfp1, Qbfs1, Qtci1, Qtco1 = sacsma2021.simulacao(area, dt, PME, ETP, params1, Qmon=None, estados=None)
#
# #CALIBRAÇÃO MACS
# dt = 0.25
# params3 = pd.read_csv('sispshi_params3.csv', index_col='parNome').to_dict('dict')['parValor']
# Qsim3, Qbfp3, Qbfs3, Qtci3, Qtco3 = sacsma2021.simulacao(area, dt, PME, ETP, params3, Qmon=None, estados=None)
#
# #CALIBRAÇÃO NASH
# dt = 0.25
# params4 = pd.read_csv('sispshi_params4.csv', index_col='parNome').to_dict('dict')['parValor']
# Qsim4, Qbfp4, Qbfs4, Qtci4, Qtco4 = sacsma2021.simulacao(area, dt, PME, ETP, params4, Qmon=None, estados=None)
#
# #CALIBRAÇÃO GR5i - NASH
# dt = 6
# paramsgr = pd.read_csv('sispshi_paramsgr.csv', index_col='parNome').to_dict('dict')['parValor']
# Qsimgr = gr5i.gr5i(area, dt, PME, ETP, paramsgr, Qmon=None, Estados=None)
#
# #CALIBRAÇÃO GR5i - MANUAL
# dt = 6
# paramsgr2 = paramsgr.copy()
# paramsgr2
# paramsgr2['x1'] = 650
# paramsgr2['x3'] = 120
# paramsgr2['x4'] = 10
# Qsimgr2 = gr5i.gr5i(area, dt, PME, ETP, paramsgr2, Qmon=None, Estados=None)
#
# #AVALIAÇÃO
# simul = pd.DataFrame(data=[Qsim1, Qsim3, Qsim4, Qsimgr, Qsimgr2]).T
# simul.index = idx
# simul.columns = ['Qsim1', 'Qsim3', 'Qsim4', 'Qsimgr', 'Qsimgr2']
#
# ##CORTE DE TEMPO PARA NASH E PLOTAGEM##
# df = pd.merge(PEQ['qjus'], simul, how = 'outer',
#               left_index = True, right_index = True)
# df = pd.merge(df, PEQ['siprec'], how = 'outer',
#               left_index = True, right_index = True)
# df2 = df.loc['2020-07':'2020-12']
# #print('Período: 01/2014 - 06/2014')
#
#
# nash_log = he.nse(df2['qjus'],df2['Qsim1'])
# print('Nash Sac LOG = ' + str(nash_log))
#
# nash_macs = he.nse(df2['qjus'],df2['Qsim3'])
# print('Nash Sac MACS = ' + str(nash_macs))
#
# nash_nse = he.nse(df2['qjus'],df2['Qsim4'])
# print('Nash Sac NSE = ' + str(nash_nse))
#
# nash_gr_nse = he.nse(df2['qjus'],df2['Qsimgr'])
# print('Nash GR5i NSE = ' + str(nash_gr_nse))
#
# nash_gr_manual = he.nse(df2['qjus'],df2['Qsimgr2'])
# print('Nash GR5i MANUAL = ' + str(nash_gr_manual))
