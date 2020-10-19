# Arlan Scortegagna - julho/2020
# Este programa substitui o "1-prevWRF.py"
# Realiza a coleta das previsoes de cmb do WRF 5km diretamente do banco do Simepar

import pandas as pd
import numpy as np
import datetime as dt
import requests
import csv

datas = pd.read_csv("/simepar/hidro/COPEL/SISPSHI2/data.txt", header=None, sep=" ")
datas = datas.set_index(4)
datas2 = datas[[0,1,2,3]].copy()
datas2.columns = ['year', 'month', 'day', 'hour']
dref = pd.to_datetime(datas2)[0]
ini_prev = dref 
fim_prev = pd.to_datetime(datas2)[2]
# Lembrando que o Angelo Breda considerada a indexacao no limite inferior do intervalo
# Entao, previsao das 13 horas eh das 13 as 14...

# Obter a relacao do banco de dados entre o id das bacias (arquivo de saidas) e o id no source 14
relacao_banco = pd.read_csv('relacao_cmb_banco.csv', sep=';', \
                dtype={'id_arquivo_saida':str})
relacao_banco = relacao_banco.set_index('id_arquivo_saida')
relacao_banco = relacao_banco['id_source14'].copy()


idx_ideal = pd.date_range(ini_prev, fim_prev, freq="H")
# Para cada bacia realiza consulta via API
for id in relacao_banco.index:
    url = "http://www.simepar.br/rest-forecasts/api/forecasts?type=hourly&source=14&location_id={}&customer_id=1".format(relacao_banco[id])
    print(url)
    response = requests.get(url=url)
    data = response.json()
    prevs = pd.DataFrame.from_dict(data)
    prevs = pd.DataFrame.from_dict(prevs.value[0])
    idx_UTC = pd.to_datetime(prevs["date"].values).tz_localize(None) # O DataFrame vem em UTC - tem que ser convertido para area da bacia informada na API - America/Sao Paulo
    idx_BRT = idx_UTC - dt.timedelta(hours=3)
    idx_angelo = idx_BRT - dt.timedelta(hours=1) # Lembra que o Angelo indexa o acumulado no limite inferior do intervalo
    prevs = prevs.set_index(idx_angelo)
    prevs_prec = prevs["precIntensity"].clip(lower=0) #Evita dados negativos - editado por Bruno em 15-09-2020
    prevs_prec = prevs_prec.reindex(idx_ideal)
    #prevs_prec = prevs_prec.truncate(before=ini_prev, after=fim_prev)
    with open('prevcmb_{}.txt'.format(id), mode='w') as csv_file:
        csv_writer = csv.writer(csv_file)
        for i in prevs_prec.index:
            prevs_prec = prevs_prec.fillna(0)
            linha = '{} {:02} {:02} {:02}   {:.2f}'.format(i.year, i.month, i.day, i.hour, prevs_prec.loc[i])
            csv_writer.writerow([linha])
        print('Gerou arquivo de CMB prev para bacia {}'.format(id))

    
