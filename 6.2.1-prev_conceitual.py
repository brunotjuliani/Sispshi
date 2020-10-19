#!/usr/bin/python
# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from sys import path, stdout
path.append('/simepar/hidro/COPEL/SISPSHI2/Bibliotecas')
from admin import dataexec, serie_horaria
from iguacu import base, FluvSISPSHI, BaciaSISPSHI, PrevCMB
from simuhidro import bdsimuls, listaprev2 as listaprev, EntradaPadrao, SimulacaoPadrao
from prm_modhid import ParamRRR, ParamSACSIMPLES
import numpy as np

#ATENCAO AQUI ESTA IMPORTANDO listaprev2 (de simuhidro.py) como listaprev! isso muda a configuracao!

""" 2.1-prev_conceitual.py: Executa simulações hidrológicas com modelos conceituais e computa previsão de vazão
    Este programa executa simulações hidrológicas com configurações pré-definidos, entre 100 dias antes da data de referência
(para aquecimento dos estados do modelo) e a data final de previsão (veja dataexec() na biblioteca admin.py).
    A lista 'listaprev' do módulo simuhidro.py guarda quais simulações e a ordem em que serão executadas. Seus elementos são
códigos de simulação, sendo eles as chaves do dicionário 'bdsimuls' (também na biblioteca simuhidro.py). Cada código representa
uma rodada de modelagem atendendo a certas especificações, tais como: modelo hidrológico, conjunto de parâmetros, tipo de CMB,
cenário de CMB na previsão, etc.
    Por padrão, os resultados de cada simulação são gravados em arquivos cujo nome é formado pelo próprio código (em 4 algarismos).
Por exemplo, o arquivo 0910.txt contém os resultados da simulação '910', a qual utiliza o modelo 'RRR' com parâmetros de 2003, CMB
do tipo PC_D2, sem chuva no período de previsão e vazão de montante proveniente da soma das previsões feitas nas rodada 510 e 810.
    Nos arquivos de resultados são gravadas quatro séries, além da série de datahora, na seguinte ordem: chuva média na bacia, vazão
de montante, vazão na exutória e vazão modelada. """
print '\n ~/SISPSHI2/Conceitual/2.1-prev_conceitual.py'




# 1 - Configurações
#-------------------------------------------------------------------------------------------------------------------------------
# Datas do intervalo de simulação/previsão hidrológica
tref, tN = dataexec(['datareferencia', 'datafinalprevisao'])    # Data de referência (último dado observado)
                                                                #e data final do período de simulação
t0 = tref - timedelta(days = 100)    # Data inicial do período de simulação
print '\n     > Simulações entre %s e %s, com previsão a partir de %s.' % (t0, tN, tref+timedelta(hours=1))

# Lista dos datetime, de hora em hora, entre t0 e tN
datas, t = [], t0
while t <= tN:
    datas.append(t)
    t += timedelta(hours = 1)

print '\n     > Reconheceu %i simulações.' % len(listaprev)
#===============================================================================================================================





# 2 - Simulação Hidrológica
#-------------------------------------------------------------------------------------------------------------------------------
for isim in range(len(listaprev)):
    print '     > Simulação %4.4i:' % listaprev[isim],
    stdout.flush()    # forçando a escrita na tela

    """ A primeira parte da simulação é, na verdade, preparar os dados de entrada do modelo. Na biblioteca simuhidro.py existe a
    classe 'entradas', onde todos estes dados são agrupados para então utilizar a função SimulacaoPadrao() para obter a vazão
    modelada. Portanto, agora será montanda uma variável 'entradas' conforme as especificações da simulação. Especialmente para
    simulações que envolvam o modelo SACFRACAO deve-se extender a série de vazão observada sobre o período de previsão, visto
    que ele necessita da vazão na exutória para computar os pesos das simulações para fraçẽos específicas do hidrograma. A
    extensão da série é feita repetindo-se o valor de vazão observada na datahora de referência para todo o período de previsão."""

    # Configurações da simulação e dados de entrada
    info    = bdsimuls [ listaprev[isim] ]
    Bac     = BaciaSISPSHI(info['BACIA'])
    cliente = EntradaPadrao(Bac, t0, tN, listaprev[isim])
    
    t = tref + timedelta(hours = 1)
    while t <= tN:
        cliente.qobs[t] = cliente.qobs[tref]
        t += timedelta(hours = 1)

    print ' Inputs OK!',
    stdout.flush()
    
    if listaprev[isim] == 1512 or listaprev[isim] == 1515:
        t = datetime(2016,2,27,0,0,0)
        while t <= datetime(2016,2,28,0,0,0):
            try:
                 cliente.cmb[t] = cliente.cmb[t]*0.5  #MS: ISSO PARECE SER ALGUM TESTE, DIMINUINDO A CHUVA!
            except KeyError:
                pass
            t += timedelta(hours = 1)

    """ A administração da simulação hidrológica em si, entre t0 e tN, utiliza os dados (chuva, vazão, etc.) e informações (tipo
    de modelo e seus parâmetros) armazenado em 'cliente'. Ela retorna um dicionário com a série horária de vazão modelada. Para
    obter a previsão de vazão deve-se calcular a diferente entre vazão observada e modelada na hora de referência, tref, e
    acrescentar esta diferença aos dados modelados entre tref+1hora e tN. Processo este conhecido como 'ancoragem'. """

    # Série modelada
    Qmod   = SimulacaoPadrao(cliente)
    ancora = cliente.qobs[tref] - Qmod[tref]
    print '| Simulação OK!',

    """ Com exceção da série de evapotranspiração potencial, todos os dados utilizados e gerados na simulação hidrológica são
    gravados no arquivo de resultados. Programas que utilizem estes resultados como inputs devem pegar de seu conteúdo os
    dados em si e, do nome do arquivo, o código da simulação para identificar as configurações da mesma. """
    # Gravando resultados
    arq = open(str('%s/Conceitual/Resultados/%4.4i.txt' % (base, listaprev[isim])), 'w')
    for t in datas:
        
        # Data/hora, chuva e vazão a montate
        if cliente.cmb[t] is None: # Intervenção do Arlan (NAO ENTENDI PQ ISSO PODE ACONTECER!)
	  cliente.cmb[t] = 0.
        arq.write('%s %7.2f %8.1f' % (t.strftime('%Y %m %d %H'), cliente.cmb[t], cliente.qmont[t]))
        
        # Vazão na exutória
        if t <= tref:
            # Período observado
            arq.write(' %8.1f' % cliente.qobs[t])
        else:
            # Período de previsão
            arq.write(' %8.1f' % (Qmod[t] + ancora))

        # Vazão simulada
        arq.write(' %8.1f\n' % Qmod[t])
    arq.close()
    print '| Outputs OK!'
#===============================================================================================================================


print '\n    Etapa de simulação hidrológica concluída.\n'

