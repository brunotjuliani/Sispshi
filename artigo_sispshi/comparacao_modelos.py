import pandas as pd
import numpy as np
import math
import sacsma2021
import gr5i
import hymod
import smap
import iph2
import datetime
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import HydroErr as he
import hydroeval as hv

def sac(X):
    params = X
    Qsim = sacsma2021.simulacao(area, dt_sac, PME, ETP, params)
    Qsim = pd.Series(index=idx, data=Qsim, name='qsim')
    return Qsim

def gr4(X):
    params = X
    Qsim = gr5i.gr5i(area, dt_gr, PME, ETP, params)
    Qsim = pd.Series(index=idx, data=Qsim, name='qsim')
    return Qsim

def hymod_f(X):
    params = X
    Qsim = hymod.HYMOD_CAL(PME, ETP, params)
    Qsim = pd.Series(index=idx, data=Qsim, name='qsim')
    return Qsim

def smap_f(X):
    params = X
    Qsim = smap.SMAP(area, dt_smap, PME, ETP, params)
    Qsim = pd.Series(index=idx, data=Qsim, name='qsim')
    return Qsim

def iph2_f(X):
    params = X
    Qsim = iph2.IPH2(area, dt_iph2, PME, ETP, params)
    Qsim = pd.Series(index=idx, data=Qsim, name='qsim')
    return Qsim

### LEITURA FORÇANTES
bn = 10
bnome = 'Madereira_Gavazzoni'
area = pd.read_csv(f'./PEQ/{bn:02d}_{bnome}_peq_diario.csv', nrows=1, header=None).values[0][0]
# DTs diários para cada modelo
dt_sac = 1
dt_gr = 24
dt_smap = 86400
dt_iph2 = 24

PEQ = pd.read_csv(f'./PEQ/{bn:02d}_{bnome}_peq_diario.csv', skiprows=1,
                  parse_dates=True, index_col='datahora')

fwidths = [6,6,6,12]
Obs = pd.read_fwf(f'./MGB/obs_{bnome}.txt', widths = fwidths,
                  names = ["day", "month", "year", "obs"])
Obs.set_index(pd.to_datetime(Obs[["year", "month", "day"]]), inplace=True)
Obs[Obs['obs']<0] = np.nan
Obs = Obs.loc['2017':'2020']

Simul = pd.DataFrame()
Simul['Q_obs'] = Obs['obs']
#Simul['Q_obs2'] = PEQ['qjus']
Simul['pme'] = PEQ['pme']
Simul['etp'] = PEQ['etp']
PME = Simul['pme']
ETP = Simul['etp']
idx = Simul.index

MGB = pd.read_fwf(f'./MGB/SIM_{bnome}.TXT', widths = fwidths,
                  names = ["day", "month", "year", "sim"])
MGB.set_index(pd.to_datetime(MGB[["year", "month", "day"]]), inplace=True)
Simul['MGB'] = MGB['sim']

params_sac = pd.read_csv(f'./Parametros/param_sac_{bn:02d}_{bnome}.csv', index_col='Parametros')
Simul['SAC'] = sac(params_sac['Par_MACS'])

params_sac = pd.read_csv(f'./Parametros/param_sac_{bn:02d}_{bnome}.csv', index_col='Parametros')
Simul['SAC'] = sac(params_sac['Par_MACS'])

params_gr = pd.read_csv(f'./Parametros/param_gr5i_{bn:02d}_{bnome}.csv', index_col='Parametros')
Simul['GR4'] = gr4(params_gr['Par_GR4'])

params_hym = pd.read_csv(f'./Parametros/param_hymod_{bn:02d}_{bnome}.csv', index_col='Parametros')
Simul['HYMOD'] = hymod_f(params_hym['Par_NSE'])

params_smap = pd.read_csv(f'./Parametros/param_smap_{bn:02d}_{bnome}.csv', index_col='Parametros')
Simul['SMAP'] = smap_f(params_smap['Par_NSE'])

params_iph2 = pd.read_csv(f'./Parametros/param_iph2_{bn:02d}_{bnome}.csv', index_col='Parametros')
Simul['IPH2'] = iph2_f(params_iph2['Par_NSE'])

Simul.round(3).to_csv(f'./Parametros/simul_{bn:02d}_{bnome}.csv', index_label='data')

Simul = Simul.loc['2020-07':]

