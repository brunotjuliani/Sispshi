import pandas as pd
import datetime as dt
import requests
import pytz
import numpy as np 


listaUHES = [
	      ['DRJ', 'Derivação Rio Jordão', '30'],
	      ['FCH', 'Foz do Chopim', '6'],
	      ['GBM', 'Gov. Bento Munhoz (Foz do Areia)', '1'],
	      ['SCL', 'Santa Clara', '31'],
	      ['SCX', 'Gov. José Richa (Salto Caxias)', '20'],
	      ['SGD', 'Gov. Ney Braga (Segredo)', '24'],
	      ['SOS', 'Salto Osório', '53']
	    ]

for UHE in listaUHES:
    sigla = UHE[0]
    nome  = UHE[1]
    ponto = UHE[2]

    # 1 - Leitura da "serie longa" (DF)
    DF = pd.read_csv('{}.txt'.format(sigla), delimiter='\s+')
    DF.columns = ['year', 'month', 'day', 'hour', 'Qaflu', 'Qdeflu']
    DF = DF.set_index(pd.to_datetime(DF[['year', 'month', 'day', 'hour']]))
    DF = DF.set_index(DF.index.tz_localize('UTC'))
    DF = DF.drop(['year', 'month', 'day', 'hour'], axis=1) 

    # 2 - Aquisicao dos dados atuais, com folga para preenchimento de nans
    datahoraf = dt.datetime.now(pytz.utc) - dt.timedelta(hours=1)
    datahorai = datahoraf - dt.timedelta(days=365)
    url = "http://www.simepar.br/telemetry-copel/monhid?datahorai={:%Y-%m-%dT%H:%M:%S}&datahoraf={:%Y-%m-%dT%H:%M:%S}&ids={}&tipos=R".format(datahorai, datahoraf, ponto)
    response = requests.get(url=url)
    data = response.json()
    df = pd.DataFrame.from_dict(data)
    df = df.set_index(pd.to_datetime(df.datahora))

    df2 = pd.DataFrame()
    for row in df.itertuples():
        try:
            df2.loc[row[0],'Qaflu'] = row[3]['vazaoAfluente']
        except:
            df2.loc[row[0],'Qaflu'] = -99999.9
        
        try:
            df2.loc[row[0],'Qdeflu'] = row[3]['vazaoDefluente']
        except:
            df2.loc[row[0],'Qdeflu'] = -99999.9

    # 3 - expande o indice da serie longa ate o tempo atual e preenche com df2
    df2 = df2.set_index(df2.index.tz_localize('UTC'))
    idx = pd.date_range(DF.index.min(), df2.index.max(), freq='H')
    DF2 = DF.reindex(idx)
    DF2.update(df2)  
    
    # 4 - exporta no padrao Angelo em BRT
    DF2 = DF2.loc[~DF2.index.duplicated(keep='last')]
    DF2 = DF2.set_index(DF2.index - dt.timedelta(hours=3))
    arq = open('{}.txt'.format(sigla), 'w')
    arq.write('#AAA MM DD HH    Qaflu   Qdeflu\n')
    for row in DF2.itertuples():
        string1 = '{:{dfmt} {tfmt}}'.format(row[0], dfmt='%Y %m %d', tfmt='%H')
        arq.write(string1)
        string2 = ' {:8.2f} {:8.2f}\n'.format(row[1], row[2])
        arq.write(string2)
    print('Salvou o arquivo da UHE - {}!'.format(nome))
    arq.close()


