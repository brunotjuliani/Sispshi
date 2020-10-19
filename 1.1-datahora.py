#!/usr/bin/python
# -*- coding: utf-8 -*-
from sys import argv
from datetime import datetime, timedelta

""" 1-datahora.py: Gera e grava datas que serão utilizadas na rodada do SISPSHI2

    Programa para gerar o arquivo /simepar/hidro/COPEL/SISPSHI2/data.txt no qual serão gravadas as datas que irão guiar os subprocessos do SISPSHI 2. Ao total serão gravadas 4 
    campos de data e hora distintos, identificadas por "tags" específicas, conforme:
     - linha 1: 'datareferencia'      -> Datahora de referência da rodada = Datahora do último dado das séries observadas. Deve ser fornecido como argumento ao programa. Caso 
     contrário será computada como a hora imediatamente anterior a hora atual do sistema;
     - linha 2: 'datainiciobanco'     -> Datahora inicial do período de consulta dos dados do banco. Esta programada para ser dataref - 120 horas.
     - linha 3: 'datafinalprevisao'   -> Datahora onde se encerra o período de previsão. Esta programada para ser dataref + 120 horas.
     - linha 4: 'datainiciohistorico' -> Datahora para início de arquivos com séries longas e remoção de arquivos gerados em momento anterior a esta datahora. Esta programa para 
     ser dataref - 400 dias.

     O fato de a datahora de referência poder ser fornecida ao programa serve para os casos em que se deseja recuperar rodadas antigas. Entrentato, operacionalmente, o SISPSHI2 
     utiliza a datahora anterior à datahora atual como referência para garantir que haverá dados observados de todas as estações no banco.
"""
print '\n ~/SISPSHI2/1-datahora.py'


# Verificando se quantidade de argumentos fornecida está correta.
""" Os argumentos, incluindo o nome do arquivo do programa, são armazenados automaticamente na lista argv.
Se o programa tiver sido acionado sem argumentos: argv = ['1-datahora.py']. Se tiver sido passado os quatro inteiros (ano, mês, dia e hora), então argv = ['1-datahora.py', ano, mes, dia, hora]. """
if len(argv) not in [1,5]:
    print '\n     ERRO'
    print """     01: Número de argumentos fornecidos ao programa está errado.

     Caso deseje a obtenção automática da datahora de referência (hora anterior à hora atual) execute o programa sem argumentos:
      > python 1-datahora.py

     Se deseja especificar a datahora de referência forneça, na respectiva sequência, o ano, o mes, o dia e a hora, tal como:
      > python 1-datahora.py 2012 6 28 20\n"""
    exit()


# Gerando datahora de referência
if len(argv) == 1:
    """ Nenhum argumento foi fornecido. Utilizada a hora anterior à hora atual do sistema. """
    aux = datetime.now()
    ano, mes, dia, hor = aux.year, aux.month, aux.day, aux.hour
    dref = datetime(ano, mes, dia, hor, 0, 0) - timedelta(hours = 1)
    
    #ms tratamento de horario de verao
    import time
    isdst = time.localtime().tm_isdst
    dref = dref - timedelta(hours=isdst)

else:
    """ A datahora de refêrencia foi fornecida como argumentos do programa."""
    ano, mes, dia, hor = map(int,argv[1:5])
    dref = datetime(ano, mes, dia, hor, 0, 0)


# Gravando arquivo com datahora de referência e demais datahoras utilizadas no SISPSHI2
arq = open('/simepar/hidro/COPEL/SISPSHI2/data.txt','w')
arq.write('%s datareferencia\n' % dref.strftime('%Y %m %d %H'))
print '     - %s <- Datahora de referência.' % dref

daux = dref - timedelta(hours = 120)
arq.write('%s datainiciobanco\n' % daux.strftime('%Y %m %d %H'))
print '     - %s <- Datahora do início do período de consulta ao banco.' % daux

daux = dref + timedelta(hours = 168)
arq.write('%s datafinalprevisao\n' % daux.strftime('%Y %m %d %H'))
print '     - %s <- Datahora do final do período de previsão' % daux

daux = dref - timedelta(days = 400)
arq.write('%s datainiciohistorico\n' % daux.strftime('%Y %m %d %H'))
print '     - %s <- Datahora limite para início de séries de dados e presença de arquivos antigos' % daux

arq.close()
print ''
