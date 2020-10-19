#!/usr/bin/python
# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from sys import path; path.append('/simepar/hidro/COPEL/SISPSHI2/Bibliotecas')
from admin import dataexec
from iguacu import base, curva_descarga
from os import system, listdir

""" Alterações:
 - 31/08/2015 Rodada com simulação 0914 foi trocada pela 0912 e a 0915 pela 0916 visando difundir os resultados
   apresentados na página do SISPSHI para o modelo SAC-SIMPLES;
  
  - 06/05/2020: Arlan alterou o calculo da curva-chave.  """

print '\n~/SISPSHI2/Site_Update/5-xml_copelger.py'


# Definindo data/horas chaves dos plots
tref = dataexec(['datareferencia'])
tfinal = tref + timedelta(hours = 48)    # Apenas as primeiras 48h da previsão são enviadas no XML

# Curva de descarga de União da Vitória


### INTERVENÇÃO 1 (AS, maio-2020) ###
# cd = curva_descarga(26145104)
import pandas as pd
cc = pd.read_csv('curva_chave_UV_EMERGENCIAL.txt',sep=';')
H = cc['h'].values
Q = cc['q'].values
### INTERVENÇÃO 1 (AS, maio-2020) ###


# Local onde serão gravados os arquivos XML
local = '/simepar/copelger/sispshi/'

# Estimando ancoragem para os dados de nível para corrigir deslocamento gerado pela aplicação da curva de descarga sem remanso
arq = open(base+'/Dados_Estacoes/CotaVazao_15M/cot15M_26145104.txt', 'r')
obs = {}
for l in arq:
    nota = int(l[37:38])    
    if nota == 0 or nota == 4:
        obs[ datetime(int(l[0:4]), int(l[5:7]), int(l[8:10]), int(l[11:13]), int(l[14:16]), 0) ] = float(l[28:36])
arq.close()
daux = sorted(obs.keys())

tanc = tref
while tanc >= daux[0]:
    if tanc not in daux:
        tanc -= timedelta(hours = 1)
    else:
        break

arq = open(base+'/Conceitual/Resultados/0912.txt', 'r')
qanc, hanc = None, None
for l in arq:
    t = datetime(int(l[0:4]), int(l[5:7]), int(l[8:10]), int(l[11:13]), 0, 0)
    if t == tanc:
        qanc = float(l[31:39])
        
        ### INTERVENÇÃO 2 (AS, maio-2020) ###
        # hanc = cd.nivel(qanc)
        import numpy as np
        hanc = np.interp(qanc, Q, H)
        ## ### INTERVENÇÃO 2 (AS, maio-2020) ###
        
arq.close()

try:
    anc = obs[tanc] - hanc
except:
    anc = 0.0
    print 'Atenção! Não houve ancoragem do nível'

# Inicializando matriz de dados (48h de previsão de cota e vazão para dois cenários)
mtz, datas = {}, []
t = tref + timedelta(hours = 1)
while t <= tfinal:
    mtz[t] = [None,None,None,None]
    datas.append(t)
    t += timedelta(hours = 1)

# Lendo dados da previsão de vazão sem chuva prevista
arq = open('/simepar/hidro/COPEL/SISPSHI2/Conceitual/Resultados/0912.txt', 'r')
for l in arq:
    l = l.split()
    t = datetime(int(l[0]),int(l[1]),int(l[2]),int(l[3]),0,0)
    if tref < t <= tfinal:
        qprev = float(l[6])
        
        
        ### INTERVENÇÃO 3 (AS, maio-2020) ###
        # hprev = cd.nivel(qprev)
        hprev = np.interp(qprev, Q, H)
        ### INTERVENÇÃO 3 (AS, maio-2020) ###
               
        mtz[t][0] = hprev + anc
        mtz[t][1] = qprev
arq.close()

# Lendo dados da previsão de vazão com previsão de chuva.
arq = open('/simepar/hidro/COPEL/SISPSHI2/Conceitual/Resultados/0916.txt', 'r')
for l in arq:
    l = l.split()
    t = datetime(int(l[0]),int(l[1]),int(l[2]),int(l[3]),0,0)
    if tref < t <= tfinal:
        qprev = float(l[6])
        
        
        ### INTERVENÇÃO 4 (AS, maio-2020) ###
        # hprev = cd.nivel(qprev)
        hprev = np.interp(qprev, Q, H)
        ### INTERVENÇÃO 4 (AS, maio-2020) ###
        
        mtz[t][2] = hprev + anc
        mtz[t][3] = qprev
