import numpy as np
import pandas as pd
import os

postos_vazao = {
               'Rio_Negro':['01','26064948'],
               'Porto_Amazonas':['02','25334953'],
               'Sao_Bento':['03','25564947'],
               'Pontilhao':['04','25555031'],
               'Santa_Cruz_Timbo':['05','26125049'],
               'Sao_Mateus_Sul':['06','25525023'],
               'Divisa':['07','26055019'],
               'Fluviopolis':['08','26025035'],
               'Uniao_da_Vitoria':['09','26145104'],
               'Madereira_Gavazzoni':['10','25485116'],
               'Jangada':['11','26225115'],
               'Solais_Novo':['13','26055155'],
               'Porto_Santo_Antonio':['14','25235306'],
               'Aguas_do_Vere':['15','25465256'],
               'Porto_Capanema':['20','25345435'],
               'Hotel_Cataratas':['21','25685442'],
           }

for posto_nome, posto_informacoes in postos_vazao.items():
    cod_bacia = posto_informacoes[0]
    posto_codigo = posto_informacoes[1]

    ########## SERIES HORARIAS ##########

    #le arquivo com serie de 15 minutos
    bruto_15min = pd.read_csv('../Dados/Vazao_Pre_Consist/'+cod_bacia+'_'+posto_nome+'_FC.csv',
                              index_col=0, sep=',')
    bruto_15min.index = pd.to_datetime(bruto_15min.index)
    bruto_15min.drop(['flag'], axis=1, inplace = True)

    #cria DFs padrao horario para ser preenchido com os dados de 15 min
    t_ini = bruto_15min.index[0].round('1h')
    t_fim = bruto_15min.index[-1]
    date_rng_horario = pd.date_range(start=t_ini, end=t_fim, freq='H', tz = "UTC")
    table_hor = pd.DataFrame(date_rng_horario, columns=['date'])
    table_hor['datahora']= pd.to_datetime(table_hor['date'])
    table_hor = table_hor.set_index('datahora')
    table_hor.drop(['date'], axis=1, inplace = True)


    # agrupa em dados horarios, com intervalo fechado à direita (acumulado/media da 0:01 a 1:00);
    # coluna count resulta a soma (contagem) dos "1", coluna valor resulta na media dos valores;
    # para os valores de cont < 4, substitui o dado em 'valor' por NaN:
    bruto_15min['count'] = np.where(bruto_15min['q_m3s'].notnull(), 1, 0)
    df_horario = (bruto_15min.resample("H", closed='right', label='right').
                  agg({'count' : np.sum, 'q_m3s' : np.mean, 'h_m' : np.mean}))

    # remove colunas 'count' dos dataframes e agrupa com data padrao
    df_horario.drop('count', axis=1, inplace=True)
    table_hor = pd.merge(table_hor, df_horario, left_index = True,
                         right_index = True, how = 'left')
    table_hor = table_hor[~table_hor.index.duplicated(keep='first')]

    #exporta observado para csv
    table_hor.to_csv('../Dados/Vazao_Horaria/'+cod_bacia+'_'+posto_nome+'_HR.csv',
                     date_format='%Y-%m-%dT%H:%M:%S+00:00', sep = ",",
                     float_format = '%.3f')
    print(posto_nome, ' acabou')