fig = make_subplots(rows=3, cols=1, shared_xaxes=True, specs=[[{'rowspan': 1, 'colspan': 1}],[{'rowspan': 2, 'colspan': 1}],[{'rowspan': 0, 'colspan': 0}]])
fig.add_trace(go.Scatter(x=Simul.index, y=Simul['pme'], name="PME (mm)"), row=1, col=1)
fig['layout']['yaxis']['autorange'] = "reversed"
fig.add_trace(go.Scatter(x=Simul.index, y=Simul['Q_obs'], name="Qobs (m3/s)", marker_color='black'), row=2, col=1)
fig.add_trace(go.Scatter(x=Simul.index, y=Simul['MGB'], name='MGB', marker_color='green'), row=2, col=1)
fig.add_trace(go.Scatter(x=Simul.index, y=Simul['SAC'], name='Sacramento', marker_color='red'), row=2, col=1)
fig.add_trace(go.Scatter(x=Simul.index, y=Simul['GR4'], name='GR4J', marker_color='purple'), row=2, col=1)
fig.add_trace(go.Scatter(x=Simul.index, y=Simul['HYMOD'], name='Hymod', marker_color='blue'), row=2, col=1)
fig.add_trace(go.Scatter(x=Simul.index, y=Simul['SMAP'], name='Smap', marker_color='orange'), row=2, col=1)
fig.add_trace(go.Scatter(x=Simul.index, y=Simul['IPH2'], name='iph-2', marker_color='orangered'), row=2, col=1)
fig.update_yaxes(title_text='Chuva [mm]', row=1, col=1)
fig.update_yaxes(title_text='Vazão [m3s-1]', row=2, col=1)
fig.update_layout(legend_title_text=f'Comparação Madereira Gavazzoni')
fig.update_layout(autosize=False,width=1200,height=675,margin=dict(l=30,r=30,b=10,t=10))
fig.write_image(f'./Parametros/imagem_{bn:02d}_{bnome}.png')
# fig.update_layout(autosize=False,width=1500,height=750,margin=dict(l=30,r=30,b=10,t=10))
# fig.write_html(f'./Parametros/teste_calib_{bn:02d}_{bnome}.html')
fig.show()

