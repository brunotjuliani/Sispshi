import pandas as pd
import numpy as np
import datetime as dt
import xarray as xr
from pathlib import Path
import ast
import os
import time
import warnings
import sacsma2021

#ignora warnings de slice dos dataframe por membro e passo de tempo
warnings.simplefilter(action='ignore', category=pd.errors.PerformanceWarning)

print('\n#####-----#####-----#####-----#####-----#####-----#####')
print(f'05.1 - Previsão ECMWF\n')
start1 = time.time()

#Definicoes da hora da rodada
hora_att = open('../Dados/disparo.txt')
data_ant = hora_att.readline().strip()
disparo = hora_att.readline().strip()
hora_att.close()
#datetime rodada
rodada = dt.datetime.strptime(disparo, '%Y-%m-%d %H:%M:%S%z')
ano, mes, dia, hora = rodada.year, rodada.month, rodada.day, rodada.hour
#datetime rodada anterior
anterior = dt.datetime.strptime(data_ant, '%Y-%m-%d %H:%M:%S%z')
mes_ant, dia_ant = anterior.month, anterior.day
#hora arquivo ecmwf
data_ecmwf = dt.datetime(ano, mes, dia, 00, tzinfo=dt.timezone.utc)
#inicio aquecimento
inicio = rodada - dt.timedelta(days=730)
#fim da previsao
fim_prev = rodada + dt.timedelta(days=14)
#inicio da serie exportada (sem ancoragem)
anc7 = rodada - dt.timedelta(days=7)

#Definicao das sub-bacias
bacias_def = pd.read_csv('../Dados/bacias_def_provisorio.csv')
#Definicao da grade padrao
grade_def = pd.read_csv('../Dados/grade_def.csv', index_col='idGrade')

#Leitura arquivo grib recortado quando já gerado
#Para novo dia, gera arquivo e copia para pasta
if mes_ant == mes and dia_ant == dia:
    print('Gribfile já recortado\n')
    #grib para dataframe
    with xr.open_dataset(f'../Dados/Chuva/Grib/recorte_D1E_{ano:04d}{mes:02d}{dia:02d}00.grb', engine='cfgrib') as ds:
        grbs = ds.to_dataframe()
    print('Arquivo carregado\n')
else:
    print('Recortando arquivo para área de interesse\n')
    #muda diretorio para salvar grib, e volta para /Programas
    dir_prog = os.getcwd()
    os.chdir('../Dados/Chuva/Grib/')
    os.system('rm *')
    os.system('/usr/local/bin/recortaInterpolaGribEcmwf.sh')
    os.chdir(dir_prog)
    #grib para dataframe
    with xr.open_dataset(f'../Dados/Chuva/Grib/recorte_D1E_{ano:04d}{mes:02d}{dia:02d}00.grb', engine='cfgrib') as ds:
        grbs = ds.to_dataframe()
    print('\nArquivo recortado e carregado\n')

#Trata dataframe do grib
print('Tratando dataframe de previsão\n')
grbs = grbs.iloc[:,-1].rename('chuva_acum').reset_index(level=['latitude','longitude'])
#transforma lon para padrao, e arredonda p/ correlacao
grbs['x'] = (grbs['longitude'] - 360).apply(lambda x: round(x,1))
grbs['y'] = grbs['latitude'].apply(lambda x: round(x,1))
grbs = grbs.drop(['latitude', 'longitude'], axis=1)

#Lista membro ensemble
membros = grbs.index.unique('number')
#Lista passos de tempo
steps = grbs.index.unique('step')

#Dicionarios para dataframes de previsoes por membro
prev_membros = {}
prev_disc = {}

