import pandas as pd
import numpy as np
import datetime as dt
import pygrib
from pathlib import Path
import time

print('\n#####-----#####-----#####-----#####-----#####-----#####')
print(f'05.1 - Previsão ECMWF\n')
start1 = time.time()

#Definicoes da hora da rodada
hora_att = open('../Dados/disparo.txt')
data_ant = hora_att.readline().strip()
disparo = hora_att.readline().strip()
hora_att.close()
rodada = dt.datetime.strptime(disparo, '%Y-%m-%d %H:%M:%S%z')
ano, mes, dia, hora = rodada.year, rodada.month, rodada.day, rodada.hour
#hora arquivo ecmwf
data_ecmwf = dt.datetime(ano, mes, dia, 00, tzinfo=dt.timezone.utc)
#inicio aquecimento
inicio = rodada - dt.timedelta(days=730)
#fim da previsao
fim_prev = rodada + dt.timedelta(days=14)

#Definicao das sub-bacias
bacias_def = pd.read_csv('../Dados/bacias_def.csv')
#Definicao da grade padrao
grade_def = pd.read_csv('../Dados/grade_def.csv', index_col='idGrade')

print('Leitura gribfile')
grbfile = '../Dados/recorte_D1E.grb'
grbs = pygrib.open(grbfile)

#Dicionarios para dataframes de previsoes por membro
prev_membros = {}
prev_disc = {}