# metricas_2020 = pd.DataFrame(index=['MGB', 'SAC', 'GR4J', 'HYMOD', 'SMAP', 'IPH2'])
# metricas_2020.index.names = ['2018:2020']
#
# mgb_nse = he.nse(Simul['MGB'], Simul['Q_obs'])
# sac_nse = he.nse(Simul['SAC'], Simul['Q_obs'])
# gr4_nse = he.nse(Simul['GR4'], Simul['Q_obs'])
# hym_nse = he.nse(Simul['HYMOD'], Simul['Q_obs'])
# smap_nse = he.nse(Simul['SMAP'], Simul['Q_obs'])
# iph2_nse = he.nse(Simul['IPH2'], Simul['Q_obs'])
# metricas_2020['NSE'] = [mgb_nse, sac_nse, gr4_nse, hym_nse, smap_nse, iph2_nse]
#
# mgb_lognse = he.nse(np.log(Simul['MGB']), np.log(Simul['Q_obs']))
# sac_lognse = he.nse(np.log(Simul['SAC']), np.log(Simul['Q_obs']))
# gr4_lognse = he.nse(np.log(Simul['GR4']), np.log(Simul['Q_obs']))
# hym_lognse = he.nse(np.log(Simul['HYMOD']), np.log(Simul['Q_obs']))
# smap_lognse = he.nse(np.log(Simul['SMAP']), np.log(Simul['Q_obs']))
# iph2_lognse = he.nse(np.log(Simul['IPH2']), np.log(Simul['Q_obs']))
# metricas_2020['Log-NSE'] = [mgb_lognse, sac_lognse, gr4_lognse,
#                             hym_lognse, smap_lognse, iph2_lognse]
#
# mgb_kge = he.kge_2012(Simul['MGB'], Simul['Q_obs'])
# sac_kge = he.kge_2012(Simul['SAC'], Simul['Q_obs'])
# gr4_kge = he.kge_2012(Simul['GR4'], Simul['Q_obs'])
# hym_kge = he.kge_2012(Simul['HYMOD'], Simul['Q_obs'])
# smap_kge = he.kge_2012(Simul['SMAP'], Simul['Q_obs'])
# iph2_kge = he.kge_2012(Simul['IPH2'], Simul['Q_obs'])
# metricas_2020['KGE'] = [mgb_kge, sac_kge, gr4_kge, hym_kge, smap_kge, iph2_kge]
#
# mgb_pbias = hv.evaluator(hv.pbias,Simul['MGB'],Simul['Q_obs'])[0]
# sac_pbias = hv.evaluator(hv.pbias,Simul['SAC'],Simul['Q_obs'])[0]
# gr4_pbias = hv.evaluator(hv.pbias,Simul['GR4'],Simul['Q_obs'])[0]
# hym_pbias = hv.evaluator(hv.pbias,Simul['HYMOD'],Simul['Q_obs'])[0]
# smap_pbias = hv.evaluator(hv.pbias,Simul['SMAP'],Simul['Q_obs'])[0]
# iph2_pbias = hv.evaluator(hv.pbias,Simul['IPH2'],Simul['Q_obs'])[0]
# metricas_2020['PBIAS(%)'] = [mgb_pbias, sac_pbias, gr4_pbias,
#                           hym_pbias, smap_pbias, iph2_pbias]
#
# metricas_2020 = metricas_2020.round(3)
#
#
# Simul = Simul.loc['2018':'2019']
# metricas_2019 = pd.DataFrame(index=['MGB', 'SAC', 'GR4J', 'HYMOD', 'SMAP', 'IPH2'])
# metricas_2019.index.names = ['2018:2019']
#
# mgb_nse = he.nse(Simul['MGB'], Simul['Q_obs'])
# sac_nse = he.nse(Simul['SAC'], Simul['Q_obs'])
# gr4_nse = he.nse(Simul['GR4'], Simul['Q_obs'])
# hym_nse = he.nse(Simul['HYMOD'], Simul['Q_obs'])
# smap_nse = he.nse(Simul['SMAP'], Simul['Q_obs'])
# iph2_nse = he.nse(Simul['IPH2'], Simul['Q_obs'])
# metricas_2019['NSE'] = [mgb_nse, sac_nse, gr4_nse, hym_nse, smap_nse, iph2_nse]
#
# mgb_lognse = he.nse(np.log(Simul['MGB']), np.log(Simul['Q_obs']))
# sac_lognse = he.nse(np.log(Simul['SAC']), np.log(Simul['Q_obs']))
# gr4_lognse = he.nse(np.log(Simul['GR4']), np.log(Simul['Q_obs']))
# hym_lognse = he.nse(np.log(Simul['HYMOD']), np.log(Simul['Q_obs']))
# smap_lognse = he.nse(np.log(Simul['SMAP']), np.log(Simul['Q_obs']))
# iph2_lognse = he.nse(np.log(Simul['IPH2']), np.log(Simul['Q_obs']))
# metricas_2019['Log-NSE'] = [mgb_lognse, sac_lognse, gr4_lognse,
#                             hym_lognse, smap_lognse, iph2_lognse]
#
# mgb_kge = he.kge_2012(Simul['MGB'], Simul['Q_obs'])
# sac_kge = he.kge_2012(Simul['SAC'], Simul['Q_obs'])
# gr4_kge = he.kge_2012(Simul['GR4'], Simul['Q_obs'])
# hym_kge = he.kge_2012(Simul['HYMOD'], Simul['Q_obs'])
# smap_kge = he.kge_2012(Simul['SMAP'], Simul['Q_obs'])
# iph2_kge = he.kge_2012(Simul['IPH2'], Simul['Q_obs'])
# metricas_2019['KGE'] = [mgb_kge, sac_kge, gr4_kge, hym_kge, smap_kge, iph2_kge]
#
# mgb_pbias = hv.evaluator(hv.pbias,Simul['MGB'],Simul['Q_obs'])[0]
# sac_pbias = hv.evaluator(hv.pbias,Simul['SAC'],Simul['Q_obs'])[0]
# gr4_pbias = hv.evaluator(hv.pbias,Simul['GR4'],Simul['Q_obs'])[0]
# hym_pbias = hv.evaluator(hv.pbias,Simul['HYMOD'],Simul['Q_obs'])[0]
# smap_pbias = hv.evaluator(hv.pbias,Simul['SMAP'],Simul['Q_obs'])[0]
# iph2_pbias = hv.evaluator(hv.pbias,Simul['IPH2'],Simul['Q_obs'])[0]
# metricas_2019['PBIAS(%)'] = [mgb_pbias, sac_pbias, gr4_pbias,
#                           hym_pbias, smap_pbias, iph2_pbias]
#
# metricas_2019 = metricas_2019.round(3)
# metricas_2019.to_csv(f'./Parametros/metricas_{bn:02d}_{bnome}.csv')
#
#
# print(metricas_2019)
# print(metricas_2020)