for ens_n in membros:
    print('Espacializando membro ', ens_n)
    #inicializa dataframe unico para membro
    prev_membros[ens_n] = pd.DataFrame()
    for passo in steps:
        idx_hora = data_ecmwf + passo
        #filtra dados para membro e tempo
        membro = grbs.loc[ens_n,passo]
        #correlaciona com grade padrao das sub-bacias Sispshi
        prev_sispshi = pd.merge(membro, grade_def, on=['x', 'y'])
        #precipitacao media em cada bacia
        for idx, info in bacias_def.iterrows():
            bacia = info['bacia']
            prev_bacia = prev_sispshi.loc[prev_sispshi['bacia']==bacia]['chuva_acum'].mean()
            #armazena p/ passo de tempo e bacia
            prev_membros[ens_n].loc[idx_hora,bacia] = prev_bacia
    #diferenciacao para cada passo de tempo isolado, comparacao do acumulado
    #exclui primeira linha - condicoes iniciais
    prev_disc[ens_n] = prev_membros[ens_n].diff().iloc[1:]
    #limpa casos de diff negativa - valores muito pequenos - erro do grib
    prev_disc[ens_n] = prev_disc[ens_n].clip(lower=0)

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
        #para index duplicado, fica com dado observado
        chuva_comb = chuva_comb[~chuva_comb.index.duplicated(keep='first')]
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
    if peq_prev.index[0] == rodada:
        peq_prev = peq_prev.iloc[1:]
    peq_prev = peq_prev.drop(['q_m3s'], axis=1)
    peq_prev.to_csv(f'../Simulacoes/{ano:04d}_{mes:02d}_{dia:02d}_{hora:02d}/prev_b{bacia:02d}_{ano:04d}{mes:02d}{dia:02d}{hora:02d}.csv',
                    index_label='datahora', float_format='%.3f')

print('\nPreparo de dados finalizado')

print('\n#####-----#####-----#####-----#####-----#####-----#####')
print(f'05.3 - Simulação Sacramento sem ancoragem\n')
parametros = pd.read_csv('../Dados/param_dt6.csv', index_col='Parametros')
simulado = {}
for idx, info in bacias_def.iterrows():
    bacia = info['bacia']
    area_inc = info['area_incremental']
    montante = info['b_montante']

    #Para bacias de cabeceira
    if montante == 'n':
        print(f'Iniciando bacia {bacia:02d}')
        #Dados para simulacao
        dt = 0.25 #6 horas
        params = parametros[f'par_{bacia:02d}']
        ETP = aq_bacias[bacia]['etp']
        Qobs = aq_bacias[bacia]['q_m3s'].rename('qobs')
        q_atual_obs = Qobs.loc[Qobs.last_valid_index()]
        #Caso nao tenha dado observado mais recente, compara com ultima hora de dado
        idx_obs_atual = Qobs.last_valid_index()
        dados_precip = aq_bacias[bacia].drop(['etp', 'q_m3s'], axis=1)

        ##SIMULACAO SACRAMENTO sem ancoragem
        Qsims = pd.DataFrame()
        #Simula para ensemble e faz quantis
        ens_n = 0
        while ens_n <= 50:
            PME = dados_precip[f'pme_{ens_n}']
            Qsims[f'sac_{ens_n}'] = sacsma2021.simulacao(area_inc, dt, PME, ETP, params)
            ens_n += 1
        Qsims.index = dados_precip.index
        #Armazena no dicionario para aproveitamento de montante
        simulado[bacia] = Qsims
        q_atual_sim = Qsims.loc[idx_obs_atual,'sac_0']
        #Recorta para periodo de previsao -salva os 7 ultimos dias de ancoragem
        Qsims = Qsims.loc[anc7:]
        #Calculo dos quantis
        Qsims['Qmed'] = Qsims.median(axis=1)
        Qsims['Q25'] = Qsims.quantile(0.25, axis=1)
        Qsims['Q75'] = Qsims.quantile(0.75, axis=1)
        Qsims['Qmax'] = Qsims.max(axis=1)
        Qsims['Qmin'] = Qsims.min(axis=1)

        #Exporta serie sem ancoragem
        Qsims.to_csv(f'../Simulacoes/{ano:04d}_{mes:02d}_{dia:02d}_{hora:02d}/sim_bru_b{bacia:02d}_{ano:04d}{mes:02d}{dia:02d}{hora:02d}.csv',
                        index_label='datahora', float_format='%.3f')

