import pandas as pd
from spotpy.analyser import *
from spotpy.algorithms import sceua
import sispshi_sacsma2021 as sacsma2021
import sispshi_gr5i as gr5i
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import HydroErr as he

n_bacia = 5
nome = 'Santa_Cruz_Timbo'

_# FORCANTES
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

#periodo de validação
t1_cal = pd.Timestamp('2018', tz='UTC')
idx_cal = idx[idx >= t1_cal]

# CALIBRACAO 01 - LOG - Lower Zone
spot_setup_1 = sacsma2021.spotpy_1(area, dt, PME, ETP, Qjus, idx, idx_cal, Qmon=Qmon, fobj='LOG')
sampler_1 = sceua(spot_setup_1)
# sampler.sample(100)
sampler_1.sample(8000, ngs=15, kstop=1, peps=0.1, pcento=5)
results_1 = sampler_1.getdata()
params_1 = get_best_parameterset(results_1, maximize=False)
params_nomes_1 = list(params_1.dtype.names)
params_valores_1 = list(params_1[0])
DF_params_1 = pd.DataFrame(data=params_valores_1, index=params_nomes_1, columns=['valor'])
DF_params_1.to_csv('sispshi_params1.csv')
bestindex_1, bestobjf_1 = get_minlikeindex(results_1)
simulation_fields_1 = get_simulation_fields(results_1)
Qsim_1 = list(results_1[simulation_fields_1][bestindex_1])
Qsim_1

# CALIBRACAO 02 - DRMS - Upper Zone
spot_setup_2 = sacsma2021.spotpy_2(area, dt, PME, ETP, Qjus, idx, idx_cal, Qmon=Qmon, fobj='DRMS')
sampler_2 = sceua(spot_setup_2)
sampler_2.sample(8000, ngs=15, kstop=1, peps=0.1, pcento=5)
results_2 = sampler_2.getdata()
params_2 = get_best_parameterset(results_2, maximize=False)
params_nomes_2 = list(params_2.dtype.names)
params_valores_2 = list(params_2[0])
DF_params_2 = pd.DataFrame(data=params_valores_2, index=params_nomes_2, columns=['valor'])
DF_params_2.to_csv('sispshi_params2.csv')
bestindex_2, bestobjf_2 = get_minlikeindex(results_2)
simulation_fields_2 = get_simulation_fields(results_2)
Qsim_2 = list(results_2[simulation_fields_2][bestindex_2])

# CALIBRACAO 03 - LOG - Refina Lower Zone
spot_setup_3 = sacsma2021.spotpy_3(area, dt, PME, ETP, Qjus, idx, idx_cal, Qmon=Qmon, fobj='LOG')
sampler_3 = sceua(spot_setup_3)
sampler_3.sample(8000, ngs=15, kstop=1, peps=0.1, pcento=5)
results_3 = sampler_3.getdata()
params_3 = get_best_parameterset(results_3, maximize=False)
params_nomes_3 = list(params_3.dtype.names)
params_valores_3 = list(params_3[0])
DF_params_3 = pd.DataFrame(data=params_valores_3, index=params_nomes_3, columns=['valor'])
DF_params_3.to_csv('sispshi_params3.csv')
bestindex_3, bestobjf_3 = get_minlikeindex(results_3)
simulation_fields_3 = get_simulation_fields(results_3)
Qsim_3 = list(results_3[simulation_fields_3][bestindex_3])

# CALIBRACAO 04 - NASH
spot_setup_4 = sacsma2021.spotpy_4(area, dt, PME, ETP, Qjus, idx, idx_cal, Qmon=Qmon, fobj='NSE')
sampler_4 = sceua(spot_setup_4)
sampler_4.sample(8000, ngs=15, kstop=1, peps=0.1, pcento=5)
results_4 = sampler_4.getdata()
params_4 = get_best_parameterset(results_4, maximize=False)
params_nomes_4 = list(params_4.dtype.names)
params_valores_4 = list(params_4[0])
DF_params_4 = pd.DataFrame(data=params_valores_4, index=params_nomes_4, columns=['valor'])
DF_params_4.to_csv('sispshi_params4.csv')
bestindex_4, bestobjf_4 = get_minlikeindex(results_4)
simulation_fields_4 = get_simulation_fields(results_4)
Qsim_4 = list(results_4[simulation_fields_4][bestindex_4])

