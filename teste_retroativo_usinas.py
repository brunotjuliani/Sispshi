import pandas as pd
import datetime as dt
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import requests
import pytz
import numpy as np


listaUHES = [
	      #['DRJ', 'Derivação Rio Jordão', '30'],
	      ['FCH', 'Foz do Chopim', '6', '1710', '1714'],
	      ['GBM', 'Gov. Bento Munhoz (Foz do Areia)', '1', '1210', '1214'],
	      ['SCL', 'Santa Clara', '31', '1810', '1812'],
	      ['SCX', 'Gov. José Richa (Salto Caxias)', '20', '1910', '1912'],
	      ['SGD', 'Gov. Ney Braga (Segredo)', '24', '1610', '1614'],
	      #['SOS', 'Salto Osório', '53']
	    ]

dispara = dt.datetime(2021, 4, 23, 10, tzinfo=dt.timezone.utc)
datahoraf = dispara + dt.timedelta(days=7)
datahorai = dispara - dt.timedelta(days=7)
datahorai2 = dispara - dt.timedelta(days=8)

 # for UHE in listaUHES:
 #     sigla = UHE[0]
 #     nome  = UHE[1]
 #     ponto = UHE[2]
 #     s_chuva = UHE[3]
 #     c_chuva = UHE[4]

sigla = 'GBM'
nome = 'Gov. Bento Munhoz (Foz do Areia)'
ponto = '1'
s_chuva = '1210'
c_chuva = '1214'

# Coleta dados observados
url = "http://produtos.simepar.br/telemetry-copel/monhid?datahorai={:%Y-%m-%dT%H:%M:%S}&datahoraf={:%Y-%m-%dT%H:%M:%S}&ids={}&tipos=R".format(datahorai2, datahoraf, ponto)
response = requests.get(url=url)
data = response.json()
df = pd.DataFrame.from_dict(data)
df = df.set_index(pd.to_datetime(df.datahora))
df2 = pd.DataFrame()
for row in df.itertuples():
    try:
        df2.loc[row[0],'Qobs'] = row[3]['vazaoAfluente']
    except:
        df2.loc[row[0],'Qobs'] = np.nan
df2[df2['Qobs'] < 0] = np.nan

df2 = df2.sort_index()
df2['M_24'] = df2['Qobs'].rolling(window=24, min_periods=1).mean()
df2['M_12'] = df2['Qobs'].rolling(window=12, min_periods=1).mean()
df2['M_6'] = df2['Qobs'].rolling(window=6, min_periods=1).mean()
df2['M_4'] = df2['Qobs'].rolling(window=4, min_periods=1).mean()

df2 = df2.loc[datahorai:]

# Leitura de simulações
sim_s_chuva = pd.read_csv(f'./Resultados/{dispara.month:02d}_{dispara.day:02d}/{s_chuva}.txt',
                          delimiter='\s+', header = None)
sim_s_chuva.columns = ['year', 'month', 'day', 'hour', 'Precip', 'Qmon', 'Qanc', 'Qsim']
sim_s_chuva = sim_s_chuva.set_index(pd.to_datetime(sim_s_chuva[['year', 'month', 'day', 'hour']]))
sim_s_chuva = sim_s_chuva.set_index(sim_s_chuva.index.tz_localize('America/Sao_Paulo'))
sim_s_chuva.index = sim_s_chuva.index.tz_convert('UTC')
sim_s_chuva = sim_s_chuva.drop(['year', 'month', 'day', 'hour'], axis=1)
sim_s_chuva = sim_s_chuva.loc[datahorai:datahoraf]

sim_c_chuva = pd.read_csv(f'./Resultados/{dispara.month:02d}_{dispara.day:02d}/{c_chuva}.txt',
                          delimiter='\s+', header = None)
sim_c_chuva.columns = ['year', 'month', 'day', 'hour', 'Precip', 'Qmon', 'Qanc', 'Qsim']
sim_c_chuva = sim_c_chuva.set_index(pd.to_datetime(sim_c_chuva[['year', 'month', 'day', 'hour']]))
sim_c_chuva = sim_c_chuva.set_index(sim_c_chuva.index.tz_localize('America/Sao_Paulo'))
sim_c_chuva.index = sim_c_chuva.index.tz_convert('UTC')
sim_c_chuva = sim_c_chuva.drop(['year', 'month', 'day', 'hour'], axis=1)
sim_c_chuva = sim_c_chuva.loc[datahorai:datahoraf]
sim_c_chuva2 = sim_c_chuva.loc[dispara:datahoraf]

df_aval = pd.merge(df2, sim_c_chuva['Qanc'], how='outer',
                   left_index=True, right_index=True)
df_aval = pd.merge(df_aval, sim_c_chuva['Qsim'], how='outer',
                   left_index=True, right_index=True)

# Plotagem
fig = go.Figure()
fig.add_trace(go.Scatter(x=df_aval.index, y=df_aval['Qobs'], name=f"Q afluente - {sigla} (m3/s)", marker_color='black'))
fig.add_trace(go.Scatter(x=sim_c_chuva2.index, y=sim_c_chuva2['Qanc'], name="Q ancorada (m3/s)", marker_color='red'))
fig.add_trace(go.Scatter(x=df_aval.index, y=df_aval['Qsim'], name="Q simulada (m3/s)", marker_color='blue'))
fig.add_trace(go.Scatter(x=df_aval.index, y=df_aval['M_24'], name="Média - 24h (m3/s)", marker_color='darkgreen'))
fig.add_trace(go.Scatter(x=df_aval.index, y=df_aval['M_12'], name="Média - 12h (m3/s)", marker_color='darkviolet'))
fig.add_trace(go.Scatter(x=df_aval.index, y=df_aval['M_6'], name="Média - 6h (m3/s)", marker_color='dodgerblue'))
fig.add_trace(go.Scatter(x=[dispara], y=[df_aval.loc[dispara,'Qobs']], marker=dict(color="gold", size=10), name='Disparo Previsão'))
fig.update_yaxes(title_text='Vazão [m3s-1]')
fig.update_xaxes(tickformat="%Y-%m-%d %H")

#fig.update_layout(title={'text':f'Simulação {nome}', 'x':0.5, 'xanchor':'center', 'y':0.95})
fig.update_layout(autosize=False,width=1000,height=400,margin=dict(l=30,r=30,b=10,t=10))
fig.update_layout(legend_title='Trend')
#fig.write_image(f'./Resultados/{dispara.month:02d}_{dispara.day:02d}/{sigla}.png')
fig.show()
