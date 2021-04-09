import numpy as np
import pandas as pd
import json

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

    ########## SERIES 15 MIN ##########
    print('Tratando ',posto_nome)
    dados = pd.read_csv('../Dados/Vazao_Bruto/'+cod_bacia+'_'+posto_nome+'_FB.csv',
                        index_col = 0, sep = ',')
    dados.index = pd.to_datetime(dados.index)

    #DADOS BRUTOS -> FLAG 0
    #DADO BRUTO BAIXADO SEM VALOR -> FLAG 1
    dados['flag'] = np.where(dados['h_m'].isnull(), 1, 0)

    dados["q_m3s"] = pd.to_numeric(dados["q_m3s"], downcast="float")
    dados["h_m"] = pd.to_numeric(dados["h_m"], downcast = "float")

    # cria DFs padrão de data, para serem preenchidas com os dados baixados
    t_ini = dados.index[0]
    t_fim = dados.index[-1]

    date_rng_15min = pd.date_range(start=t_ini, end=t_fim, freq='15min')
    table_15min = pd.DataFrame(date_rng_15min, columns=['index_15min'])
    table_15min['datahora']= pd.to_datetime(table_15min['index_15min'])
    table_15min = table_15min.set_index('datahora')
    table_15min.drop(['index_15min'], axis=1, inplace = True)
    df_15min = pd.merge(table_15min, dados, how='left',
                        left_index=True, right_index=True)
    df_15min = df_15min[~df_15min.index.duplicated(keep='first')]

    #DATA SEM REGISTRO NA SERIE DE DADOS BRUTOS -> FLAG 2
    df_15min['flag'] = np.where(df_15min['flag'].isnull(), 2, df_15min['flag'])

    #SINALIZA A OCORRENCIA DE VALORES NEGATIVOS -> FLAG 3
    #REMOVE VALORES DE COTA NEGATIVOS
    df_15min['flag'] = np.where((df_15min['h_m'] <= 0), 3, df_15min['flag'])
    df_15min['flag'] = np.where((df_15min['q_m3s'] <= 0), 3, df_15min['flag'])
    df_15min['h_m'] = np.where((df_15min['h_m'] <= 0), np.nan, df_15min['h_m'])
    df_15min['h_m'] = np.where((df_15min['q_m3s'] <= 0), np.nan, df_15min['h_m'])

    #SINALIZA COTAS CONSTANTES DE 12 HORAS -> FLAG 4
    #REMOVE COTAS CONSTANTES - AQUI APLICADO PARA 48 OBS DE 15 MIN - 12 HORAS
    dados2 = df_15min.groupby((df_15min['h_m'].shift()!=df_15min['h_m']).cumsum()
                           ).filter(lambda x: len(x) >= 48)
    df_15min['flag'] = np.where(df_15min.index.isin(dados2.index),
                                4, df_15min['flag'])
    df_15min['h_m'] = np.where(df_15min.index.isin(dados2.index),
                               np.nan, df_15min['h_m'])

    # SINALIZA ERROS VISUAIS -> FLAG 5
    # REMOVE SPIKES COM BASE EM DICIONARIO DE ERROS GROSSEIROS
    #importa dicionario de erros grosseiros e escolhe estacao
    dicionario_erros = json.load(open('../Dados/Vazao_Bruto/erros_grosseiros_bruto.txt'))
    erros_estacao = dicionario_erros[posto_nome]
    #trata a matriz de erros
    try:
        erros_estacao = np.hstack(erros_estacao)
    except ValueError:
        pass
    #remove spikes da serie observada
    df_15min.loc[pd.to_datetime(erros_estacao), 'h_m'] = np.nan
    df_15min['flag'] = np.where(df_15min.index.isin(pd.to_datetime(erros_estacao)),
                                np.where((df_15min['flag'] != 0), df_15min['flag'],
                                         5), df_15min['flag'])

    #REMOVE VALORES DE VAZAO DO PONTO EM QUE COTA TENHA SIDO RETIRADA
    df_15min['q_m3s'] = np.where(df_15min['h_m'].isnull(),
                                 np.nan, df_15min['q_m3s'])

    #COLUNA FLAG PARA INTEIRO
    df_15min['flag'] = df_15min['flag'].astype(int)

    #exporta observado para csv
    df_15min.to_csv('../Dados/Vazao_Pre_Consist/'+cod_bacia+'_'+posto_nome+'_FC.csv',
                    date_format='%Y-%m-%dT%H:%M:%S+00:00', sep = ",",
                    float_format = '%.3f')

    print(posto_nome, ' acabou')