# CALIBRACAO GR5i
dt = 6
spot_setup_gr = gr5i.spotpy(area, dt, PME, ETP, Qjus, idx, idx_cal, Qmon=Qmon, fobj='NSE')
sampler_gr = sceua(spot_setup_gr)
sampler_gr.sample(8000, ngs=15, kstop=1, peps=0.1, pcento=5)
results_gr = sampler_gr.getdata()
params_gr = get_best_parameterset(results_gr, maximize=False)
params_nomes_gr = list(params_gr.dtype.names)
params_valores_gr = list(params_gr[0])
DF_params_gr = pd.DataFrame(data=params_valores_gr, index=params_nomes_gr, columns=['valor'])
DF_params_gr.to_csv('sispshi_paramsgr.csv')
bestindex_gr, bestobjf_gr = get_minlikeindex(results_gr)
simulation_fields_gr = get_simulation_fields(results_gr)
Qsim_gr = list(results_gr[simulation_fields_gr][bestindex_gr])

fig = make_subplots(rows=3, cols=1, shared_xaxes=True, specs=[[{'rowspan': 1, 'colspan': 1}],[{'rowspan': 2, 'colspan': 1}],[{'rowspan': 0, 'colspan': 0}]])
fig.add_trace(go.Scatter(x=idx, y=PME, name="PME (mm)"), row=1, col=1)
fig['layout']['yaxis']['autorange'] = "reversed"
#fig.add_trace(go.Scatter(x=PEQ.index, y=ETP, name="ETP (mm)"), row=1, col=1)
fig.add_trace(go.Scatter(x=idx, y=Qjus, name="Qobs (m3/s)", marker_color='black'), row=2, col=1)
#fig['data'][2]['line']['color']="black"
fig.add_trace(go.Scatter(x=idx, y=Qsim_1, name='Qsim - 1', marker_color='green'), row=2, col=1)
fig.add_trace(go.Scatter(x=idx, y=Qsim_2, name='Qsim - 2', marker_color='red'), row=2, col=1)
fig.add_trace(go.Scatter(x=idx, y=Qsim_3, name='Qsim - 3', marker_color='purple'), row=2, col=1)
fig.add_trace(go.Scatter(x=idx, y=Qsim_4, name='Qsim - 4 (NSE)', marker_color='orange'), row=2, col=1)
fig.add_trace(go.Scatter(x=idx, y=Qsim_gr, name='Qsim - GR5i (NSE)', marker_color='blue'), row=2, col=1)
fig.update_yaxes(title_text='Chuva [mm]', row=1, col=1)
fig.update_yaxes(title_text='Vazão [m3s-1]', row=2, col=1)
fig.update_layout(legend_title_text='Comparação Modelo Sacramento')
fig.update_layout(autosize=False,width=800,height=450,margin=dict(l=30,r=30,b=10,t=10))
fig.show()

#AVALIAÇÃO
simul = pd.DataFrame(data=[Qsim_1, Qsim_3, Qsim_4, Qsim_gr]).T
simul.index = idx
simul.columns = ['Qsim_1', 'Qsim_3', 'Qsim_4', 'Qsim_gr']

##CORTE DE TEMPO PARA NASH E PLOTAGEM##
df = pd.merge(PEQ['qjus'], simul, how = 'outer',
              left_index = True, right_index = True)
df = pd.merge(df, PEQ['pme'], how = 'outer',
              left_index = True, right_index = True)
df2 = df.loc['2019':'2020']
#print('Período: 01/2014 - 06/2014')
df2

nash_log = he.nse(df2['qjus'],df2['Qsim_1'])
print('Nash Sac LOG = ' + str(nash_log))

nash_macs = he.nse(df2['qjus'],df2['Qsim_3'])
print('Nash Sac MACS = ' + str(nash_macs))

nash_nse = he.nse(df2['qjus'],df2['Qsim_4'])
print('Nash Sac NSE = ' + str(nash_nse))

nash_gr_nse = he.nse(df2['qjus'],df2['Qsim_gr'])
print('Nash GR5i NSE = ' + str(nash_gr_nse))