print('\n#####-----#####-----#####-----#####-----#####-----#####')
print(f'05.4 - Simulação Sacramento com ancoragem\n')
parametros = pd.read_csv('../Dados/param_dt6.csv', index_col='Parametros')
ancorado = {}
for idx, info in bacias_def.iterrows():
    bacia = info['bacia']
    area_inc = info['area_incremental']
    montante = info['b_montante']

    #Para bacias de cabeceira
    if montante == 'n':
        print(f'\nIniciando bacia {bacia:02d}')
        #Dados para simulacao
        dt = 0.25 #6 horas
        params = parametros[f'par_{bacia:02d}']
        ETP = aq_bacias[bacia]['etp']
        Qobs = aq_bacias[bacia]['q_m3s'].rename('qobs')
        q_atual_obs = Qobs.loc[Qobs.last_valid_index()]
        Qjus = Qobs.loc[:Qobs.last_valid_index()].interpolate(method='spline', order=3)
        #Caso nao tenha dado observado mais recente, compara com ultima hora de dado
        idx_obs_atual = Qobs.last_valid_index()
        dados_precip = aq_bacias[bacia].drop(['etp', 'q_m3s'], axis=1)

        #Simulacao para verificar ancoragem
        Qsims = pd.DataFrame()
        PME = dados_precip['pme_0']
        Qsims['sac_0'] = sacsma2021.simulacao(area_inc, dt, PME, ETP, params)
        Qsims.index = dados_precip.index
        #Taxa Proporcao
        q_atual_sim = Qsims.loc[idx_obs_atual,'sac_0']
        dif_sim = (q_atual_obs - q_atual_sim)/q_atual_obs
        print(f'Ultima Vazao observada = {q_atual_obs} m3/s')
        print(f'Vazao simulada comparativa = {q_atual_sim} m3/s')
        #Se simulado for menor que observado, modifica estados iniciais de chuva
        #Apos ajustar chuva p/ simulação com diferença < 5%, faz proporcionalidade
        #Se simulado for maior que observado, faz apenas proprocionalidade
        dados_perturb = dados_precip.copy()
        if dif_sim > 0:
            print(f'Incrementando chuva aquecimento')
            inc_0 = 0
            taxa = 1
            incremento = inc_0
            while abs(dif_sim) > 0.05:
                incremento = inc_0 + taxa
                print('Tentativa - incremento = ', str(incremento))
                dados_perturb = dados_precip.copy()
                dados_perturb.loc[:rodada] += incremento
                Qsims = pd.DataFrame()
                #Simula perturbacao
                PME = dados_perturb['pme_0']
                Qsims['sac_0'] = sacsma2021.simulacao(area_inc, dt, PME, ETP, params)
                Qsims.index = dados_perturb.index
                #Taxa Proporcao
                q_atual_sim = Qsims.loc[idx_obs_atual,'sac_0']
                dif_sim = (q_atual_obs - q_atual_sim)/q_atual_obs
                #Se simulado for maior que observado, reduz taxa de incremento
                #Se simulado for menor que observado, adciona-se a taxa ao incremento base
                if dif_sim < 0:
                    taxa = taxa/2
                else:
                    inc_0 = incremento
            print(f'Chuva incremental bacia {bacia:02d}: {incremento} mm')

        ##SIMULACAO SACRAMENTO com proporcionalidade para os membros
        Qsims = pd.DataFrame()
        #Simula para ensemble e faz quantis
        ens_n = 0
        while ens_n <= 50:
            PME = dados_perturb[f'pme_{ens_n}']
            Qsims[f'sac_{ens_n}'] = sacsma2021.simulacao(area_inc, dt, PME, ETP, params)
            ens_n += 1
        Qsims.index = dados_precip.index
        #Agrupa os dados de jusante c/ parte simulada
        #Armazena no dicionario para aproveitamento de montante
        df_ancorado = Qsims.copy()
        ens_n = 0
        while ens_n <= 50:
            serie_jusante = pd.concat([Qjus.rename(f'sac_{ens_n}'), Qsims[f'sac_{ens_n}'].loc[Qjus.last_valid_index():]])
            serie_jusante = serie_jusante[~serie_jusante.index.duplicated(keep='first')]
            df_ancorado[f'qjus_{ens_n}'] = serie_jusante
            ens_n += 1
        ancorado[bacia] = df_ancorado
        #Ancora com proporcionalidade
        print(f'Proporcionalizando vazao simulada')
        q_atual_sim = Qsims.loc[idx_obs_atual,'sac_0']
        Qsims = Qsims * q_atual_obs/q_atual_sim
        #Recorta para periodo de previsao
        #Pega ultimo index com dado observado como inicio
        Qsims = Qsims.loc[rodada:]
        #Calculo dos quantis
        Qsims['Qmed'] = Qsims.median(axis=1)
        Qsims['Q25'] = Qsims.quantile(0.25, axis=1)
        Qsims['Q75'] = Qsims.quantile(0.75, axis=1)
        Qsims['Qmax'] = Qsims.max(axis=1)
        Qsims['Qmin'] = Qsims.min(axis=1)

        #Exporta serie ancorada
        Qsims.to_csv(f'../Simulacoes/{ano:04d}_{mes:02d}_{dia:02d}_{hora:02d}/sim_anc_b{bacia:02d}_{ano:04d}{mes:02d}{dia:02d}{hora:02d}.csv',
                        index_label='datahora', float_format='%.3f')

