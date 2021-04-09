import pandas as pd
import numpy as np
import plotly.graph_objects as go

peq = pd.read_csv('sispshi_01_Rio_Negro_peq.csv', skiprows=1,
                     index_col = 0, parse_dates=True)
peq

peq['pme_acum'] = peq['pme'].cumsum()
peq['siprec_acum'] = peq['siprec'].cumsum()

fig = go.Figure()
fig.add_trace(go.Scatter(x=peq['pme_acum'], y=peq['siprec_acum'], showlegend=False, marker_color='blue'))
fig.update_xaxes(title_text='Precipitacao Acumulada - Pluviômetros - Sispshi')
fig.update_yaxes(title_text='Precipitação Acumulada - Siprec')
#fig.update_layout(title_text='Comparação Pluviometros x Siprec')
fig.show()

# soma_siprec = peq['siprec'].sum()
# soma_siprec
#
# soma_espac = peq['pme'].sum()
# soma_espac
#
# peq_anual = peq.copy().resample('Y', closed='right', label = 'right').agg(
#     {'pme':np.sum, 'siprec':np.sum, 'etp':np.sum,'qjus':np.mean, 'qmon':np.mean})
# peq_anual
#
# chuva_obs['chuva_mm'].cumsum()