### ======= SCRIPT ARLAN ANTERIOR ======= ### 
#for UHE in listaUHES:
#    sigla = UHE[0]
#    nome_UHE = UHE[1]
#    ponto = UHE[2]
#    DF = pd.read_csv('{}.txt'.format(sigla), delimiter="\s+")
#    DF.columns = ['year', 'month', 'day', 'hour', 'Qaflu', 'Qdeflu']
#    DF.set_index(pd.to_datetime(DF[['year','month','day','hour']]), inplace=True)
#    DF.drop(columns=['year','month','day','hour'], inplace=True)
#    tini = DF.index[-720] + dt.timedelta(hours=3)
#    texto_psql = "select mondatahora, \
#		  monvalues->>'vazaoAfluente', \
#		  monvalues->>'vazaoDefluente' \
#		  from copel.monhid \
#		  where mondatahora > '{}' and \
#		  monponto = {}".format(tini, ponto)
#    conn = psycopg2.connect(dbname='clim', user='reader', password='r&ead3r', host='tornado', port='5432')
#    consulta = conn.cursor(cursor_factory = psycopg2.extras.DictCursor)
#    consulta.execute(texto_psql)
#    consulta = consulta.fetchall()
#    
#    df3 = pd.DataFrame(consulta) 
#    df = pd.DataFrame(consulta, columns=['mondatahora','Qaflu','Qdeflu'])
#    df2 = df.copy()
#    idx_UTC = pd.to_datetime(df['mondatahora'].values)
#    idx_BRT = idx_UTC - dt.timedelta(hours=3)
#    df = df[['Qaflu','Qdeflu']].astype(float).set_index(idx_BRT)
#    DF = DF.sort_index(ascending=True)
#    df = df.sort_index(ascending=True)
#    DF = df.combine_first(DF)
#    DF = DF.loc[~DF.index.duplicated(keep='first')]
#    arq = open('{}.txt'.format(sigla), 'w')
#    arq.write('#AAA MM DD HH    Qaflu   Qdeflu\n')
#    for row in DF.itertuples():
#        string1 = '{:{dfmt} {tfmt}}'.format(row[0], dfmt='%Y %m %d', tfmt='%H')
#        arq.write(string1)
#        string2 = ' {:8.2f} {:8.2f}\n'.format(row[1], row[2])
#        arq.write(string2)
#    print('Salvou o arquivo da UHE - {}!'.format(nome_UHE))
#    arq.close()
#    break

### ================================ SCRIPT ANGELO ======================== ###
## -*- coding: utf-8 -*-
#from datetime import datetime, timedelta
#from sys import path, stdout; path.append('/simepar/hidro/COPEL/SISPSHI2/Bibliotecas/')
#from admin import serie_horaria


#""" 1-vazoes_uhes.py: Faz a gestão das séries longas de vazão nas usinas hidrelétricas da COPEL
    #Este programa serve para atualizar os arquivos que contém as séries longas de vazão afluente (QAA) e defluente (QDA) das
#usinas hidrelétricas da COPEL. Os dados recentes são disponibilizados no diretório compartilhado com a COPEL:
#/simepar/copelger/sispshi/ rm arquivos textos. Há um arquivo para cada empreendimento, cujas sigla ou abreviação dá nome ao
#arquivos. Os dados são em escala horária e há duas séries, uma de vazão afluente (estimada por balanço hídrico) e outra de
#vazão defluente.
    #Este programa não executa procedimentos de consistência. Apenas adiciona os dados recentes às respectivas séries longas."""
#print '\n ~/SISPSHI2/Dados_Usinas/1-vazoes_uhes.py'

#listaUHES = [
    #['DRJ', 'Derivação Rio Jordão'],
    #['FCH', 'Foz do Chopim'],
    #['GBM', 'Gov. Bento Munhoz (Foz do Areia)'],
    #['SCL', 'Santa Clara'],
    #['SCX', 'Gov. José Richa (Salto Caxias)'],
    #['SGD', 'Gov. Ney Braga (Segredo)'],
    #['SOS', 'Salto Osório'] ]

#dirCopel = '/simepar/copelger/sispshi/'




#for sigla, nome in listaUHES:
    
    ##Lendo arquivo de dados histórico
    #hist = serie_horaria([[sigla+'.txt', 4, 5]])
    
    ##Lendo arquivo de dados recentes
    #arq = open(dirCopel+sigla+'.txt', 'r')
    #for l in arq:
        #l = l.split(';')
        #try:
            #ano, mes, dia = int(l[0][6:10]), int(l[0][3:5]), int(l[0][0:2])
            #hor, mnt = int(l[0][11:13]), int(l[0][14:16])
            #if hor == 24:
                #dt = datetime(ano, mes, dia, 23, mnt, 0) + timedelta(hours = 1)
            #else:
                #dt = datetime(ano, mes, dia, hor, mnt, 0)
            #qa = float(l[1].replace(',', '.'))
            #qd = float(l[2].replace(',', '.'))
            #hist[dt] = [qa, qd]
        #except:
            #pass
    #arq.close()

    ##Lista das data/horas de dados em todo o histórico
    #datas = sorted(hist.keys())
    
    ##Regravando série histórica de dados atualizada
    #arq = open(sigla+'.txt', 'w')
    #arq.write('#AAA MM DD HH    Qaflu   Qdeflu\n')
    
    #for dt in datas:
        
        #arq.write('%s' % dt.strftime('%Y %m %d %H'))
        #arq.write(' %8.2f %8.2f\n' % (hist[dt][0], hist[dt][1]))
        
    #arq.close()
