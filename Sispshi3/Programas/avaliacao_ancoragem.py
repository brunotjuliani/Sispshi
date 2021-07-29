import pandas as pd
import datetime as dt
from plotly.subplots import make_subplots
import plotly.graph_objects as go

# Leitura
rodada = dt.datetime(2021, 7, 28, 13, tzinfo=dt.timezone.utc)
ini_obs = rodada-dt.timedelta(days=10)
ini_obs = ini_obs.isoformat()
fim_prev = rodada+dt.timedelta(days=14)
fim_prev = fim_prev.isoformat()
ano = rodada.year
mes = rodada.month
dia = rodada.day
hora = rodada.hour

bacias_def = pd.read_csv('../Dados/bacias_def.csv')

codigos_operacionais = {
    1:116, 2:216, 3:316, 4:416, 5:516, 6:616, 7:716, 8:816, 9:916, 10:1015,
    11:1115, 12:1214, 13:1315, 14:1415, 15:1515, 16:1614, 17:1714, 18:1812,
    19:1912, 20:2012, 21:2115
}
#info = bacias_def.loc[2]
for idx, info in bacias_def.iterrows():
    idBacia = info['idBacia']
    bacia = info['bacia']
    posto_nome = info['nome']
    codigo_op = codigos_operacionais[bacia]
    montante = info['b_montante']
    #Para bacias de cabeceira
    if montante == 'n':
        vazao_obs = pd.read_csv(f'../Dados/Vazao/{idBacia}.csv',
                                index_col='datahora', parse_dates=True)
        vazao_obs = vazao_obs.resample("6H", closed='right', label = 'right').mean()
        vazao_obs = vazao_obs.loc[ini_obs:fim_prev]
        q_atual_obs = vazao_obs.iloc[vazao_obs.index.get_loc(rodada, method='pad'),0]

        dados_anc = pd.read_csv(f'../Simulacoes/{ano:04d}_{mes:02d}_{dia:02d}_{hora:02d}/sim_anc_b{bacia:02d}_{ano:04d}{mes:02d}{dia:02d}{hora:02d}.csv',
                                 index_col='datahora', parse_dates=True)
        dados_bru = pd.read_csv(f'../Simulacoes/{ano:04d}_{mes:02d}_{dia:02d}_{hora:02d}/sim_bru_b{bacia:02d}_{ano:04d}{mes:02d}{dia:02d}{hora:02d}.csv',
                                 index_col='datahora', parse_dates=True)
        dados_bru = dados_bru.loc[ini_obs:fim_prev]

        operacional = pd.read_csv(f'../Simulacoes/{ano:04d}_{mes:02d}_{dia:02d}_{hora:02d}/{ano:04d}{mes:02d}{dia:02d}{hora-3:02d}.txt', header=None, delimiter='\s+')
        operacional.columns = ['codigo','year','month','day','hour','chuva','vazao']
        operacional.index = (pd.to_datetime(operacional[['year','month','day','hour']]) + dt.timedelta(hours=3))
        operacional.index = operacional.index.tz_localize('utc')
        operacional = operacional.loc[operacional['codigo']==codigo_op].iloc[1:].resample("6H", closed='right', label = 'right').mean()

        # Plotagem
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=dados_anc.index, y=dados_anc['Q75'], showlegend=False, marker_color='blue'))
        fig.add_trace(go.Scatter(x=dados_anc.index, y=dados_anc['Q25'], showlegend=False, marker_color='blue', fill='tonexty'))
        fig.add_trace(go.Scatter(x=dados_anc.index, y=dados_anc['Qmed'], name=f"Simulação - ancorada (m3/s)", marker_color='blue'))
        fig.add_trace(go.Scatter(x=dados_bru.index, y=dados_bru['Qmed'], name=f"Simulação - bruta (m3/s)", marker_color='green'))
        fig.add_trace(go.Scatter(x=operacional.index, y=operacional['vazao'], name=f"Simulação - operacional (m3/s)", marker_color='red'))
        fig.add_trace(go.Scatter(x=vazao_obs.index, y=vazao_obs['q_m3s'], name=f"Q observada (m3/s)", marker_color='black'))
        #fig.add_trace(go.Scatter(x=[rodada], y=[q_atual_obs], marker=dict(color="gold", size=10), name='Disparo Previsão'))

        fig.update_yaxes(title_text='Vazão [m3s-1]')
        fig.update_xaxes(tickformat="%Y-%m-%d %H")
        fig.update_layout(legend_title_text=f'Bacia {bacia:02d} - {posto_nome}')
        fig.update_layout(autosize=False,width=1200,height=675,margin=dict(l=30,r=30,b=10,t=10))
        fig.write_image(f'../Simulacoes/{ano:04d}_{mes:02d}_{dia:02d}_{hora:02d}/teste_b{bacia:02d}_{ano:04d}{mes:02d}{dia:02d}{hora:02d}.png')
        fig.show()

dados_anc = pd.read_csv(f'../Simulacoes/{ano:04d}_{mes:02d}_{dia:02d}_{hora:02d}/sim_anc_b10_{ano:04d}{mes:02d}{dia:02d}{hora:02d}.csv',
                         index_col='datahora', parse_dates=True)
dados_anc