ens_n = 0
while ens_n <= 50:
    print('Espacializando membro ', ens_n)
    #seleciona todos os dados para determinado membro
    membro = grbs.select(perturbationNumber = ens_n)
    #inicializa dataframe unico para membro
    prev_membros[ens_n] = pd.DataFrame()
    #loop temporal p/ cada membro
    for previsao in membro:
        passo_tempo = data_ecmwf + dt.timedelta(hours=previsao.step)
        #retorna lista (todos os pontos) na respectiva ordem: lat,lon,p_acumulada
        valores = previsao.latLonValues
        lista = [valores[i * 3:(i + 1) * 3] for i in range((len(valores) + 3 - 1) // 3 )]
        df = pd.DataFrame(lista, columns=['y', 'x', 'value'])
        #transforma lon para padrao, e arredonda p/ correlacao
        df['x'] = df['x'] - 360
        df['x'] = df['x'].apply(lambda x: round(x,1))
        df['y'] = df['y'].apply(lambda x: round(x,1))
        #correlaciona com grade padrao das sub-bacias Sispshi
        prev_sispshi = pd.merge(df, grade_def, on=['x', 'y'])
        #precipitacao media em cada bacia
        for idx, info in bacias_def.iterrows():
            bacia = info['bacia']
            prev_bacia = prev_sispshi.loc[prev_sispshi['bacia']==bacia]['value'].mean()
            #armazena p/ passo de tempo e bacia
            prev_membros[ens_n].loc[passo_tempo,bacia] = prev_bacia
    #diferenciacao para cada passo de tempo isolado, comparacao do acumulado
    #exclui primeira linha - condicoes iniciais
    prev_disc[ens_n] = prev_membros[ens_n].diff().iloc[1:]
    #limpa casos de diff negativa - valores muito pequenos - erro do grib
    prev_disc[ens_n] = prev_disc[ens_n].clip(lower=0)
    #passa para proximo membro
    ens_n +=1

print('\n#####-----#####-----#####-----#####-----#####-----#####')
print(f'05.2 - Dados de Entrada para previsão hidrológica\n')

#Cria pasta para exportar resultados de simulacao
Path(f'../Simulacoes/{ano:04d}_{mes:02d}_{dia:02d}_{hora:02d}').mkdir(parents=True,exist_ok=True)

#Abre serie gradeada de chuva do periodo de aquecimento para toda a area
grade_chuva = pd.read_csv('../Dados/Chuva/chuva_grade_730.csv', index_col='datahora',
                          parse_dates=True)
grade_chuva.columns = grade_chuva.columns.astype(int)
grade_chuva = grade_chuva.loc[:rodada]

#Organizacao dos arquivos de entrada para cada bacia
aq_bacias = {}
for idx, info in bacias_def.iterrows():
    idBacia = info['idBacia']
    bacia = info['bacia']
    posto_nome = info['nome']

    #df padrao horario para ser preenchido
    date_rng_horario = pd.date_range(start=inicio, end=fim_prev, freq='H', closed='right')
    dados_peq = pd.DataFrame(pd.to_datetime(date_rng_horario), columns=['datahora'])
    dados_peq = dados_peq.set_index('datahora')

    #chuva media na bacia - aquecimento
    selecao = grade_chuva[list(grade_def.loc[grade_def['bacia'] == bacia].index)]
    chuva_sub = pd.DataFrame(selecao.mean(axis=1), columns=['chuva_mm'])

    #combina com chuva ensemble de previsao - 51 membros
    ens_n = 0
    while ens_n <= 50:
        chuva_membro = pd.DataFrame(prev_disc[ens_n][bacia].rename('chuva_mm'))
        chuva_comb = pd.concat([chuva_sub, chuva_membro])
        dados_peq['pme_'+str(ens_n)] = chuva_comb['chuva_mm']
        ens_n +=1

    #etp
    etp = pd.read_csv(f'../Dados/ETP/etpclim_{bacia:02d}.txt', header = None)
    etp['Mes'] = etp[0].str.slice(0,2)
    etp['Dia'] = etp[0].str.slice(3,5)
    etp['Hora'] = etp[0].str.slice(6,8)
    etp['etp'] = pd.to_numeric(etp[0].str.slice(9,17))
    etp = etp.drop([0], axis=1)
    etp.index = etp['Mes'] + '-' + etp['Dia'] + '-' + etp['Hora']
    dados_peq['data'] = dados_peq.index.strftime('%m-%d-%H')
    dados_peq['etp'] = dados_peq['data'].map(etp['etp'])
    dados_peq = dados_peq.drop(['data'], axis=1)

    #agrupa em passo de tempo de 6 horas - soma
    peq_6hrs = dados_peq.resample("6H", closed='right', label = 'right').sum()

    #vazao exutoria da bacia e agrupa em 6 horas - media
    vazao_sub = pd.read_csv(f'../Dados/Vazao/{idBacia}.csv',
                            index_col='datahora', parse_dates=True)
    vazao_sub = vazao_sub.loc[inicio:rodada]
    vazao_6hrs = vazao_sub.resample("6H", closed='right', label = 'right').mean()

    #agrupa todos os dados e exporta arquivos da rodada por bacia
    peq_6hrs = pd.merge(peq_6hrs, vazao_6hrs, how = 'left',
                     left_index = True, right_index = True)
    aq_bacias[bacia] = peq_6hrs
    #dados observados
    peq_obs = peq_6hrs[['pme_0', 'etp', 'q_m3s']]
    peq_obs.columns = ['chuva_mm', 'etp_mm', 'q_m3s']
    peq_obs = peq_obs.loc[:rodada]
    peq_obs.to_csv(f'../Simulacoes/{ano:04d}_{mes:02d}_{dia:02d}_{hora:02d}/obs_b{bacia:02d}_{ano:04d}{mes:02d}{dia:02d}{hora:02d}.csv',
                   index_label='datahora', float_format='%.3f')
    #dados de entrada para previsao
    peq_prev = peq_6hrs.loc[rodada:]
    peq_prev = peq_prev.iloc[1:]
    peq_prev = peq_prev.drop(['q_m3s'], axis=1)
    peq_prev.to_csv(f'../Simulacoes/{ano:04d}_{mes:02d}_{dia:02d}_{hora:02d}/prev_b{bacia:02d}_{ano:04d}{mes:02d}{dia:02d}{hora:02d}.csv',
                    index_label='datahora', float_format='%.3f')

print('\nPreparo de dados finalizado')
print('#####-----#####-----#####-----#####-----#####-----#####\n')

end1 = time.time()
print('Tempo decorrido ', end1-start1)
