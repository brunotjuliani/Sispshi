import numpy as np
import pandas as pd
import datetime as dt
import psycopg2, psycopg2.extras


def coletar_dados(t_ini,t_fim,posto_codigo,sensores):
        # Montagem do texto
    t_ini_string = t_ini.strftime('%Y-%m-%d %H:%M')
    t_fim_string = t_fim.strftime('%Y-%m-%d %H:%M')
    texto_psql = "select hordatahora at time zone 'UTC' as hordatahora, \
                  horleitura, horsensor \
                  from horaria where hordatahora >= '{}' and hordatahora <= '{}' \
                  and horestacao in ({}) \
                  and horsensor in {} \
                  order by horestacao, horsensor, hordatahora; \
                  ".format(t_ini_string, t_fim_string, posto_codigo,sensores)
    # Execução da consulta no banco do Simepar
    conn = psycopg2.connect(dbname='clim', user='hidro', password='hidrologia',
                            host='tornado', port='5432')
    consulta = conn.cursor(cursor_factory = psycopg2.extras.DictCursor)
    consulta.execute(texto_psql)
    consulta_lista = consulta.fetchall()
    df_consulta =pd.DataFrame(consulta_lista,columns=['tempo','valor','sensor'])
    df_consulta.set_index('tempo', inplace=True)
    return df_consulta

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

    ## COLETA DADOS VAZAO

    ########## SERIES 15 MIN ##########
    print('Coletando dados brutos',posto_nome)
    t_ini = dt.datetime(1997, 1, 1,  0,  0) #AAAA, M, D, H, Min
    t_fim = dt.datetime(2021, 1, 1, 0, 0)

    #coleta dados de cota
    dados_cota = coletar_dados(t_ini,t_fim, posto_codigo, '(18)')
    dados_cota.columns = ['h_m', 'sensor_cota']

    #coleta dados de vazao
    dados_vazao = coletar_dados(t_ini,t_fim, posto_codigo, '(33)')
    dados_vazao.columns = ['q_m3s', 'sensor_vazao']

    #concatena vazao e cota
    dados = pd.merge(dados_cota['h_m'],dados_vazao['q_m3s'],how='inner',
                     left_index=True,right_index=True)
    dados
    #converte indice para formato DATETIME ISO UTC
    dados.index = pd.to_datetime(dados.index, utc=True).rename('datahora')
    dados["q_m3s"] = pd.to_numeric(dados["q_m3s"], downcast="float")
    dados["h_m"] = pd.to_numeric(dados["h_m"], downcast = "float")

    #exporta observado para csv
    dados.to_csv('../Dados/Vazao_Bruto/'+cod_bacia+'_'+posto_nome+'_FB.csv',
                    date_format='%Y-%m-%dT%H:%M:%SZ', sep = ",",
                    float_format = '%.3f')
    print(posto_nome, 'acabou - ')
