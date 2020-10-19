#!/usr/bin/python
# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from sys import path, stdout; path.append('/simepar/hidro/COPEL/SISPSHI2/Bibliotecas/')
from os import system
from admin import dataexec, N2F
from iguacu import PluvSISPSHI, BaciaSISPSHI, MediaPonderada, MediaMalha, Thiessen


""" 1-cmb.py: Faz a gestão das séries longas de chuva média nas sub-bacias simuladas pelo SISPSHI2
    Este programa serve para atualizar os arquivos que contém as séries longas de cmb. O tamanho da série longa é determinado pelo intervalo entre as datas gravadas no arquivo ~/SISPSHI2/data.txt correspondente às tags "datainiciohistorico" e "datareferencia". Para cada sub-bacia são geradas cinco séries de chuva, cada uma calculada por um método diferente. A atualização é feita seguindo os seguintes passos:
     - Armazena as séries curtas de chuva horárias nos postos pluviométricos. Estas séries foram geradas em ~/SISPSHI2/Dados_Estacoes/Chuva_01H/;
     - Computa, para cada sub-bacias, as séries curtas de cmb estimadas pelos métodos MEDIA, PC_D2, PC_D4, PM_D2, THSEN;
     - Substitui os dados das séries curta sobre os dados redundantes das séries longas. """
print '\n ~/SISPSHI2/Dados_Bacias/1-cmb.py'


# Listando sub-bacias do SISPSHI2
Lbacs = BaciaSISPSHI()
Nbacs = len(Lbacs)

# Atrelando informações espaciais das sub-bacias que são utilizadas no cálculo da CMB
for i in range(Nbacs):
    Lbacs[i].informacoes_espaciais()    #Função p/ acrescentar atributos '.malha' e '.pluvsprox'. Ver biblioteca 'iguacu.py'

# Listando pluviômetros
Lpluvs = PluvSISPSHI()
Npluvs = len(Lpluvs)
dirchuva = '/simepar/hidro/COPEL/SISPSHI2/Dados_Estacoes/Chuva_01H/'

# Lista de strings para notificação de erros via e-mail
notificacao = []










# PARTE 1: Gerando séries curtas de CMB
#---------------------------------------------------------------------------------------------------------------------------------------
# Inicializando matrizes de dados
dtref, dtbanco = dataexec(['datareferencia','datainiciobanco'])
cpluv = {}    #matriz onde serão armazenadas as séries curtas nos pluviômetros
ccmb1 = {}    #matriz onde serão armazenadas as séries curtas nas bacias
datas = []

dt = dtbanco
while dt <= dtref:
    
    # Matriz de dados dos pluviômetros
    cpluv[dt] = {}
    for P in Lpluvs:
        cpluv[dt][P.codigo] = None

    # Matriz de dados de CMB (5 tipos)
    ccmb1[dt] = {}
    for B in Lbacs:
        ccmb1[dt][B.numero] = [None, None, None, None, None]
        
    datas.append(dt)
    dt += timedelta(hours = 1)


# Armazenando dados das estações
print '     - Incorporando séries horárias dos pluviômetros:'
for P in Lpluvs:
    try:
        arq = open(dirchuva + str('chv01H_%8i.txt' % P.codigo), 'r')
        for L in arq.readlines():
            L = L.split()
            dt, valor = datetime(int(L[0]), int(L[1]), int(L[2]), int(L[3]), 0, 0), float(L[4])
            if valor > -1:    #Registros com falhas estão representado por -99999.9 no arquivo
                try:
                    cpluv[dt][P.codigo] = valor
                except KeyError:

                    # Local para induzir a exclusão de notificação
                    #if P.codigo == 26015237:
                        #continue
                    if P.codigo == 25245437:
                        continue

                    # Notificação automática
                    aux = '~/SISPSHI2/Dados_Bacias/1-cmb.py encontrou registro de chuva horária fora do período de consulta:'
                    if aux not in notificacao:
                        notificacao.append(aux)
                    aux = str(' > ~%s (%s) > %s | %.1f' % (arq.name[21:], P.nome.encode('utf-8'), dt, valor))
                    if aux not in notificacao:
                        notificacao.append(aux)
        arq.close()
        print '          > %-25s (%i)' % (P.nome.encode('utf-8'), P.codigo)
    except IOError:
        print '          > Não encontrou arquivo de dados do posto %-25s (%i)' % (P.nome.encode('utf-8'), P.codigo)


