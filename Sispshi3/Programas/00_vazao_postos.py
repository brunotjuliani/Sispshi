import numpy as np
import pandas as pd
import datetime as dt
import csv
import psycopg2, psycopg2.extras
import requests
import xmltodict

def coleta_simepar(t_ini,t_fim,posto_codigo,sensores):
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

def coleta_uhes(t_ini,t_fim,posto_codigo):
    url = f"http://produtos.simepar.br/telemetry-copel/monhid?datahorai={t_ini:%Y-%m-%dT%H:%M:%S}&datahoraf={t_fim:%Y-%m-%dT%H:%M:%S}&ids={posto_codigo}&tipos=R"
    response = requests.get(url=url)
    data = response.json()
    df = pd.DataFrame.from_dict(data)
    df = df.set_index(pd.to_datetime(df.datahora))
    df2 = pd.DataFrame()
    for row in df.itertuples():
        try:
            df2.loc[row[0],'Qaflu'] = row[3]['vazaoAfluente']
        except:
            df2.loc[row[0],'Qaflu'] = np.nan
    return df2

postos_flu = pd.read_csv('../Dados/postos_flu.csv')
postos_flu = postos_flu.loc[postos_flu['tipo']=='uhe']
#define manualmente início da serie a ser coletada
t_ini = dt.datetime(1997,1,1)
t_fim = dt.datetime.now()

print('\n#####-----#####-----#####-----#####-----#####-----#####')
print(f'02 - Coleta de dados de vazão\n')

for index, posto in postos_flu.iterrows():
    ## COLETA DADOS PRECIPITACAO
    idPosto = posto['idPosto']
    posto_codigo = posto['codigo_banco']
    posto_bacia = posto['bacia']
    posto_nome = posto['nome']
    posto_tipo = posto['tipo']

    if posto_tipo == 'estacao':
        #Coleta dados de precipitacao do banco Simepar
        dados = coleta_simepar(t_ini,t_fim, posto_codigo, '(33)')
        dados.columns = ['q_m3s', 'sensor']
        dados = dados[['q_m3s']]
        #Converte indice para formato padrao
        dados.index = pd.to_datetime(dados.index, utc=True).rename('datahora')
        dados["q_m3s"] = pd.to_numeric(dados["q_m3s"], downcast = "float")

    elif posto_tipo == 'uhe':
        dados = coleta_uhes(t_ini,t_fim,posto_codigo)
        dados.index
        dados.columns = ['q_m3s']
        #Localiza dados UTC, no formato padrao
        dados.index = dados.index.tz_convert('utc').rename('datahora')
        dados["q_m3s"] = pd.to_numeric(dados["q_m3s"], downcast = "float")
        dados = dados.sort_index()
    else:
        print('Dados indefinidos')
        continue

    #Remove valores registrados como negativos na serie bruta
    dados['q_m3s'] = np.where((dados['q_m3s'] < 0), np.nan, dados['q_m3s'])

    #Agrupa em serie horaria, com intervalo fechado à direita (acumulado 0:01 a 1:00)
    dados_hor = (dados.resample("H", closed='right', label='right').agg({'q_m3s' : np.mean}))

    #Cria DF padrao horario para ser preenchido
    date_rng_horario = pd.date_range(start=t_ini, end=t_fim, freq='H', tz='utc',
                                     closed='right')
    table_hor = pd.DataFrame(date_rng_horario, columns=['date'])
    table_hor['datahora']= pd.to_datetime(table_hor['date'])
    table_hor = table_hor.set_index('datahora')
    table_hor = table_hor[[]]

    #Unifica dados horarios no DF padrao
    #Se dado vazio, entao preenche com nan
    try:
        table_hor = pd.merge(table_hor, dados_hor, left_index = True,
                         right_index = True, how = 'left')
    except:
        table_hor['q_m3s'] = np.nan
    table_hor = table_hor[~table_hor.index.duplicated(keep='first')]
    table_hor = table_hor.loc[table_hor['q_m3s'].first_valid_index():]

    #exporta dados horarios para csv
    table_hor.to_csv(f'../Dados/Vazao/{idPosto}.csv', sep = ",", float_format='%.2f')

    #Estacoes com falha nos dados
    if dados.empty:
        print(f'{index+1}/{len(postos_flu)} - {idPosto} - FALHA NO DADO')
    else:
        print(f'{index+1}/{len(postos_flu)} - {idPosto} - ',
              table_hor['q_m3s'].first_valid_index(), ' - ',
              table_hor['q_m3s'].last_valid_index())

print(f'\nColeta finalizada')
print('#####-----#####-----#####-----#####-----#####-----#####\n')
