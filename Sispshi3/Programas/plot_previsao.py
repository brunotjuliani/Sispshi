import pandas as pd
import datetime as dt
from plotly.subplots import make_subplots
import plotly.graph_objects as go

# Leitura
rodada = dt.datetime(2021, 9, 10, 13, tzinfo=dt.timezone.utc)
ini_obs = rodada-dt.timedelta(days=5)
ini_obs = ini_obs.isoformat()
fim_prev = rodada+dt.timedelta(days=14)
fim_prev = fim_prev.isoformat()
ano = rodada.year
mes = rodada.month
dia = rodada.day
hora = rodada.hour

bacias_def = pd.read_csv('../Dados/bacias_def.csv')

#info = bacias_def.loc[2]
for idx, info in bacias_def.iterrows():
    idBacia = info['idBacia']
    bacia = info['bacia']
    posto_nome = info['nome']
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

        # Plotagem
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=dados_anc.index, y=dados_anc['Q75'], showlegend=False, marker_color='blue'))
        fig.add_trace(go.Scatter(x=dados_anc.index, y=dados_anc['Q25'], showlegend=False, marker_color='blue', fill='tonexty'))
        n=0
        while n <= 50:
            fig.add_trace(go.Scatter(x=dados_anc.index, y=dados_anc['sac_'+str(n)], showlegend=False, marker_color='darkgray'))
            n += 1
        fig.add_trace(go.Scatter(x=dados_anc.index, y=dados_anc['Q75'], name=f"Quantil 75 (m3/s)", marker_color='blue'))
        fig.add_trace(go.Scatter(x=dados_anc.index, y=dados_anc['Qmed'], name=f"Mediana (m3/s)", marker_color='red'))
        fig.add_trace(go.Scatter(x=dados_anc.index, y=dados_anc['Q25'], name=f"Quantil 25 (m3/s)", marker_color='blue'))
        fig.add_trace(go.Scatter(x=vazao_obs.index, y=vazao_obs['q_m3s'], name=f"Q observada (m3/s)", marker_color='black'))
        #fig.add_trace(go.Scatter(x=[rodada], y=[q_atual_obs], marker=dict(color="gold", size=10), name='Disparo Previsão'))
        fig.update_yaxes(title_text='Vazão [m3s-1]')
        fig.update_xaxes(tickformat="%Y-%m-%d %H")
        fig.update_layout(legend_title_text=f'Bacia {bacia:02d} - {posto_nome}')
        fig.update_layout(autosize=False,width=800,height=450,margin=dict(l=20,r=20,b=5,t=5))
        fig.write_image(f'../Simulacoes/{ano:04d}_{mes:02d}_{dia:02d}_{hora:02d}/plot_b{bacia:02d}_{ano:04d}{mes:02d}{dia:02d}{hora:02d}.png')
        #fig.show()
