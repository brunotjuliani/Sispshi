import pandas as pd
import numpy as np
import csv
import datetime as dt
import plotly.graph_objects as go
import locale
# setar locale para português
locale.setlocale(locale.LC_ALL, 'pt_BR.utf8')

vazao_old = pd.read_excel(f'./Vazoes_Diarias_1931_2019_GBM.xlsx',
                          skiprows = 7, header = None)
vazao_old.index = pd.to_datetime(vazao_old[0], format='%d/%b/%Y').rename('data')
vazao_old.columns = ['Data', 'QAflu']
vazao_old = vazao_old.drop('Data', 1)

vazao_new = pd.read_csv('./Vazoes_de_foz_do_areia_2020_jun_2021.txt',
                        delimiter='\s+', skiprows = 3, header = 0, decimal=',')
vazao_new.index = pd.to_datetime(vazao_new['Dia'], format='%d/%m/%Y').rename('data')
vazao_new2 = pd.DataFrame(vazao_new['Afluente'].rename('QAflu'))

dados = pd.concat([vazao_old, vazao_new2])

dados_mont = pd.read_csv('./Uniao_da_Vitoria_diario.csv',
                         index_col = 0, parse_dates=True)

dados['QMon'] = dados_mont['vazao']

fig = go.Figure()
fig.add_trace(go.Scatter(x=dados.index, y=dados['QAflu'], name="QAflu - Naturalizada (m3/s)", marker_color='gray'))
fig.add_trace(go.Scatter(x=dados.index, y=dados['QMon'], name="Q UVA (m3/s)", marker_color='red'))
fig.update_yaxes(title_text='Vazão [m3s-1]')
fig.update_xaxes(tickformat="%Y-%m-%d %H")
fig.update_layout(autosize=False,width=1000,height=500,margin=dict(l=30,r=30,b=10,t=10))
#fig.write_html(f'./Dados_Usinas/comp_gbm_uva.html')
fig.show()
