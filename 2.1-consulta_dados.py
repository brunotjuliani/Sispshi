#!/usr/bin/python
# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from os import system, putenv
from sys import path; path.append('/simepar/hidro/COPEL/SISPSHI2/Bibliotecas/')
from iguacu import PluvSISPSHI, FluvSISPSHI
from admin import dataexec

""" 1-consulta_dados.py: Obtêm séries de chuva, nível e vazão nas estações do SISPSHI2
    O programa irá gerar um script de consulta ao banco de dados PostGreSQL para extrair as séries de dados brutos de chuva, cota e vazão, registrados nos postos de monitoramento utilizados pelo SISPSHI2. O período de consulta é determinado pelo intervalo entre as datas gravadas no arquivo /simepar/hidro/COPEL/SISPSHI2/data.txt correspondente aos tags "datareferencia" e "datainiciobanco". Também é incluida na consulta a nota atribuida pelo controle de qualidade dos dados.
    
    A relação de pluviômetros é dada pela lista pluvs_sispshi e a relação de estações fluviométricas pela lista fluvios_sispshi. Ambas estão localizadas no arquivo estacoes.py do diretório Bibliotecas. """
print '\n ~/SISPSHI2/Dados_Estacoes/1-consulta_dados.py'




# Obtendo data de referência da rodada e data inicial para o período de consulta dos dados ao banco.
dtref, dtinicio = dataexec(['datareferencia','datainiciobanco'])
print '     - Período da consulta: %s a %s' % (dtinicio,dtref)

# Alterando datahoras para GMT (horário em que os dados são armazenados no banco)
dtref    += timedelta(hours = 3)
dtinicio += timedelta(hours = 3) - timedelta(minutes = 45)
""" OBS: A datahora de tag 'datainiciobanco' não deve começar no minuto 0 e sim no minuto 15 da hora anterior. Ao computar a chuva horária o acumulado se dá a partir do valor registrado no minuto 15 da hora anterior até o minuto 0 da hora correspondente do dado. Portanto, se a consulta iniciar em uma datahora com minuto zero, o valor de chuva horária para esta hora será computada apenas pelo valor desse dado, sem somar os valores registrados nos minutos 15, 30 e 45 da hora anterior. """


# Lista dos pluviômetros e das estações fluviométricas
Lpluvs = PluvSISPSHI()
Lfluvs = FluvSISPSHI()
print '     - %i pluviômetros e %i postos fluviométricos' % (len(Lpluvs), len(Lfluvs))




# Script de consulta ao banco de dados PostGreSQL
""" Será gerado um script para realizar a consulta dos dados hidrológicos no banco PostGreSQL. O resultado serão dois arquivos, um com as séries de dados de chuva, obtidos nos pluviômetros a cada 15 minutos, e outro com as séries de nível e de vazão nos postos fluviométricos, também na frequência de 15 minutos."""
arq = open('script_consulta.sql', 'w')

# Cabeçalho geral do script
arq.write("""-- Script PostGreSQL para consulta de dados de chuva, nível e vazão.
\\t
\pset footer null
""")


# Nomeando arquivo de dados de chuva
arq.write("""
-- Consultando dados de chuva, registrados de 15 em 15 minutos, nas estações meteorológicas e hidrológicas do SISPSHI2.
\o chuva_15M.txt
""")

# Escolhendo campos para consulta e definindo estilo e timezone da data
arq.write("""select horestacao,
       to_char(hordatahora - '3 hours'::interval,'yyyy mm dd hh24 mi') as hordatahora,
       horsensor,
       horleitura,
       horqualidade\n""")
arq.write("from horaria\n")
arq.write("where hordatahora >= '%s'\n" % dtinicio)
arq.write("  and hordatahora <= '%s'\n" % dtref)

# Listando estações com pluviometros
arq.write('  and horestacao in (%8i,    -- %s\n' %(Lpluvs[0].codigo, Lpluvs[0].nome.encode('utf-8')))
for p in range(1, len(Lpluvs)):
    if Lpluvs[p].codigo != Lpluvs[-1].codigo:
        arq.write('                     %8i,    -- %s\n' %(Lpluvs[p].codigo, Lpluvs[p].nome.encode('utf-8')))
    else:           #Após a última estação deve ser colocado um ')' ao invés de ','.
        arq.write('                     %8i)    -- %s\n' %(Lpluvs[p].codigo, Lpluvs[p].nome.encode('utf-8')))

# Concluindo bloco de consulta de chuva
arq.write("""  and horsensor = 7\norder by horestacao, hordatahora;
\o
""")


# Nomeando arquivo de dados de fluviométricos
arq.write("""
-- Consultando dados de cota e vazão, registrados de 15 em 15 minutos, nas estações hidrológicas do SISPSHI2.
\o cotavazao_15M.txt
""")

# Escolhendo campos para consulta e definindo estilo e timezone da data
arq.write("""select horestacao,
       to_char(hordatahora - '3 hours'::interval,'yyyy mm dd hh24 mi') as hordatahora,
       horsensor,
       horleitura,
       horqualidade\n""")
arq.write("from horaria\n")
arq.write("where hordatahora >= '%s'\n" % dtinicio)
arq.write("  and hordatahora <= '%s'\n" % dtref)

# Listando estações com pluviometros
arq.write('  and horestacao in (%8i,    -- %s\n' %(Lfluvs[0].codigo, Lfluvs[0].nome))
for p in range(1, len(Lfluvs)):
    if Lfluvs[p].codigo != Lfluvs[-1].codigo:
        arq.write('                     %8i,    -- %s\n' %(Lfluvs[p].codigo, Lfluvs[p].nome))
    else:           #Após a última estação deve ser colocado um ')' ao invés de ','.
        arq.write('                     %8i)    -- %s\n' %(Lfluvs[p].codigo, Lfluvs[p].nome))

# Concluindo bloco de consulta de chuva
arq.write("""  and horsensor in (18,33)\norder by horestacao, horsensor, hordatahora;
\o
\q
""")


# Encerrando confecção do script
arq.close()
print '     - Gerado script PostGreSQL: %s' % arq.name




# Executando script para consulta dos dados
print '\n----- POSTGRESQL -----'
putenv('PGPASSWORD','hidrologia')
#system(str('psql -h tornado-slave1 -d clim -p 5432 -U hidro -f %s' % arq.name))
system(str('psql -h tornado -d clim -p 5432 -U hidro -f %s' % arq.name))
print '----- POSTGRESQL -----\n'

