import numpy as np
import pandas as pd
import datetime as dt
import csv
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


# #Lista postos de precipitacao com as seguintes informacoes
# # Nome : [codigo simepar, codigo ANA, latitude, longitute, altitude, Banco]
# postos_precip = {
#     'Aguas do Vere':['25465256', '2552056', '-25.7737', '-52.9329', '466', 'simepar'],
#     'Balsa Jaracatia':['25345816', '2553066', '-25.5832', '-53.2668', '23', 'simepar'],
#     'Bituruna':['26065150', ' ', '-26.0639', '-51.5083', '720', 'simepar'],
#     'Boa Vista da Aparecida':['25315021', '2553069', '-25.5225', '-53.3558', '367', 'simepar'],
#     'Cascavel':['24535333', '2453064', '-24.8845', '-53.5547', '719.3', 'simepar'],
#     'Coronel Domingos Soares':['25825217', ' ', '-26.03729', '-51.98156', '607', 'simepar'],
#     'Curitiba':['25264916', '2549101', '-25.44817', '-49.23033', '935', 'simepar'],
#     'Derivacao do Rio Jordao':['25755210', '2557071', '-25.75922', '-52.10889', '689', 'simepar'],
#     'Divisa':['26055019', '2650026', '-26.0833', '-50.3166', '770', 'simepar'],
#     'Entre Rios':['25335129', '2551072', '-25.5459', '-51.4884', '1095', 'simepar'],
#     'Fernandes Pinheiro':['25275035', ' ', '-25.4532', '-50.5839', '893', 'simepar'],
#     'Fluviopolis':['26025035', '2650027', '-26.0333', '-50.5833', '770', 'simepar'],
#     'Foz do Areia Hid':['26005139', '2651055', '-26.00639', '-51.66754', '728.2', 'simepar'],
#     'Foz do Areia Met':['26055139', '2651053', '-26.0037', '-51.6679', '780', 'simepar'],
#     'Foz do Cachoeira':['26355045', '2650028', '-26.5833', '-50.75', '895', 'simepar'],
#     'Foz do Timbo':['26105047', '2650029', '-26.29452', '-50.89522', '0', 'simepar'],
#     'Fragosos':['26094923', '2649073', '-26.15', '-49.3833', '0', 'simepar'],
#     'Francisco Beltrao':['26055305', ' ', '-26.0593', '-53.06548', '652', 'simepar'],
#     'Guarapuava':['25215130', '2551070', '-25.3845', '-51.4935', '1070', 'simepar'],
#     'Jangada':['26225115', '2651057', '-26.3666', '-51.25', '1046', 'simepar'],
#     'Lapa':['25474946', '2549104', '-25.7817', '-49.7598', '909.8', 'simepar'],
#     'Madeireira Gavazzoni':['25485116', '2551054', '-25.80682', '-51.22884', '805', 'simepar'],
#     'Palmas':['26285158', ' ', '-26.4682', '-51.9762', '1100', 'simepar'],
#     'Palmital do Meio':['26025109', '2651056', '-26.02999', '-51.14149', '840', 'simepar'],
#     'Pato Branco':['26075241', '2652042', '-26.1229', '-52.6514', '721.8', 'simepar'],
#     'PCH AA Barramento':['25345306', ' ', '-25.5713', '-53.1135', '351', 'simepar'],
#     'PCH AA Porto Palmeirinha':['26015237', '2652048', '-26.0291', '-52.6283', '720', 'simepar'],
#     'Pinhais':['25254905', ' ', '-25.3907', '-49.1299', '930', 'simepar'],
#     'Pinhao':['25385157', '2551071', '-25.64944', '-51.9625', '910', 'simepar'],
#     'Ponta Grossa':['25135001', '2550071', '-25.0137', '-50.1524', '888.25', 'simepar'],
#     'Pontilhao':['25555031', '2550070', '-25.9166', '-50.5166', '0', 'simepar'],
#     'Porto Amazonas':['25334953', '2549106', '-25.55', '-49.8833', '780', 'simepar'],
#     'Porto Capanema':['25345435', '2553070', '-25.6154', '-53.7923', '234', 'simepar'],
#     'Porto Santo_Antonio':['25235306', '2553062', '-25.3833', '-53.1', '386', 'simepar'],
#     'Porto Vitoria':['26105114', '2651058', '-26.1666', '-51.2333', '745', 'simepar'],
#     'Reservatorio Salto Caxias':['25325329', '2553068', '-25.5333', '-53.4833', '440', 'simepar'],
#     'Rio Negro':['26064948', '2649074', '-26.1097', '-49.80194', '766', 'simepar'],
#     'Salto Caxias Met':['25315329', ' ', '-25.52092', '-53.49412', '440', 'simepar'],
#     'Santa Cruz do Timbo':['26125049', '2650030', '-26.38392', '-50.87826', '0', 'simepar'],
#     'Sao Bento':['25564947', '2549105', '-25.9333', '-49.7833', '799', 'simepar'],
#     'Sao Mateus do Sul':['25525023', '2550069', '-25.87702', '-50.38755', '760', 'simepar'],
#     'Sao Miguel do Iguacu':['25115408', '2554034', '-25.3528', '-54.2546', '298', 'simepar'],
#     'Segredo':['25475206', '2552057', '-25.7911', '-52.11895', '607', 'simepar'],
#     'Solais Novo':['26055155', '2651054', '-26.0833', '-51.9166', '809', 'simepar'],
#     'Uniao da Vitoria Hid':['26145104', '2651059', '-26.22772', '-51.08059', '749', 'simepar'],
#     'Uniao da Vitoria Met':['26145103', '2651060', '-26.22825', '-51.06827', '756.53', 'simepar'],
#     'Vossoroca':['25494905', '2549102', '-25.8166', '-49.0833', '851', 'simepar'],
#     }
#
# postos_def = pd.DataFrame(columns=['idPosto', 'nome', 'codigo_simepar',
#                                    'codigo_snirh', 'x', 'y', 'z', 'banco'])
#
# for posto_nome, posto_informacoes in postos_precip.items():
#     df2 = {
#         'idPosto':posto_informacoes[0]+'_'+posto_informacoes[5],
#         'nome':posto_nome,
#         'codigo_simepar':posto_informacoes[0],
#         'codigo_snirh':'',
#         'x':float(posto_informacoes[3]),
#         'y':float(posto_informacoes[2]),
#         'z':float(posto_informacoes[4]),
#         'banco':posto_informacoes[5]
#     }
#     postos_def = postos_def.append(df2, ignore_index=True)
#
# postos_def.to_csv('../Dados/Precip_Estacoes/postos_def.csv', index=False)

