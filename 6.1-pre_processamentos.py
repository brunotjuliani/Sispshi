#!/usr/bin/python
# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from sys import path; path.append('/simepar/hidro/COPEL/SISPSHI2/Bibliotecas')
from admin import dataexec, serie_horaria
from iguacu import base

""" Programa destinado a conduzir eventuais processos que precisam ser feitos antes de acionar o sistema de previsão de hidrológica
em si. """




# 1 - Previsão de vazão da UHE Salto Caxias
""" Para executar a previsão de vazão para B20 - Porto Capanema é preciso ter a previsão de vazão afluente da UHE Salto Caxias.
No SISPSHI1, fazia-se uma ponderação com base nas previsões de Águas do Verê e Porto Santo Antônio, contudo esse método tende a
subestimar, intensamente, o volume lançado pela UHE.
Para o SISPSHI2 decidiu-se utilizar um perfil médio diário de descarga da UHE. Com base nos dados horários dos últimos cinco dias
será computada a média da vazão para cada uma das 24 horas do dia, gerando um perfil médio de vazão lançada ao longo do dia. Este
perfil será empregado nos dias do período de previsão. """

# Datas de referência e de final do período de previsão
tref, tN = dataexec(['datareferencia','datafinalprevisao'])
# Cinco dias atrás da data de referência
t0 = tref - timedelta(days = 5)
# Dicionário indexado por datetime dos dados observados em UHE Salto Caxias
mtz = serie_horaria( [[base+'/Dados_Bacias/vazao_19.txt', 4]], [t0, tref] )
# Inicializando dicionário de dados para cômputo da vazão média em cada hora do dia
prv = dict( [(i,[0.0,0]) for i in range(24)] )

# Acumulando dados para computar médias horárias
nfal = 0
for dt in mtz.keys():
    if mtz[dt] != None:
        prv[dt.hour][0] += mtz[dt]
        prv[dt.hour][1] += 1
    else:
        nfal += 1

# Não há dados suficientes! Usar um "perfil climatologico" (dados entre 2013-04-03 e 2013-06-19)
clima = {0:1821.0, 1:1391.5, 2:1003.5, 3:766.7, 4:495.0, 5:407.1, 6:460.7, 7:495.6, 8:521.3, 9:724.1, 10:1115.2,
         11:1437.8, 12:1657.6, 13:1822.9, 14:1831.8, 15:1723.5, 16:1757.8, 17:1840.3, 18:1782.9, 19:1821.3,
         20:1938.6, 21:2008.9, 22:2004.5, 23:1954.3}
if nfal >= 108:
    print """\n IN: ~/SISPSHI2/Conceitual/1-preprocessamento.py
     Não há dados de UHE Salto Caxias. Utilizará série climatológica.\n"""
    for h in range(24):
        prv[h][0] = clima[h]
        prv[h][1] = 1

# Computando médias horárias
nfal = 0
for h in range(24):
    if prv[h][1] == 0:
        prv[h] = None
        nfal += 1
    else:
        prv[h] = prv[h][0] / prv[h][1]

# Completando horas sem dados
if nfal != 0:
    print """\n IN: ~/SISPSHI2/Conceitual/1-preprocessamento.py
     Algumas horas do dia estão sem dados entre %s e %s.\n""" % (t0, tref)
    from admin import Preenchimento

    while prv.values().count(None) != 0:
        # Localizando hora com dado, seguida de hora sem dado
        for i in range(24):
            h0, h1 = i, i+1
            if h1 == 24:
                h1 = 0
            if prv[h0] != None and prv[h1] == None: break

        # Confecionando lista para Preenchimento
        dados = [ [h0, prv[h0], clima[h0]] ]
        while prv[h1] == None:
            dados.append( [h1, prv[h1], clima[h1]] )
            h1 += 1
            if h1 == 24:
                h1 = 0
        dados.append( [h1, prv[h1], clima[h1]] )
        
        # Preenchendo série
        aux = Preenchiment(dados)
        for h0, vazao in aux:
            prv[h0] = vazao

# Gravando "previsão" da afluência da UHE Salto Caxias
t0 = tref + timedelta(hours = 1)
arq = open('prev_caxias.txt', 'w')
while t0 <= tN:
    arq.write('%s %8.1f\n' % (t0.strftime('%Y %m %d %H'), prv[t0.hour]))
    t0 += timedelta(hours = 1)
arq.close()
