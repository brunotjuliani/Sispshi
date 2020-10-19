#!/usr/bin/python
# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from sys import path, stdout; path.append('/simepar/hidro/COPEL/SISPSHI2/Bibliotecas')
from os import listdir, mkdir
from admin import dataexec, Ldatas, serie_horaria
from simuhidro import listaprev2 as listaprev
from iguacu import base

""" Programa para armazenar em um único arquivo os dados de chuva média na bacia e vazão na exutória durante o período de previsão
gerados no módulo de previsão por modelos conceituais do SISPSHI2.
    O arquivo de dados é nomeado conforme a data de referência da rodada. O seu conteúdo é composta por quatro informações:
    1 - código da simulação;
    2 - data/hora dos dados;
    3 - dado de chuva média na bacia;
    4 - vazão na exutória.
    Os códigos das simulações são obtidos da lista 'listaprev' presente na biblioteca simuhidro, a qual coincide com as simulações
executadas para gerar as previsões de vazão por modelos conceituais. Fica implicito ao código as informações sobre: número da bacia
no SISPSHI, tipo de CMB utilizada, modelo hidrológico utilizado, conjunto de parâmetros utilizado, dados de vazão de montante
utilizado.
    A data/hora do dado é composta por quatro colunas na seguinte ordem "ANO MES DIA HORA". O período de dados gravados vai desde a
data/hora de referência até a data/hora do final do período de previsão. Por comodidade, "data/hora de referência" será nomeado por
"tref" e "data/hora do final do período de previsão" por "tN".
    O dado de chuva média na bacia em tref é obtido a partir da série de dados observados. De tref + 1 hora até tN os dados são
oriundos da previsão de quantitativa de chuva por modelo de simulação atmosférica.
    Em tref, o dado presente na coluna de vazão na exutória corresponde na realidade ao valor de ancoragem utilizado para correção
do BIAS da série prevista. Este valor é calculado por Qobs[tref] - Qsim[tref], onde Qobs é a vazão observada e Qsim a vazão simulada.
De tref + 1 hora até tN são armazenados os dados de previsão de vazão, que correspondem a Qsim[t] + ancoragem. """
print '\n     ~/SISPSHI2/Historico_Previsoes/1-armazena_prev_conceitual.py\n'

# Data/hora de referência e final da previsão
tref, tN = dataexec(['datareferencia','datafinalprevisao'])
datas = Ldatas(tref+timedelta(hours=1), tN)

# Verificando se o diretório para gravação do resultado precisa ser criado
ano, mes = str('%4.4i' % tref.year), str('%2.2i' % tref.month)
if ano not in listdir(base+'/Historico_Previsoes'):
    mkdir(base + str('/Historico_Previsoes/%s' % ano))
if mes not in listdir(base + str('/Historico_Previsoes/%s' % ano)):
    mkdir(base + str('/Historico_Previsoes/%s/%s' % (ano, mes)))

# Arquivo onde serão gravados as previsões de todas as simulações
arq = open(base + str('/Historico_Previsoes/%s/%s/%s.txt' % (ano, mes, tref.strftime('%Y%m%d%H'))), 'a')




# Ciclo das simulações com modelo conceitual já executadas
print '     > Simulação: ',
for cod in listaprev:
    arq2 = base+str('/Conceitual/Resultados/%4.4i.txt' % cod)
    mtz  = serie_horaria([[arq2, 4,6,7]], [tref, tN], rejeito = -9e12)    # 'rejeito' posto com um valor muito pequeno para não
                                                                          #transformar previsões menores que -99 em None.
    # Valor da ancoragem
    anc = mtz[tref][1] - mtz[tref][2]
    
    # Dados em tref
    arq.write('%4.4i %s %7.2f %8.1f\n' % (cod, tref.strftime('%Y %m %d %H'), mtz[tref][0], anc))
    
    # Dados da previsão
    for t in datas:
        arq.write('%4.4i %s %7.2f %8.1f\n' % (cod, t.strftime('%Y %m %d %H'), mtz[t][0], mtz[t][1]))

    # Encerrando armazenamento da simulação atual
    print cod,
    stdout.flush()

arq.close()
print '\n'
