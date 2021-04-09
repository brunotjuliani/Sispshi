import pandas as pd
import sacsma2021
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import HydroErr as he

# Leitura
PEQ = pd.read_csv('sispshi_01_Rio_Negro_peq.csv', skiprows=1, index_col='datahora', parse_dates=True)
area = pd.read_csv('sispshi_01_Rio_Negro_peq.csv', nrows=1, header=None).values[0][0]
dt = 0.25
PME = PEQ['pme']
PME_Siprec = PEQ['siprec']
ETP = PEQ['etp']
Qjus = PEQ['qjus']
fconv = area/(dt*86.4) # mm -> m3/s

params = pd.read_csv('sispshi_par_sacsma2021_01.csv', index_col='parNome').to_dict('dict')['parValor']
params2 = pd.read_csv('sispshi_par_sacsma2021_01.csv', index_col='parNome').to_dict('dict')['par2']


Qsim, Qbfp, Qbfs, Qtci, Qtco = sacsma2021.simulacao(area, dt, PME, ETP, params, Qmon=None, estados=None)
PEQ['Qsim1'] = Qsim
nash_1 = he.nse(PEQ.loc['2020','qjus'],PEQ.loc['2020','Qsim1'])
print('Nash2020 01 = ' + str(nash_1))

Qsim2, Qbfp2, Qbfs2, Qtci2, Qtco2 = sacsma2021.simulacao(area, dt, PME, ETP, params2, Qmon=None, estados=None)
PEQ['Qsim2'] = Qsim2
nash_2 = he.nse(PEQ.loc['2020','qjus'],PEQ.loc['2020','Qsim2'])
print('Nash2020 02 = ' + str(nash_2))


params3 = pd.read_csv('sispshi_par_sacsma2021_01.csv', index_col='parNome').to_dict('dict')['par3']
params4 = pd.read_csv('sispshi_par_sacsma2021_01.csv', index_col='parNome').to_dict('dict')['par4']

Qsim3, Qbfp3, Qbfs3, Qtci3, Qtco3 = sacsma2021.simulacao(area=area, dt=dt, PME=PME_Siprec, ETP=ETP, params=params3, Qmon=None, estados=None)
PEQ['Qsim3'] = Qsim3
nash_3 = he.nse(PEQ.loc['2020','qjus'],PEQ.loc['2020','Qsim3'])
print('Nash2020 03 = ' + str(nash_3))

Qsim4, Qbfp4, Qbfs4, Qtci4, Qtco4 = sacsma2021.simulacao(area=area, dt=dt, PME=PME_Siprec, ETP=ETP, params=params4, Qmon=None, estados=None)
PEQ['Qsim4'] = Qsim4
nash_4 = he.nse(PEQ.loc['2020','qjus'],PEQ.loc['2020','Qsim4'])
print('Nash2020 04 = ' + str(nash_4))

# Plotagem
fig = make_subplots(rows=3, cols=1, shared_xaxes=True, specs=[[{'rowspan': 1, 'colspan': 1}],[{'rowspan': 2, 'colspan': 1}],[{'rowspan': 0, 'colspan': 0}]])
fig.add_trace(go.Scatter(x=PEQ.index, y=PME, name="PME (mm)"), row=1, col=1)
fig.add_trace(go.Scatter(x=PEQ.index, y=PME_Siprec, name="PME - Siprec (mm)"), row=1, col=1)
fig['layout']['yaxis']['autorange'] = "reversed"
#fig.add_trace(go.Scatter(x=PEQ.index, y=ETP, name="ETP (mm)"), row=1, col=1)
fig.add_trace(go.Scatter(x=PEQ.index, y=Qjus, name="Qobs (m3/s)", marker_color='black'), row=2, col=1)
fig['data'][2]['line']['color']="black"
fig.add_trace(go.Scatter(x=PEQ.index, y=Qsim, name='Qsim - 1 - Espac.', marker_color='green'), row=2, col=1)
fig.add_trace(go.Scatter(x=PEQ.index, y=Qsim2, name='Qsim - 2 - Espac.', marker_color='red'), row=2, col=1)
fig.add_trace(go.Scatter(x=PEQ.index, y=Qsim3, name='Qsim - 3 - Siprec', marker_color='purple'), row=2, col=1)
fig.add_trace(go.Scatter(x=PEQ.index, y=Qsim4, name='Qsim - 4 - Siprec', marker_color='orange'), row=2, col=1)
fig.update_yaxes(title_text='Chuva [mm]', row=1, col=1)
fig.update_yaxes(title_text='Vazão [m3s-1]', row=2, col=1)
fig.update_layout(legend_title_text='Comparação Modelo Sacramento')
fig.update_layout(autosize=False,width=800,height=450,margin=dict(l=30,r=30,b=10,t=10))
fig.show()