arq.close()

# Controle de qualidade
nota = {}
for i, t in enumerate(datas):
    nota[t] = [0,0]
    
    if mtz[t][1] != None:
        if 0.0 < mtz[t][1] < 5000:
            if i > 0:
                if abs(mtz[t][1] - mtz[datas[i-1]][1]) > 100:
                    nota[t][0] = 1
        else:
            nota[t][0] = 1
    else:
        nota[t][0] = 1

    if mtz[t][3] != None:
        if 0.0 < mtz[t][3] < 5000:
            if i > 0:
                if abs(mtz[t][3] - mtz[datas[i-1]][3]) > 100:
                    nota[t][1] = 1
        else:
            nota[t][1] = 1
    else:
        nota[t][1] = 1

# Comparação entre previsões
med1, med2, N, tGrafCopel = 0.0, 0.0, 0.0, tref + timedelta(hours = 30)
for t in datas:
    if nota[t][0] == 0 and nota[t][1] == 0 and t <= tGrafCopel:
        med1 += mtz[t][1]
        med2 += mtz[t][3]
        N += 1.0

if N == 0.0:
    print '\n\n ERRO!'
    print ' Não há dados consistentes das previsões. Veja /simepar/hidro/COPEL/SISPSHI2/Site_Update/lixo.txt\n\n'
    arq = open('lixo.txt', 'w')
    arq.write('AAAA MM DD HH COTA912 VAZAO912 NOTA912 COTA916 VAZAO916 NOTA916\n')
    for t in datas:
        arq.write('%s' % t.strftime('%Y %m %d %H'))
        arq.write(' %7.3f %8.2f %7i' % (mtz[t][0], mtz[t][1], nota[t][0]))
        arq.write(' %7.3f %8.2f %7i' % (mtz[t][2], mtz[t][3], nota[t][1]))
        arq.write('\n')
    arq.close()
    exit() # Não atualiza a previsão no XML

else:
    med1, med2 = med1/N, med2/N
    
    if med2 < med1:
        print '\n\n AVISO!'
        print ' Vazão média da previsão com chuva é menor que da previsão sem chuva. Irá usar previsão sem chuva nos dois cenários.\n'
        for t in datas:
            mtz[t][2] = mtz[t][0]
            mtz[t][3] = mtz[t][1]
            nota[t][0] = nota[t][1]

# Gerando arquivos XML das previsões
#arq = open(local+'prevsSemChuva.xml', 'w')
#arq.write('<?xml version="1.0" encoding="ISO-8859-1"?>\n')
#arq.write('<CENARIO Local="UniaoDaVitoria" Id="semChuvaFutura" Origem="Simepar" Tipo="FLUVIOMETRICA"')
#arq.write(' data="%s" hora="%s:00">\n' % (tref.strftime('%d/%m/%Y'), tref.hour))
#for t in datas:
    #arq.write('    <PREVISAO data="%s" hora="%2.2i:00">\n' % (t.strftime('%d/%m/%Y'), t.hour))
    #arq.write('        <VALOR_COTA>%s</VALOR_COTA>\n' % (str('%.3f' % mtz[t][0]).replace('.',',')))
    #arq.write('        <VALOR_VAZAO>%s</VALOR_VAZAO>\n' % (str('%.3f' % mtz[t][1]).replace('.',',')))
    #arq.write('        <QUALIDADE>%1i</QUALIDADE>\n' % (nota[t][0]))
    #arq.write('    </PREVISAO>\n')
#arq.write('</CENARIO>')
#arq.close()
#system(str('cp %s %s/historico/prevsSemChuva_%s.xml' % (arq.name, local, tref.strftime('%Y%m%d%H'))))

#arq = open(local+'prevsComChuva.xml', 'w')
#arq.write('<?xml version="1.0" encoding="ISO-8859-1"?>\n')
#arq.write('<CENARIO Local="UniaoDaVitoria" Id="comChuvaFutura" Origem="Simepar" Tipo="FLUVIOMETRICA"')
#arq.write(' data="%s" hora="%s:00">\n' % (tref.strftime('%d/%m/%Y'), tref.hour))
#for t in datas:
    #arq.write('    <PREVISAO data="%s" hora="%2.2i:00">\n' % (t.strftime('%d/%m/%Y'), t.hour))
    #arq.write('        <VALOR_COTA>%s</VALOR_COTA>\n' % (str('%.3f' % mtz[t][2]).replace('.',',')))
    #arq.write('        <VALOR_VAZAO>%s</VALOR_VAZAO>\n' % (str('%.3f' % mtz[t][3]).replace('.',',')))
    #arq.write('        <QUALIDADE>%1i</QUALIDADE>\n' % (nota[t][1]))
    #arq.write('    </PREVISAO>\n')