print('\n#####-----#####-----#####-----#####-----#####-----#####')
print(f'05.5 - Simulação Sacramento - Bacias com montante\n')
parametros = pd.read_csv('../Dados/param_dt6.csv', index_col='Parametros')
dict_mtes = ast.literal_eval(open('../Dados/dict_montantes.txt','r').read())
for idx, info in bacias_def.iterrows():
    bacia = info['bacia']
    area_inc = info['area_incremental']
    montante = info['b_montante']

    #Para bacias com montante
    if montante == 's':
        print(f'\nIniciando bacia {bacia:02d}')
        #Dados para simulacao
        dt = 0.25 #6 horas
        params = parametros[f'par_{bacia:02d}']
        ETP = aq_bacias[bacia]['etp']
        Qobs = aq_bacias[bacia]['q_m3s'].rename('qobs')
        q_atual_obs = Qobs.loc[Qobs.last_valid_index()]
        Qjus = Qobs.loc[:Qobs.last_valid_index()].interpolate(method='spline', order=3)
        #Vazao de montante para cada um dos membros do ensemble
        bacias_mtes = dict_mtes[bacia]
        Qmon = pd.DataFrame(index=Qobs.index)
        ens_n = 0
        while ens_n <= 50:
            Qmon[f'q_mon_{ens_n}'] = 0
            for b in bacias_mtes:
                Qmon[f'q_mon_{ens_n}'] = Qmon[f'q_mon_{ens_n}'] + ancorado[b][f'qjus_{ens_n}']
            ens_n += 1
        #Caso nao tenha dado observado mais recente, compara com ultima hora de dado
        idx_obs_atual = Qobs.last_valid_index()
        dados_precip = aq_bacias[bacia].drop(['etp', 'q_m3s'], axis=1)

        #Simulacao para verificar ancoragem
        Qsims = pd.DataFrame()
        PME = dados_precip['pme_0']
        Qsims['sac_0'] = sacsma2021.simulacao(area_inc, dt, PME, ETP, params, Qmon=Qmon['q_mon_0'])
        Qsims.index = dados_precip.index
        #Taxa Proporcao
        q_atual_sim = Qsims.loc[idx_obs_atual,'sac_0']
        dif_sim = (q_atual_obs - q_atual_sim)/q_atual_obs
        print(f'Ultima Vazao observada = {q_atual_obs} m3/s')
        print(f'Vazao simulada comparativa = {q_atual_sim} m3/s')
        #Se simulado for menor que observado, modifica estados iniciais de chuva
        #Apos ajustar chuva p/ simulação com diferença < 5%, faz proporcionalidade
        #Se simulado for maior que observado, faz apenas proprocionalidade
        dados_perturb = dados_precip.copy()
        if dif_sim > 0:
            print(f'Incrementando chuva aquecimento')
            inc_0 = 0
            taxa = 1
            incremento = inc_0
            while abs(dif_sim) > 0.05:
                incremento = inc_0 + taxa
                print('Tentativa - incremento = ', str(incremento))
                dados_perturb = dados_precip.copy()
                dados_perturb.loc[:rodada] += incremento
                Qsims = pd.DataFrame()
                #Simula perturbacao
                PME = dados_perturb['pme_0']
                Qsims['sac_0'] = sacsma2021.simulacao(area_inc, dt, PME, ETP, params, Qmon=Qmon['q_mon_0'])
                Qsims.index = dados_perturb.index
                #Taxa Proporcao
                q_atual_sim = Qsims.loc[idx_obs_atual,'sac_0']
                dif_sim = (q_atual_obs - q_atual_sim)/q_atual_obs
                #Se simulado for maior que observado, reduz taxa de incremento
                #Se simulado for menor que observado, adciona-se a taxa ao incremento base
                if dif_sim < 0:
                    taxa = taxa/2
                else:
                    inc_0 = incremento
            print(f'Chuva incremental bacia {bacia:02d}: {incremento} mm')

        ##SIMULACAO SACRAMENTO com proporcionalidade para os membros
        Qsims = pd.DataFrame()
        #Simula para ensemble e faz quantis
        ens_n = 0
        while ens_n <= 50:
            PME = dados_perturb[f'pme_{ens_n}']
            Qsims[f'sac_{ens_n}'] = sacsma2021.simulacao(area_inc, dt, PME, ETP, params, Qmon=Qmon[f'q_mon_{ens_n}'])
            ens_n += 1
        Qsims.index = dados_precip.index
        #Agrupa os dados de jusante c/ parte simulada
        #Armazena no dicionario para aproveitamento de montante
        df_ancorado = Qsims.copy()
        ens_n = 0
        while ens_n <= 50:
            serie_jusante = pd.concat([Qjus.rename(f'sac_{ens_n}'), Qsims[f'sac_{ens_n}'].loc[Qjus.last_valid_index():]])
            serie_jusante = serie_jusante[~serie_jusante.index.duplicated(keep='first')]
            df_ancorado[f'qjus_{ens_n}'] = serie_jusante
            ens_n += 1
        ancorado[bacia] = df_ancorado

        #Ancora com proporcionalidade
        print(f'Proporcionalizando vazao simulada')
        q_atual_sim = Qsims.loc[idx_obs_atual,'sac_0']
        Qsims = Qsims * q_atual_obs/q_atual_sim
        #Recorta para periodo de previsao
        #Pega ultimo index com dado observado como inicio
        Qsims = Qsims.loc[rodada:]
        #Calculo dos quantis
        Qsims['Qmed'] = Qsims.median(axis=1)
        Qsims['Q25'] = Qsims.quantile(0.25, axis=1)
        Qsims['Q75'] = Qsims.quantile(0.75, axis=1)
        Qsims['Qmax'] = Qsims.max(axis=1)
        Qsims['Qmin'] = Qsims.min(axis=1)

        #Exporta serie ancorada
        Qsims.to_csv(f'../Simulacoes/{ano:04d}_{mes:02d}_{dia:02d}_{hora:02d}/sim_anc_b{bacia:02d}_{ano:04d}{mes:02d}{dia:02d}{hora:02d}.csv',
                        index_label='datahora', float_format='%.3f')

print('\nSimulação finalizada')
print('#####-----#####-----#####-----#####-----#####-----#####\n')
end1 = time.time()
print('Tempo decorrido ', end1-start1)
