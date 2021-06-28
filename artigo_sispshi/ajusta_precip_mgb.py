import numpy as np
import pandas as pd
import datetime as dt
import csv

def ler_mgb(filename):
    fwidths = [6,6,6,12]
    df = pd.read_fwf(filename, widths = fwidths, names = ["day", "month", "year", "prec"])
    df.set_index(pd.to_datetime(df[["year", "month", "day"]]), inplace=True)
    df = df.drop(columns=["day", "month", "year"])
    return df

#Lista postos de precipitacao com as seguintes informacoes
# Nome : [codigo simepar, codigo ANA, latitude, longitute, altitude]
postos_precip = {
                 #;Código ;Latitude;Longitude;Nome
    '02452051':[-24.9472,-52.5978,'PORTO CARRIEL'],
    '02549017':[-25.5192,-49.1467,'FAZENDINHA'],
    '02549061':[-25.855,-49.5258,'QUITANDINHA'],
    '02549093':[-25.5992,-49.51,'GUAJUVIRA'],
    '02549105':[-25.9487,-49.7955,'SÃO BENTO'],
    '02549106':[-25.5488,-49.8879,'PORTO AMAZONAS'],
    '02550000':[-25.2372,-50.9608,'PRUDENTÓPOLIS CAPT. SANEPAR'],
    '02550069':[-25.8788,-50.3863,'SÃO MATEUS DO SUL'],
    '02550070':[-25.9096,-50.5221,'PONTILHÃO'],
    '02551008':[-25.5325,-51.4414,'COLÔNIA VITÓRIA'],
    '02551054':[-25.8068,-51.2884,'MADEIREIRA GAVAZZONI'],
    '02551059':[-25.6446,-51.9579,'SANTA CLARA'],
    '02551060':[-25.7021,-52.0021,'FUNDÃO'],
    '25485173':[-25.4856,-51.7279,'FAZENDA AURORA'],
    '23365141':[-25.6121,-51.6529,'GUARAPUAVINHA'],
    '02552008':[-25.1,-52.2667,'MARQUINHO'],
    '02552030':[-25.86,-52.5269,'UHE SALTO SANTIAGO CHOPINZINHO'],
    '02552056':[-25.7738,-52.9346,'ÁGUAS DO VERÊ'],
    '02552057':[-25.7913,-52.1154,'SEGREDO'],
    '25385201':[-25.3813,-52.0246,'VAU DOS RIBEIROS'],
    '25495221':[-25.4871,-52.2163,'PCH CAVERNOSO II'],
    '02553061':[-25.5438,-53.4913,'SALTO CAXIAS'],
    '02553062':[-25.3938,-53.1038,'PORTO SANTO ANTÔNIO'],
    '02553066':[-25.5828,-53.2672,'BALSA DO JARACATIÁ'],
    '25345435':[-25.5804,-53.9163,'PORTO CAPANEMA'],
    '02648002':[-26.7242,-48.9317,'LUIZ ALVES'],
    '02649004':[-26.8297,-49.2719,'TIMBÓ NOVO'],
    '02649013':[-26.4239,-49.2925,'CORUPÁ'],
    '02649017':[-26.7172,-49.4831,'DOUTOR PEDRINHO'],
    '02649058':[-26.6975,-49.8281,'BARRA DO PRATA'],
    '02649060':[-26.2158,-49.0806,'PRIMEIRO SALTO DO CUBATÃO'],
    '02649061':[-26.895,-49.6722,'BARRAGEM NORTE'],
    '02649073':[-26.1555,-49.3837,'FRAGOSOS'],
    '02649074':[-26.1096,-49.8021,'RIO NEGRO'],
    '02650026':[-26.0854,-50.3288,'DIVISA'],
    '02650027':[-26.0221,-50.5913,'FLUVIÓPOLIS'],
    '02650028':[-26.5871,-50.7451,'FOZ DO CACHOEIRA'],
    '02650029':[-26.2987,-50.9029,'FOZ DO TIMBÓ'],
    '02650030':[-26.373,-50.873,'SANTA CRUZ DO TIMBÓ'],
    '02651001':[-26.8733,-51.7964,'CAMPINA DA ALEGRIA'],
    '02651054':[-26.0671,-51.9129,'SOLAIS NOVOS'],
    '02651055':[-26.0096,-51.6713,'FOZ DO AREIA'],
    '02651056':[-26.0303,-51.1419,'PALMITAL DO MEIO'],
    '02651057':[-26.3879,-51.2721,'JANGADA'],
    '02651058':[-26.1579,-51.2296,'PORTO VITÓRIA'],
    '02651059':[-26.2279,-51.0788,'UNIÃO DA VITÓRIA'],
    '02652023':[-26.3833,-52,'CHOPIM'],
    '02652031':[-26.4003,-52.8956,'SÃO LOURENÇO DO OESTE'],
    '02652048':[-26.0313,-52.6296,'PORTO PALMEIRINHA'],
    '02653002':[-26.2692,-53.6275,'DIONÍSIO CERQUEIRA'],
    '02653004':[-26.6828,-53.2867,'PONTE DO SARGENTO'],
    '02653005':[-26.465,-53.4536,'SÃO JOSÉ DO CEDRO'],
     }


## COLETA DADOS PRECIPITACAO
for posto_codigo, posto_informacoes in postos_precip.items():
    posto_lat = posto_informacoes[0]
    posto_long = posto_informacoes[1]
    posto_nome = posto_informacoes[2]

    ########## AJUSTA SERIE ##########

    serie = ler_mgb(f'./MGB/Precip_MGB/{posto_codigo}.txt')
    serie.columns = ['chuva_mm']
    serie['chuva_mm'] = np.where((serie['chuva_mm'] < 0), np.nan, serie['chuva_mm'])
    serie.index.name = 'data'


    #exporta dados para csv
    with open('./MGB/precip_ajust/'+posto_codigo+'.csv','w',newline='') as file:
        writer = csv.writer(file)
        writer.writerow([posto_codigo])
        writer.writerow([posto_nome])
        writer.writerow([posto_long, posto_lat])
    serie.to_csv('./MGB/precip_ajust/'+posto_codigo+'.csv', mode = 'a', sep = ",",
                     date_format='%Y-%m-%d', float_format='%.2f')

    print(posto_nome, ' acabou - ')