postos_precip = pd.read_csv('../Dados/Precip_Estacoes/postos_def.csv')

## COLETA DADOS PRECIPITACAO
for index, posto in postos_precip.iterrows():
    idPosto = posto['idPosto']
    posto_codigo = posto['codigo_simepar']
    posto_snirh = posto['codigo_snirh']
    posto_nome = posto['nome']
    posto_banco = posto['banco']
    posto_x = posto['x']
    posto_y = posto['y']
    posto_z = posto['z']

    ########## SERIES 15 MIN ##########
    print('Coletando dados brutos',posto_nome)
    t_ini = dt.datetime(1997, 1, 1,  0,  0) #AAAA, M, D, H, Min
    t_fim = dt.datetime(2021, 7, 4, 0, 0)

    #coleta dados de precipitacao
    dados = coletar_dados(t_ini,t_fim, posto_codigo, '(7)')
    dados.columns = ['chuva_mm', 'sensor']
    dados = dados[['chuva_mm']]

    #converte indice para formato DATETIME ISO UTC
    dados.index = pd.to_datetime(dados.index, utc=True).rename('datahora')
    dados["chuva_mm"] = pd.to_numeric(dados["chuva_mm"], downcast = "float")

    ########## TRATA SERIES 15 MIN ##########

    #DADOS BRUTOS -> FLAG 0
    #DADO BRUTO BAIXADO SEM VALOR -> FLAG 1
    dados['flag'] = np.where(dados['chuva_mm'].isnull(), 1, 0)

    # cria DFs padrão de data, para serem preenchidas com os dados baixados
    t_ini = dados.index[0]
    t_fim = dados.index[-1]

    date_rng_15min = pd.date_range(start=t_ini, end=t_fim,freq='15min',tz="UTC")
    table_15min = pd.DataFrame(date_rng_15min, columns=['datahora'])
    table_15min['datahora']= pd.to_datetime(table_15min['datahora'])
    table_15min = table_15min.set_index('datahora')
    df_15min = pd.merge(table_15min, dados, how='left',
                        left_index=True, right_index=True)
    df_15min = df_15min[~df_15min.index.duplicated(keep='first')]

    #DATA SEM REGISTRO NA SERIE DE DADOS BRUTOS -> FLAG 2
    df_15min['flag'] = np.where(df_15min['flag'].isnull(), 2, df_15min['flag'])

    #SINALIZA A OCORRENCIA DE VALORES NEGATIVOS -> FLAG 3
    #SINALIZA A OCORRENCIA DE VALORES SUPERIORES A 45 MM -> FLAG 3
    #REMOVE VALORES DE COTA NEGATIVOS
    df_15min['flag'] = np.where((df_15min['chuva_mm'] < 0), 3, df_15min['flag'])
    df_15min['chuva_mm'] = np.where((df_15min['chuva_mm'] < 0
                                     ), np.nan, df_15min['chuva_mm'])
    df_15min['flag'] = np.where((df_15min['chuva_mm'] >45), 3, df_15min['flag'])
    df_15min['chuva_mm'] = np.where((df_15min['chuva_mm'] > 45
                                     ), np.nan, df_15min['chuva_mm'])

    #SINALIZA PERSISTENCIA DE VALORES NAO NULOS -> FLAG 4
    # H <= 2MM <- 6 HORAS = 24 REGISTROS
    # H > 2MM <- 1 HORA = 4 REGISTROS
    dados2 = df_15min.groupby((df_15min['chuva_mm'].
                               shift()!=df_15min['chuva_mm']).cumsum()
                              ).filter(lambda x: len(x) >= 24)
    dados2 = dados2[dados2['chuva_mm']>0]
    dados2 = dados2[dados2['chuva_mm']<=2]
    dados3 = df_15min.groupby((df_15min['chuva_mm'].
                               shift()!=df_15min['chuva_mm']).cumsum()
                              ).filter(lambda x: len(x) >= 4)
    dados3 = dados3[dados3['chuva_mm']>0]
    dados3 = dados3[dados3['chuva_mm']>2]

    df_15min['flag'] = np.where(df_15min.index.isin(dados2.index),
                                4, df_15min['flag'])
    df_15min['flag'] = np.where(df_15min.index.isin(dados3.index),
                                4, df_15min['flag'])
    df_15min['chuva_mm'] = np.where(df_15min.index.isin(dados2.index),
                                np.nan, df_15min['chuva_mm'])
    df_15min['chuva_mm'] = np.where(df_15min.index.isin(dados3.index),
                                np.nan, df_15min['chuva_mm'])

    #COLUNA FLAG PARA INTEIRO
    df_15min['flag'] = df_15min['flag'].astype(int)



    ########## TRANSFORMA SERIE HORARIA ##########
    df_15min = df_15min[['chuva_mm']]

    #cria DFs padrao horario para ser preenchido com os dados de 15 min
    t_ini = df_15min.index[0].round('1h')
    t_fim = df_15min.index[-1]
    date_rng_horario = pd.date_range(start=t_ini, end=t_fim, freq='H', tz="UTC")
    table_hor = pd.DataFrame(date_rng_horario, columns=['date'])
    table_hor['datahora']= pd.to_datetime(table_hor['date'])
    table_hor = table_hor.set_index('datahora')
    table_hor = table_hor[[]]

    # agrupa em dados horarios, com intervalo fechado à direita (acumulado/media da 0:01 a 1:00);
    # coluna count resulta a soma (contagem) dos "1", coluna valor resulta na media dos valores;
    # para os valores de cont < 4, substitui o dado em 'valor' por NaN:
    df_15min['count'] = np.where(df_15min['chuva_mm'].notnull(), 1, 0)
    df_horario = (df_15min.resample("H", closed='right', label='right').
                  agg({'count' : np.sum, 'chuva_mm' : np.sum}))

    #REMOVE A OCORRENCIA DE VALORES HORARIOS SUPERIORES A 90 MM
    df_horario['chuva_mm'] = np.where((df_horario['chuva_mm'] > 90
                                         ), np.nan, df_horario['chuva_mm'])

    # remove colunas 'count' dos dataframes e agrupa com data padrao
    df_horario = df_horario[['chuva_mm']]
    table_hor = pd.merge(table_hor, df_horario, left_index = True,
                         right_index = True, how = 'left')
    table_hor = table_hor[~table_hor.index.duplicated(keep='first')]

    #exporta dados horarios para csv
    with open(f'../Dados/Precip_Estacoes/{idPosto}.csv','w',newline='') as file:
        writer = csv.writer(file)
        writer.writerow([posto_snirh])
        writer.writerow([posto_nome])
        writer.writerow([posto_x, posto_y, posto_z])
    table_hor.to_csv(f'../Dados/Precip_Estacoes/{idPosto}.csv',
                     mode = 'a', sep = ",", float_format='%.2f')

    print(posto_nome, ' acabou - ', index+1,"/", len(postos_precip))