#arq.write('</CENARIO>')
#arq.close()

arq = open(local+'prevsSemChuva.xml', 'w')
arq.write('<?xml version="1.0" encoding="ISO-8859-1"?>\n')
arq.write('<ESTACAO Local="UniaoDaVitoria" Id="semChuvaFutura" Origem="Simepar" Tipo="FLUVIOMETRICA"')
arq.write(' data="%s" hora="%s:00">\n' % (tref.strftime('%d/%m/%Y'), tref.hour))
for t in datas:
    arq.write('    <LEITURA data="%s" hora="%2.2i:00">\n' % (t.strftime('%d/%m/%Y'), t.hour))
    arq.write('        <VALOR_NIVEL>%s</VALOR_NIVEL>\n' % (str('%.3f' % (mtz[t][0])).replace('.',',')))
    arq.write('        <QUALIDADE_NIVEL>%1i</QUALIDADE_NIVEL>\n' % (nota[t][0]))
    arq.write('        <VALOR_VAZAO>%s</VALOR_VAZAO>\n' % (str('%.3f' % mtz[t][1]).replace('.',',')))
    arq.write('        <QUALIDADE_VAZAO>%1i</QUALIDADE_VAZAO>\n' % (nota[t][0]))
    arq.write('    </LEITURA>\n')
arq.write('</ESTACAO>')
arq.close()
system(str('cp %s %s/historico/prevsSemChuva_%s.xml' % (arq.name, local, tref.strftime('%Y%m%d%H'))))

arq = open(local+'prevsComChuva.xml', 'w')
arq.write('<?xml version="1.0" encoding="ISO-8859-1"?>\n')
arq.write('<ESTACAO Local="UniaoDaVitoria" Id="comChuvaFutura" Origem="Simepar" Tipo="FLUVIOMETRICA"')
arq.write(' data="%s" hora="%s:00">\n' % (tref.strftime('%d/%m/%Y'), tref.hour))
for t in datas:
    arq.write('    <LEITURA data="%s" hora="%2.2i:00">\n' % (t.strftime('%d/%m/%Y'), t.hour))
    arq.write('        <VALOR_NIVEL>%s</VALOR_NIVEL>\n' % (str('%.3f' % (mtz[t][2])).replace('.',',')))
    arq.write('        <QUALIDADE_NIVEL>%1i</QUALIDADE_NIVEL>\n' % (nota[t][1]))
    arq.write('        <VALOR_VAZAO>%s</VALOR_VAZAO>\n' % (str('%.3f' % mtz[t][3]).replace('.',',')))
    arq.write('        <QUALIDADE_VAZAO>%1i</QUALIDADE_VAZAO>\n' % (nota[t][1]))
    arq.write('    </LEITURA>\n')
arq.write('</ESTACAO>')
arq.close()

system(str('cp %s %s/historico/prevsComChuva_%s.xml' % (arq.name, local, tref.strftime('%Y%m%d%H'))))  

#arq = open('lixo.txt', 'w')
#arq.write('AAAA MM DD HH COTA914 VAZAO914 NOTA914 COTA915 VAZAO915 NOTA915\n')
#for t in datas:
    #arq.write('%s' % t.strftime('%Y %m %d %H'))
    #arq.write(' %7.3f %8.2f %7i' % (mtz[t][0], mtz[t][1], nota[t][0]))
    #arq.write(' %7.3f %8.2f %7i' % (mtz[t][2], mtz[t][3], nota[t][1]))
    #arq.write('\n')
#arq.close()

# Removendo XMLs antigos do histórico
dirHist = local+'historico'
lista = listdir(dirHist)
tlim = tref - timedelta(days = 90)
for arq in lista:
    t = arq.split('_')[1][0:-4]
    t = datetime(int(t[0:4]), int(t[4:6]), int(t[6:8]), int(t[8:10]), 0, 0)
    if t < tlim:
        system(str('rm %s/%s' % (dirHist, arq)))
        print ' removeu %s do historico' % arq
