import pandas as pd
import numpy as np
import dds
import plotly.graph_objects as go


def att_sim_AR(Qobs, Qsim, params):

    #Parametros - Autoregressao ordem 3
    if type(params) is np.ndarray:
        params = dict(zip(Xnomes, params))
    a1 = params['a1']
    a2 = params['a2']
    a3 = params['a3']

    #Serie Erro Simulado (s_es)
    #Diferença entre valor observado e simulado
    s_es = Qobs - Qsim
    #Media das diferenças
    erro_mean = s_es.mean()
    #Serie Erro Medio (s_em)
    #Subtrai a media dos erros, correspondendo a uma serie de media zero
    s_em = s_es - erro_mean

    #Serie Erro Medio de Atualizacao (s_em_att)
    #Serie auto-regressiva de atualizacao (ordem 3)
    #Parametros: a1, a2 e a3
    array_em_att = np.empty(len(s_em))
    for i in range(1, len(s_em)):
        array_em_att[i] = a1*s_em[i-1] + a2*s_em[i-2] + a3*s_em[i-3]
        s_em_att = pd.Series(array_em_att, index=s_em.index, name = 'Qatt')

    #Serie de erros de simulação atualizada (s_es_att)
    s_es_att = s_em_att + erro_mean

    #Vazao simulada atualizada
    Qsim_att = (Qsim + s_es_att).rename('Qatt')

    return Qsim_att

X = (('a1', -10, 10),
     ('a2', -10, 10),
     ('a3', -10, 10))
Xnomes = [i[0] for i in X]
Xmin = [i[1] for i in X]
Xmax = [i[2] for i in X]

def fobj_nse(X):
    params = X
    Qatt = att_sim_AR(Qobs, Qsim, params)
    df = pd.concat([Qobs, Qatt], axis=1)
    df = df.dropna()
    NSE = 1 - df.apply(lambda x:(x.Qobs-x.Qatt)**2,axis=1).sum()/df.apply(lambda x:(x.Qobs-df.Qobs.mean())**2,axis=1).sum()
    fmin = 1 - NSE
    return fmin

serie = pd.read_csv('comparacao_b01.csv', parse_dates=True, index_col=0)
Qobs = serie['Qobs']
Qsim = serie['Qsim']

X1, F1 = dds.dds(Xmin, Xmax, fobj_nse, r=0.2, m=5000)
Qatt_1 = att_sim_AR(Qobs, Qsim, X1)

X2 = {'a1':0.66962056, 'a2':0.34461119, 'a3':-0.03721481}
Qatt_2 = att_sim_AR(Qobs, Qsim, X2)



fig = go.Figure()
fig.add_trace(go.Scatter(x=Qobs.index, y=Qobs, name='Qobs', marker_color='black'))
fig.add_trace(go.Scatter(x=Qsim.index, y=Qsim, name='Qsim_original', marker_color='blue'))
fig.add_trace(go.Scatter(x=Qatt_1.index, y=Qatt_1, name='Qatualizado', marker_color='red'))
