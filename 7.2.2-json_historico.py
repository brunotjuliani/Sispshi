#!/usr/bin/python
# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from sys import path, stdout; path.append('/simepar/hidro/COPEL/SISPSHI2/Bibliotecas/')
from admin import dataexec, serie_horaria
from iguacu import BaciaSISPSHI, base

""" 2-json_historico.py: Gerar arquivos no formato JSON dos histórico de dados de:
       1 - chuva média na bacia (tipo PM_D2);
       2 - vazão contribuinte de montante;
       3 - série de vazão preenchida;
       4 - série de vazão observada.
    Os arquivos gerados são gravados diretamente no diretório de dados do site, '/simepar/hidro/webdocs/sispshi2/dados/'. """
print '\n ~/SISPSHI2/Site_Update/2-json_historico.py'


# Data inicial e final do período de consulta
d0, dN = dataexec(['datainiciohistorico','datareferencia'])

# Lista de datahora a cada 1 hora entre d0 e dN
datas, dt = [], d0
while dt <= dN:
    datas.append(dt)
    dt += timedelta(hours = 1)
ND = len(datas)

# Lista das bacias do SISPSHI2
Lbac = BaciaSISPSHI()

# Local onde serão gravados os arquivos
dirSite = '/simepar/hidro/webdocs/sispshi2/dados/'




# Ciclo das bacias
for B in Lbac:
    
    #Chuva média na bacia   
    arquiv = base + str('/Dados_Bacias/cmb_%2.2i.txt' % B.numero)
    cmb = serie_horaria( [ [arquiv, 7] ], [d0, dN] )

    # Dados de vazão contribuinte a montante
    if (len(B.montante) == 0) and (B.numero not in [16, 19, 20]):
        qmont = dict( [(dt, 0.0) for dt in datas] )
        
    else:
        aux = []
        
        if B.numero == 16:
            aux.append( [base + '/Dados_Bacias/vazao_13.txt', 5] )
            aux.append( [base + '/Dados_Usinas/GBM.txt', 5] )
            
        elif B.numero == 19:
            aux.append( [base + '/Dados_Usinas/SOS.txt', 5] )
            
        elif B.numero == 20:
            aux.append( [base + '/Dados_Usinas/SCX.txt', 5] )
            
        else:
            for b in B.montante:
                arquivo = base + str('/Dados_Bacias/vazao_%2.2i.txt' % b)
                aux.append( [arquivo,5] )
        
        qmont = serie_horaria( aux, [d0,dN], 'somar' )

    # Vazão observada, séries com e sem preenchimento de falhas
    arquiv = base + str('/Dados_Bacias/vazao_%2.2i.txt' % B.numero)
    qobs = serie_horaria( [[arquiv, 4, 5]], [d0,dN], 'apendar' )


    # Gravando arquivo JSON com as séries históricas
    json = open(dirSite + str('histbac_%2.2i.json' % B.numero), 'w')
    json.write('[ ')
    
    def valor(x):
        if x is None:
            return 'null'
        else:
            return str('%.1f' % round(x,1))
    
    for dt in datas:        
        json.write('[%i, %i, %i, %i' % (dt.year, dt.month, dt.day, dt.hour))
        
        try:
            json.write(', %s' % valor(cmb[dt]))
        except KeyError:
            json.write(', null')

        try:
            json.write(', %s' % valor(qmont[dt]))
        except KeyError:
            json.write(', null')

        try:
            json.write(', %s' % valor(qobs[dt][1]))
        except KeyError:
            json.write(', null')
            
        try:
            json.write(',%s' % valor(qobs[dt][0]))
        except KeyError:
            json.write(', null')
        
        if dt < datas[-1]:
            json.write('],\n')
        else:
            json.write('] ]')

    json.close()
    print '     - Gravou arquivo JSON das séries históricas de B%2.2i.' % B.numero


