import pandas as pd
import numpy as np
import csv
import datetime as dt
import plotly.graph_objects as go


bacia_nome = 'Foz_do_Areia_mod'
sig_bacia = 'GBM'
cod_bacia = '12'
area_inc = '5937'

precip = pd.read_csv(f'./Dados_Usinas/{cod_bacia}_{bacia_nome}_PME.csv',
                     index_col = 0, parse_dates=True)
precip.columns = ['pme']
data_inicial = precip.index[0]
data_final = precip.index[-1]


vazao_usina = pd.read_excel(f'./Dados_Usinas/vazao_horaria_gmb.xlsx',
                            skiprows = [0,1,2,4])
vazao_usina = vazao_usina.iloc[:, [0,4]]
vazao_usina.columns = ['datahora', 'qaflu']
vazao_usina[['data','hora']] = vazao_usina.datahora.str.split(expand=True)
vazao_usina = vazao_usina.drop('datahora', axis=1)
vazao_usina['data2'] = np.where((vazao_usina['hora'] == '24'),
                                   pd.to_datetime(vazao_usina['data'], dayfirst=True) + dt.timedelta(days=1),
                                   pd.to_datetime(vazao_usina['data'], dayfirst=True))
vazao_usina['hora2'] = np.where((vazao_usina['hora'] == '24'), 0, vazao_usina['hora'].astype(int))
vazao_usina['qaflu'] = np.where((vazao_usina.qaflu.str.contains('S/L', na=False)), np.nan, vazao_usina['qaflu'])
vazao_usina['qaflu'] = vazao_usina['qaflu'].astype(float)
vazao_usina.index = vazao_usina['data2'] + pd.to_timedelta(vazao_usina['hora2'], unit='H')
vazao_usina = vazao_usina.drop(['data', 'hora', 'data2', 'hora2'], axis=1)
vazao_usina.index = ((vazao_usina.index + dt.timedelta(hours=3)).tz_localize('utc')).rename('datahora')
vazao_usina = vazao_usina.where(vazao_usina >= 0)

vazao = pd.DataFrame(vazao_usina['qaflu'])
#Período com dados estranhos
#vazao['Qaflu'].loc['2019-09':'2020-04'] = np.nan
vazao['qjus'] = vazao['qaflu'].rolling(window=24, min_periods=1).mean()
if vazao.index[0] > data_inicial:
    data_inicial = vazao.index[0]
if vazao.index[-1] < data_final:
    data_final = vazao.index[-1]

dados_peq = pd.merge(precip, vazao, how = 'outer',
                 left_index = True, right_index = True)

dados_mont = pd.read_csv(f'./Dados_Horarios/09_Uniao_da_Vitoria_HR.csv',
                         index_col = 0, parse_dates=True)
dados_mont.columns = ['qmon', 'h_m']
if dados_mont.index[0] > data_inicial:
    data_inicial = dados_mont.index[0]
if dados_mont.index[-1] < data_final:
    data_final = dados_mont.index[-1]

dados_peq = pd.merge(dados_peq, dados_mont['qmon'], how = 'outer',
                 left_index = True, right_index = True)
dados_peq = dados_peq.loc[data_inicial:data_final]

etp = pd.read_csv(f'./ETP/etpclim_{cod_bacia}.txt', header = None)
etp['Mes'] = etp[0].str.slice(0,2)
etp['Dia'] = etp[0].str.slice(3,5)
etp['Hora'] = etp[0].str.slice(6,8)
etp['etp'] = pd.to_numeric(etp[0].str.slice(9,17))
etp = etp.drop([0], axis=1)
etp.index = etp['Mes'] + '-' + etp['Dia'] + '-' + etp['Hora']

dados_peq['data'] = dados_peq.index.strftime('%m-%d-%H')
dados_peq['etp'] = dados_peq['data'].map(etp['etp'])
dados_peq = dados_peq.drop(['data'], axis=1)
dados_peq = dados_peq[['pme','etp','qaflu','qjus','qmon']]

dados_6hrs = (dados_peq.resample("6H", closed='right', label = 'right').
              agg({'pme':np.sum, 'etp':np.sum, 'qaflu':np.mean,
                   'qjus':np.mean, 'qmon':np.mean}))
dados_6hrs = dados_6hrs.iloc[1:]

dados_6hrs['qmon'] = dados_6hrs['qmon'].interpolate(method='spline', order=3)

dados_6hrs['pme'] = dados_6hrs['pme'].apply('{:.2f}'.format)
dados_6hrs['etp'] = dados_6hrs['etp'].apply('{:.3f}'.format)
dados_6hrs['qaflu'] = dados_6hrs['qaflu'].apply('{:.3f}'.format)
dados_6hrs['qjus'] = dados_6hrs['qjus'].apply('{:.3f}'.format)
dados_6hrs['qmon'] = dados_6hrs['qmon'].apply('{:.3f}'.format)

with open(f'./PEQ/{cod_bacia}_{bacia_nome}_peq.csv', 'w', newline = '') as file:
    writer = csv.writer(file)
    writer.writerow([area_inc])
dados_6hrs.to_csv(f'./PEQ/{cod_bacia}_{bacia_nome}_peq.csv', mode = 'a',
                 date_format='%Y-%m-%dT%H:%M:%S+00:00', sep = ",")
print('Finalizado PEQ - ' + cod_bacia + ' - ' + bacia_nome)

fig = go.Figure()
fig.add_trace(go.Scatter(x=dados_6hrs.index, y=dados_6hrs['qmon'], name="Q montante (m3/s)", marker_color='blue'))
fig.add_trace(go.Scatter(x=dados_6hrs.index, y=dados_6hrs['qaflu'], name="Q afluente (m3/s)", marker_color='purple'))
fig.add_trace(go.Scatter(x=dados_6hrs.index, y=dados_6hrs['qjus'], name="Q 24 (m3/s)", marker_color='red'))
fig.update_yaxes(title_text='Vazão [m3s-1]')
fig.update_xaxes(tickformat="%Y-%m-%d %H")
fig.update_layout(autosize=False,width=800,height=400,margin=dict(l=30,r=30,b=10,t=10))
fig.write_html(f'./Dados_Usinas/comp_{bacia_nome}.html')
#fig.write_image(f'./Resultados/{dispara.month:02d}_{dispara.day:02d}/{sigla}.png')
fig.show()