# Computando chuva média na bacia
""" O SISPSHI2 tem como uma de suas características o emprego de ponderações diferentes para calcular a chuva média em cada sub-bacia do sistema. Os métodos aplicados atualmente são:
  ------+-------------------------------------------------------------------------------------------------------------------------------
   ID   |  DESCRIÇÃO
  ------+-------------------------------------------------------------------------------------------------------------------------------
  MEDIA | Média aritmética simples dos pluviometros próximos a bacia.
  PC_D2 | Média ponderada pela distancia^{-2} dos pluviometros mais próximos ao centro da bacia.
  PC_D4 | Equivalente a PC_D2, porém com Norma {-4}.
  PM_D2 | Média da chuva estimada nos pontos de malha da bacia, utilizando PC_D2 em cada ponto de malha.
  THSEN | Método de Thiessen (Média ponderada com base na fração da área da bacia representada pelo polígono de Thiessen de cada
        | pluviometro).
  ------+-------------------------------------------------------------------------------------------------------------------------------
"""
print '     - Estimando chuva média nas sub-bacias:'
for B in Lbacs:
    for dt in datas:

        #Agrupando dados consistentes dos pluviômetros
        """ Os métodos PM_D2 e THSEN, que usam malha, precisam que os dados dos pluviometros estejam indexados pelo código do posto. Entretanto para MEDIA, PC_D2 e PC_D4 é preciso 
        fornecer a lista com os pares (valor, distância), sendo 'valor' a chuva registrada no pluviômetro e 'distância' a distância entre o posto e o ponto central da bacia."""
        Ddados, Ldados = {}, []
        for cod, dist in B.pluvsprox:
            if cpluv[dt][cod] == None:
                continue
            else:
                Ddados[cod] = cpluv[dt][cod]
                Ldados.append([cpluv[dt][cod],dist])

        # Computando CMB por métodos diferentes (caso haja dados)
        if len(Ldados) > 0:
            MEDIA = MediaPonderada(Ldados,0)
            PC_D2 = MediaPonderada(Ldados,2)
            PC_D4 = MediaPonderada(Ldados,4)
            PM_D2 = MediaMalha(Ddados,B.malha,2)
            THSEN = Thiessen(Ddados,B.malha)
            ccmb1[dt][B.numero] = [MEDIA, PC_D2, PC_D4, PM_D2, THSEN]

    print '          > B%2.2i - %s' % (B.numero, B.nome)
#=======================================================================================================================================










# PARTE 2: Atualizando séries longas de CMB
#---------------------------------------------------------------------------------------------------------------------------------------
print '     - Atualizando séries longas:'
dt0 = dataexec(['datainiciohistorico'])

for B in Lbacs:
    
    # Armazendo série longa já existente
    ccmb2 = {}
    try:
        arq = open(str('cmb_%2.2i.txt' % B.numero), 'r')
        for L in arq.readlines():
            L  = L.split()
            dt = datetime(int(L[0]), int(L[1]), int(L[2]), int(L[3]), 0, 0)
            ccmb2[dt] = [float(L[4]), float(L[5]), float(L[6]), float(L[7]), float(L[8])]
        arq.close()
        print '          > Armazenou série longa de CMB na B%2.2i' % (B.numero)

    except IOError:
        aux = '~/SISPSHI2/Dados_Bacias/1-cmb.py não encontrou arquivo da série longa de CMB nas bacias:'
        if aux not in notificacao:
            notificacao.append(aux)
        aux = str(' > B%2.2i - %s' % (B.numero, B.nome))
        if aux not in notificacao:
            notificacao.append(aux)
        print '          > Não encontrou arquivo da série longa de CMB na B%2.2i' % (B.numero)

    # Substituindo série curta sobre a série longa (período de redundância)
    """ Os valores de chuva média na sub-bacia em processamento, estimada pelos diferentes métodos, serão gravadas em cima dos valores que já estiverem presentes na série longa. 
    Entretanto, se as CMB não puderam ser calculada em alguma datahora, o valor da série longa permanecerá inalterado. """
    for dt in datas:
        if ccmb1[dt][B.numero][0] == None: # Tanto faz ser [0], [1], [2], [3] ou [4]
            continue
        else:
            ccmb2[dt] = ccmb1[dt][B.numero][0:5]
    print '          > Aplicou redundância entre as séries curta e longa.'

    # Regravando arquivo com a série longa entre dt0 e dtref
    dt  = dt0
    arq = open(str('cmb_%2.2i.txt' % B.numero), 'w')
    while dt <= dtref:
        arq.write('%4i %2.2i %2.2i %2.2i' % (dt.year, dt.month, dt.day, dt.hour))
        try:
            L = ccmb2[dt]
            arq.write(' %7.2f %7.2f %7.2f %7.2f %7.2f\n' % (N2F(L[0],-999.99), N2F(L[1],-999.99), N2F(L[2],-999.99), N2F(L[3],-999.99),                 
                                                            N2F(L[4],-999.99)))
        except KeyError:
            print '          > Sem dados de CMB na B%2.2i em %s' % (B.numero, dt)
            arq.write(' -999.99 -999.99 -999.99 -999.99 -999.99\n')
        dt += timedelta(hours = 1)
    arq.close()
    print '          > Regravou arquivo com séries longas de CMB.'
#=======================================================================================================================================










# PARTE 3: Reportando ocorrência de erros no programa
#---------------------------------------------------------------------------------------------------------------------------------------
if len(notificacao) == 0:    # Se não houver casos que precisam ser reportados encerra o programa
    print ''
    exit()


""" Este programa envia uma notificação por e-mail quando encontrar registros horários de chuva que não pertençam ao período de consulta. Este problema pode ocorrer quando uma estação pluviométrica é desativada (permanentemente ou temporariamente) e por consequência seus arquivos de dados permanecem nos diretórios de dados mas não são mais atualizados.  """

print '\n----- ENVIO DE RELATORIO -----'
# Criando comando do sendEmail e enviando relatorio
#comando = '/simepar/hidro/sendEmail -f "CQD SISPSHI2 <hidro@simepar.br>" -t "Angelo <angelo@simepar.br>" -o message-charset=utf-8'
comando = '/simepar/hidro/sendEmail -f "CQD SISPSHI2 <hidro@simepar.br>" -t "Jose Eduardo <jose.eduardo@simepar.br>" -o message-charset=utf-8'
comando += str(' -u "Erro no cálculo da CMB em %s"' % dtref)    # Assunto do e-mail
comando += ' -m "'
for L in notificacao:
    comando += str('\n%s' % L)
comando +='" -s mail'
system(comando)
print '----- ENVIO DE RELATORIO -----\n'
#=======================================================================================================================================