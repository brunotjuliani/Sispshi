#!/usr/bin/python
# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from sys import path, stdout; path.append('/simepar/hidro/COPEL/SISPSHI2/Bibliotecas/')
from os import system
from iguacu import PluvSISPSHI, FluvSISPSHI, curva_descarga
from admin import dataexec, N2F, interpola_linear, ler_arquivo


""" 2-consulta_dados.py: Gera séries horárias consistidas de chuva e vazão em cada posto de monitoramento
    A partir dos registros de 15 em 15 minutos, este programa irá computar o acumulado horário da chuva e a vazão média em cada hora. Entretanto, antes dessa contabilidade são
aplicados testes para identificar e remover eventuais dados espúrios (ainda de caráter grosseiro, ou seja, dados claramente inconsistentes) das séries de 15 minutos.
    Vale lembrar que estes dados já são analisados pelo sistema automático de CQD, contudo este programa revisa este CQD utilizando parâmetros próprios para cada estação de
monitoramento.

    Os testes aplicados aos dados de chuva de 15 minutos são:
     - TESTE 1 - Limites em 15 minutos: Cada registro não pode superar 45 mm, nem ser nulo.
     - TESTE 2 - Limites em 60 minutos: Conjuntos de 4 registros adjacentes (1 hora) não podem superar um acumulado de 90 mm.
     - TESTE 3 - Picos isolados: Registros acima de 25 mm devem pertencer a um acumulado horário superior a 25 mm.
     - TESTE 4 - Persistência de registros não-nulos: Valores iguais ou inferiores a 2 mm não podem ser repetidos por mais de 6 horas consecutivas (24 registros de 15 minutos).
                 Para valores superiores a 2 mm serão reprovadas sequências de dados idênticos por mais de 1 hora (4 registros consecutivos)

    Os testes aplicados nos dados de cota registrados a cada 15 minutos são:
     - TESTE 5 - Limite máximo e mínimo: Registros que estejam abaixo de 60% do menor registro histórico e acima de 140% do maior serão considerados inconsistentes.
     - TESTE 6 - Spikes pontuais: Registros que são maiores, ou menores, que os registros adjacentes (1 antes e 1 depois) e, sendo esta diferença superior ao maior degrau de vazão
                 em 15 minutos no histórico do posto fluviométrico, serão considerados inconsistentes.
     - TESTE 7 - Vizinhos incômodos: Registros consistentes cuja vizinhança (1 dado antes e 1 dado depois) seja composta por dados inconsistentes, ou ausentes, serão marcados como 
                 inconsistentes.

    Preenchimento automático nas séries de cota a cada 15 minutos:
     - Sequências de registros ausentes ou inconsistentes com extensão igual ou inferior à janela de auto-correlação acima de 0,995 para o posto em questão serão preenchidas por 
       interpolação linear.

    Não são aplicados testes de consistência ou ações de preenchimento nas séries horárias. (Não neste programa)

    Quando o programa identificar dados espúrios, não detectados pelo CQD do banco, os mesmos serão marcados com nota 9 e uma notificação será enviada por e-mail sobre o ocorrido. 
O arquivo com o log da consistência será renomeado, incluindo a data de referência no nome, para que o mesmo não seja sobrescrito em rodadas futuras do SISPSHI2. """
print '\n ~/SISPSHI2/Dados_Estacoes/2-series_horarias.py'


# Período (esperado) dos dados consultados
dtref, dtinicio = dataexec(['datareferencia','datainiciobanco'])
dtinicio -= timedelta(minutes = 45)
datas, dt = [], dtinicio
while dt <= dtref:
    datas.append(dt)
    dt += timedelta(minutes = 15)
ndad = len(datas)    # ndad = número total de dados na série consultada

# Arquivo onde serão gravadas estatísticas da verificação de consistência dos dados
afal = open('controle_qualidade.txt','w')
CQinfo = []       # Lista onde serão armazenadas informações para notificar a ocorrência de inconsistências

# Função para gerar série de chuva acumulada
def chuva_acumulada(chvin):
    """ Recebe o dicionário 'chvin' com a série de dados e notas a cada 15 minutos e retorna dicionário semelhante, porém contendo apenas a série de chuva acumulada contínua, não 
    acumulando ao encontrar notas diferentes de 0. """
    mtz, acm = {}, 0.0
    global datas
    for dt in datas:
        if chvin[dt][1] == 0:
            acm += chvin[dt][0]
        mtz[dt] = acm
    return mtz










# PARTE 1: Manipulação das séries de CHUVA
#---------------------------------------------------------------------------------------------------------------------------------------
# Reconhecendo pluviômetros e armazenando séries de dados
Lpluvs = PluvSISPSHI()
chuva  = ler_arquivo('chuva_15M.txt')
NDB    = len(chuva)    # NDB = Número de Dados do Banco
print '\n     - Armazenou dados do arquivo de séries brutas de chuva; %i linhas.' % (NDB)


# Conferindo presença dos pluviômetros
Lpluvs2 = []
for i in range(NDB):
    if chuva[i][0] not in Lpluvs2:
        Lpluvs2.append(chuva[i][0])
aux = []
if len(Lpluvs2) != len(Lpluvs):
    print '     - Encontrados %i pluviômetros sem dados:' % (len(Lpluvs)-len(Lpluvs2)),
    for P in Lpluvs:
        if P.codigo not in Lpluvs2:
            print ' %i (%s),' % (P.codigo, P.nome.encode('utf-8')),
            aux.append(P)
    for P in aux:
        Lpluvs.remove(P)
    print ''
NP = len(Lpluvs)
del Lpluvs2, aux


# Operando cada pluviômetro
""" Posto a posto, as séries de dados de chuva a cada 15 minutos serão re-avaliadas pelos testes 1 a 4 (ver descrição geral do programa). Os dados reprovados pelo CQD do banco ou 
pelo CQD aplicado neste programa serão removidos quando for geradas séries horárias de chuva."""
afal.write('Processo de controle de qualidade iniciado em %s\n' % datetime.now())

for iP, P in enumerate(Lpluvs):
    chv15M = dict([(dt,[None,None]) for dt in datas])
    afal.write('\n\n     %s (%i) CHUVA 15 minutos:' % (P.nome.encode('utf-8'), P.codigo))
    print '     - Verificando chuva em %s (%i):'  % (P.nome.encode('utf-8'), P.codigo)

    # Isolando dados de chuva a cada 15 minutos para o posto em processamento e contabilizando resultados do CQ automático
    cont = [0 for i in range(5)]
    for i in range(NDB):
        if chuva[i][0] == P.codigo:
            dt = datetime(chuva[i][1], chuva[i][2], chuva[i][3], chuva[i][4], chuva[i][5], 0)
            chv15M[dt] = [chuva[i][7], chuva[i][8]]    # 7 = valor; 8 = nota
            cont[chuva[i][8]] += 1    # Contador de dados com a mesma nota
    for i in range(5):
        afal.write('\n- Dados c/ nota %i: %12i (%6.2f%%)' % (i, cont[i], (cont[i]*100.0/float(ndad))))
    aux = cont[0] + cont[4]

    # Contabilizando dados ausentes e transformando nota 4 em 0
    cont = 0
    for dt in datas:
        if chv15M[dt][1] == None:
            cont += 1
        elif chv15M[dt][1] == 4:    # Esta etapa serve para facilitar a diferenciação entre dados consistentes e não-consistentes.
            chv15M[dt][1] = 0
    afal.write('\n- Dados ausentes:  %12i (%6.2f%%)' % (cont, (cont*100.0/float(ndad))))
    
    print '          > Dados disponíveis (pré-aval) = %i dados, %6.2f%% da série.' % (aux, (aux*100.0/float(ndad)))


    # TESTE 1: Valores máximos e mínimos para registros únicos (15 minutos)
    cont = 0
    for dt in datas:
        valor, nota = chv15M[dt]
        if valor != None:    # Não aplicável a dados ausentes
            if 0 <= valor <= 50:
                if 1 <= nota <= 3:
                    chv15M[dt][1] -= 1    # Reaprovando dado no teste de limite
            else:
                if nota == 0:
                    chv15M[dt][1] = 9
                    cont += 1
                if cont == 1:
                    afal.write('\n- Dados reprovados no TESTE 1:')
                if cont != 0:
                    afal.write('\n    > %s %12.3f %i' % (dt.strftime('%Y %m %d %H %M'), chv15M[dt][0], chv15M[dt][1]))
    if cont > 0:
        afal.write('\n    > Total de dados reprovados pelo programa:  %12i (%6.2f%%)' % (cont, (cont*100.0/float(ndad))))

    print '          > Processou TESTE 1',
    stdout.flush()


    # TESTE 2: Máximos horários
    chvacm = chuva_acumulada(chv15M)    # Dicionário de chuva acumulada, versão 1
    falhas = []    # 'falhas' é uma lista com as datahora dos dados reprovados

    # 2.1 Indentificando acumulados horários inconsistentes
    for i in range(3,ndad):
        acmhor = chvacm[datas[i]] - chvacm[datas[i-3]]
        if acmhor > 90:
            for j in range(4):
                if datas[i-j] not in falhas:
                    falhas.append(datas[i-j])
    falhas.sort()    # Organizando dados reprovados em ordem cronológica apenas por estética

    # 2.2 Reprovando dados de 15 minutos que pertençam a acumulados horários inconsistentes
    cont = 0
    if len(falhas) > 0:
        afal.write('\n- Dados reprovados no TESTE 2:')
        for dt in falhas:
            if chv15M[dt][1] == 0:
                chv15M[dt][1] = 9
                cont += 1
            afal.write('\n    > %s %12.3f %i' % (dt.strftime('%Y %m %d %H %M'), chv15M[dt][0], chv15M[dt][1]))
    if cont > 0:
        afal.write('\n    > Total de dados reprovados pelo programa:  %12i (%6.2f%%)' % (cont, (cont*100.0/float(ndad))))

    print ', 2',
    stdout.flush()


    # TESTE 3: Registros isolados acima de 25 mm
    """ Quando o dado na posição 'i' é maior que 25 preciso verificar se o acumulado nas janelas [i-3,i], [i-2,i+1], [i-1,i+2], [i, i+3] supera o valor do próprio dado. Isto deve 
ocorrer numa situação consistente pois 25 mm em 15 minutos é um volume alto e, provavelmente, oriundo de um evento meteorológico com escala temporal maior. Portanto, deve haver 
qualquer registro não-nulo entre 1 hora antes e 1 hora depois do registro em análise. Entretanto, como a série de dados inicia na posição 0 e termina na posição ndad-1, não posso 
aplicar este teste nos três primeiros registros nem nos três últimos, pois as janelas de 1 hora precisariam de dados além dos disponíveis. """
    chvacm = chuva_acumulada(chv15M)    # Dicionário de chuva acumulada, versão 2
    cont   = 0
    for i in range(3,ndad-3):
        valor, nota = chv15M[datas[i]]
        if nota == 0 and valor > 25:
            T3 = True
            for j in range(4):
                acmhor = chvacm[datas[i+j]] - chvacm[datas[i+j-3]]
                if acmhor > valor:
                    T3 = False
                    break
            if T3:    # É um pico isolado
                if cont == 0:
                    afal.write('\n- Dados reprovados no TESTE 3:')
                dt = datas[i]
                chv15M[dt][1] = 9
                afal.write('\n    > %s %12.3f %i' % (dt.strftime('%Y %m %d %H %M'), chv15M[dt][0], chv15M[dt][1]))
                cont += 1
    if cont > 0:
        afal.write('\n    > Total de dados reprovados pelo programa:  %12i (%6.2f%%)' % (cont, (cont*100.0/float(ndad))))

    print ', 3',
    stdout.flush()


    # TESTE 4: Persistência de registros não-nulos
    # 4.1 Identificando períodos com repetição contínua do mesmo valor
    dt = datas[0]
    pers, aux = [], [ [dt, max(-999.99, chv15M[dt][0])] ]    # Utilizei max() para evitar variável None: max(valor,None) = valor
    for i in range(1,ndad):
        valor, nota = chv15M[datas[i]]
        if nota == None:
            continue        
        if round(valor,1) != round(aux[-1][1],1):
            valor_repetido = aux[-1][1]
            if valor_repetido > 0.0:
                # Quando valor_repetido for 2.0 ou menos, não admite períodos maiores que 6 horas
                if len(aux) >= 24 and valor_repetido <= 2.0:
                    pers.append([aux[0][0],aux[-1][0],len(aux),aux[-1][1]]) # [dt inicial, dt final, qtde de dados, valor repetido]
                # Quando valor_repetido for maior que 2.0, não admite períodos maiores que 1 hora
                if len(aux) >= 4 and valor_repetido > 2.0:
                    pers.append([aux[0][0],aux[-1][0],len(aux),aux[-1][1]])
            aux = [[datas[i],valor]]
        else:
            aux.append([datas[i],valor])

    # 4.2 Reprovando dados nos períodos de persistência
    if len(pers) > 0:
        afal.write('\n- Dados reprovados no TESTE 4:')
        cont = 0
        for dti, dtf, duracao, valor_repetido in pers:
            while dti <= dtf:
                if chv15M[dti][1] == 9:    # Se o dado já tiver sido reprovado pelo programa antes, passa para o próximo
                    dti += timedelta(minutes = 15)
                    continue
                elif chv15M[dti][1] == 0:
                    chv15M[dti][1] = 9
                    cont += 1
                afal.write('\n    > %s %12.3f %i' % (dt.strftime('%Y %m %d %H %M'), chv15M[dti][0], chv15M[dti][1]))
                dti += timedelta(minutes = 15)
        if cont != 0:
            afal.write('\n    > Total de dados reprovados pelo programa:  %12i (%6.2f%%)' % (cont, (cont*100.0/float(ndad))))

    print ', 4'
    stdout.flush()


    # Recomputando presença de dados inconsistentes
    cont = [0 for i in range(6)]
    for dt in datas:
        if chv15M[dt][1] == None:
            cont[5] += 1
        elif chv15M[dt][1] == 9:
            cont[4] += 1
        else:
            cont[chv15M[dt][1]] += 1
    for i in range(6):
        if i <= 3:
            afal.write('\n- Dados c/ nota %i: %12i (%6.2f%%)' % (i, cont[i], (cont[i]*100.0/float(ndad))))
        elif i == 4:
            afal.write('\n- Dados c/ nota 9: %12i (%6.2f%%)' % (cont[4], (cont[4]*100.0/float(ndad))))
            if cont[4] > 0:
                aux = str('chuva %8i' % P.codigo)
                if aux not in CQinfo: CQinfo.append(aux)
        else:
            afal.write('\n- Dados ausentes:  %12i (%6.2f%%)' % (cont[5], (cont[5]*100.0/float(ndad))))

    print '          > Dados disponíveis = %i dados, %6.2f%% da série.' % (cont[0], (cont[0]*100.0/float(ndad)))
    

    # Regravando séries de chuva (15 minutos e horária)
    arqM = open(str('Chuva_15M/chv15M_%8i.txt' % P.codigo),'w')    # Arquivo de série de 15 minutos
    arqH = open(str('Chuva_01H/chv01H_%8i.txt' % P.codigo),'w')    # Arquivo de série horária
    
    for i in range(ndad):
        dt = datas[i]
        if chv15M[dt][1] == None:
            chv15M[dt] = [-99999.9,9]
        arqM.write('%s %8.1f %1i\n' % (dt.strftime('%Y %m %d %H %M'), chv15M[dt][0], chv15M[dt][1]))
        
        # Computando chuva horária quando minuto é zero
        if dt.minute == 0:
            i0 = max(0, i-3)
            acm, n = 0.0, 0
            for j in range(i0,i+1):
                if chv15M[ datas[j] ][1] == 0:
                    acm += chv15M[ datas[j] ][0]
                    n += 1
            if n == 0:
                acm = -99999.9
            arqH.write('%s %8.1f\n' % (dt.strftime('%Y %m %d %H'), acm))

    arqM.close()
    arqH.close()
    print '          > Regravou arquivos com séries de chuva.'

# Removendo dados de chuva da memória
del chuva, Lpluvs, chv15M
#=======================================================================================================================================










#PARTE 2: Manipulação das séries de COTA e VAZÃO
#---------------------------------------------------------------------------------------------------------------------------------------
#Reconhecendo postos fluviométricos (hidrológicos) e armazenando séries de dados
Lfluvs = FluvSISPSHI()
cotvaz = ler_arquivo('cotavazao_15M.txt')
NDB    = len(cotvaz)    # NDB = Número de Dados do Banco
print '\n     - Armazenou dados do arquivo de séries brutas de cota e vazão; %i linhas.' % (NDB)


#Conferindo presença dos postos fluviométricos
Lfluvs2 = []
for i in range(NDB):
    if cotvaz[i][0] not in Lfluvs2:
        Lfluvs2.append(cotvaz[i][0])
aux = []
if len(Lfluvs2) != len(Lfluvs):
    print '     - Encontrados %i postos fluviométricos sem dados:' % (len(Lfluvs)-len(Lfluvs2)),
    for P in Lfluvs:
        if P.codigo not in Lfluvs2:
            print ' %i (%s),' % (P.codigo, P.nome),
            aux.append(P)
    for P in aux:
        Lfluvs.remove(P)
    print ''
NP = len(Lfluvs)
del Lfluvs2, aux


#Operando postos fluviométricos
""" Devido a existência de remanso no cálculo de vazão para alguns postos fluviométricos, as séries de cota a cada 15 minutos não serão analisadas isoladamente em todo o processo 
de CQD e confecção das séries horárias de vazão. Por este motivo os registros serão armazenado em uma matriz (dicionário) indexada pela datahora e pelo código do posto. 
Posteriormente, posto a posto, as séries de dados de cota a cada 15 minutos serão re-avaliadas pelos testes 5 a 6 (ver descrição geral do programa). Sequências curtas de dados 
ausentes ou inconsistentes serão substituidas por interpolação linear. Com as séries de cotas avaliadas e preenchidas dar-se-á a análise da vazão e geração das seéries horárias 
desta variável.
    Como dito, a verificação da vazão é feita depois da cota devido a existência de remanso em alguns postos. Isso significa que para estes postos a vazão é estimada com base nos 
registros de cota do posto em si e de um posto a jusante. Portanto, é preciso que as séries de cotas já estejam todas consistidas."""
afal.write('\n\n\nProcesso de controle de qualidade continuando em %s\n' % datetime.now())    # Marcando posição no arquivo

#Reorganizando séries de dados fluviométrico em matriz
flu15M = {}
for dt in datas:
    flu15M[dt] = dict([(P.codigo,[None,None,None]) for P in Lfluvs])

for i in range(NDB):
    dt = datetime(cotvaz[i][1], cotvaz[i][2], cotvaz[i][3], cotvaz[i][4], cotvaz[i][5], 0)
    if dt.minute not in [0,15,30,45]: continue    # Por algum motivo desconhecido dados nos minutos 59 e 29 já foram inseridos no banco.

    codigo, sensor, valor, nota = int(cotvaz[i][0]), int(cotvaz[i][6]), float(cotvaz[i][7]), int(cotvaz[i][8])
    if sensor == 18:    # Cota [m]
        flu15M[dt][codigo][0] = valor
        flu15M[dt][codigo][1] = nota
    if sensor == 33:    # Vazão [m3/s] *vazão não passa pelo CQD do banco
        flu15M[dt][codigo][2] = valor
print '     - Reorganizou dados fluviométricos de 15 minutos em matriz'


#Verificando consistência das séries de cota
for iP, P in enumerate(Lfluvs):
    COD = P.codigo
    afal.write('\n\n     %s (%i) COTA 15 minutos:' % (P.nome, COD))
    print '     - Verificando cota em %s (%i):'  % (P.nome, COD)

    #Contabilizando resultado do CQD do banco e dados ausentes
    cont = [0 for i in range(6)]  #contanilza as notas...
    for dt in datas:
        nota = flu15M[dt][COD][1] #obtem a nota inicial
        if nota == None:
            cont[5] += 1
        else:
            cont[nota] += 1
            if nota == 4:         #nota 4: dados nao verificados
                flu15M[dt][COD][1] = 0    #Dados não-verificados agora são dados consistentes! Mas podem ser reprovados...

    for i in range(5):
        afal.write('\n- Dados c/ nota %i: %12i (%6.2f%%)' % (i, cont[i], (cont[i]*100.0/float(ndad))))
    afal.write('\n- Dados ausentes:  %12i (%6.2f%%)' % (cont[5], (cont[5]*100.0/float(ndad))))
    aux = cont[0] + cont[4]
    print '          > Dados disponíveis (pré-aval) = %i dados, %6.2f%% da série.' % (aux, (aux*100.0/float(ndad)))


    #TESTE 5: Valores máximos e mínimos para registros únicos (15 minutos)
    """ O registro de cota precisa estar entre 0,6*Hmin e 1,4*Hmax, sendo Hmin o menor registro histórico e Hmax o maior."""
    cont, HMAX, HMIN = 0, P.Hmax*1.4, P.Hmin*0.6
    for dt in datas:
        valor, nota = flu15M[dt][COD][0], flu15M[dt][COD][1]
        if valor != None:    # Não aplicável a dados ausentes
            if HMIN <= valor <= HMAX:
                if 1 <= nota <= 3:
                    flu15M[dt][COD][1] -= 1    # Reaprovando dado no teste de limite
            else:
                if nota == 0:
                    flu15M[dt][COD][1] = 9
                    cont += 1
                if cont == 1:
                    afal.write('\n- Dados reprovados no TESTE 5:')
                if cont != 0:
                    afal.write('\n    > %s %12.3f %i' % (dt.strftime('%Y %m %d %H %M'), flu15M[dt][COD][0], flu15M[dt][COD][1]))
    if cont > 0:
        afal.write('\n    > Total de dados reprovados pelo programa:  %12i (%6.2f%%)' % (cont, (cont*100.0/float(ndad))))

    print '          > Processou TESTE 5',
    stdout.flush()


    #TESTE 6: Spikes pontuais
    cont, DHlimite = 0, P.DH15
    for i in range(1,ndad-1):
        notas = [flu15M[datas[j]][COD][1] for j in range(i-1,i+2)]
        if notas.count(0) != 3:
            continue    # Não se aplica se qualquer um dos três registros for inconsistente ou ausente
        
        valores = [flu15M[datas[j]][COD][0] for j in range(i-1,i+2)]
        DHantes = valores[1] - valores[0]
        if abs(DHantes) > DHlimite:
            DHdepois = valores[2] - valores[1]
            if abs(DHdepois) > DHlimite:
                if DHdepois * DHantes < 0:    # Um DH deve ser positivo e o outro negativo
                    cont += 1
                    dt = datas[i]
                    flu15M[dt][COD][1] = 9    # Ao reprovar o dado aqui invalido a aplicação do teste no próximo registro
                    if cont == 1:
                        afal.write('\n- Dados reprovados no TESTE 6:')
                    afal.write('\n    > %s %12.3f %i' % (dt.strftime('%Y %m %d %H %M'), flu15M[dt][COD][0], flu15M[dt][COD][1]))
                        
    if cont > 0:
        afal.write('\n    > Total de dados reprovados pelo programa:  %12i (%6.2f%%)' % (cont, (cont*100.0/float(ndad))))

    print ', 6',
    stdout.flush()


    #TESTE 7: Vizinhos incômodos
    """ Uma das propriedas das séries de cota, monitoradas nos posto fluviométricos, é de ser contínua, ou seja, registros adjacentes (no tempo) apresentam alta correlação entre 
si. Deste modo, dados consistentes que estejam circundados por dados inconsistentes perdem sua "identidade". Não é possivel afirmar com certeza que o dado 'i' é consistente quando 
'i-1' e 'i+1' não são. Por este motivo, registros nestas situações também serão reprovados. """
    cont = 0
    for i in range(1,ndad-1):
        notas = [flu15M[datas[j]][COD][1] for j in range(i-1,i+2)]
        if notas[0] != 0 and notas[1] == 0 and notas[2] != 0:
            cont += 1
            dt = datas[i]
            flu15M[dt][COD][1] = 9
            if cont == 1:
                afal.write('\n- Dados reprovados no TESTE 7:')
            afal.write('\n    > %s %12.3f %i' % (dt.strftime('%Y %m %d %H %M'), flu15M[dt][COD][0], flu15M[dt][COD][1]))

    if cont > 0:
        afal.write('\n    > Total de dados reprovados pelo programa:  %12i (%6.2f%%)' % (cont, (cont*100.0/float(ndad))))

    print ', 7'
    stdout.flush()


    #Recomputando presença de dados inconsistentes
    cont = [0 for i in range(6)]
    for dt in datas:
        if flu15M[dt][COD][1] == None:
            cont[5] += 1
        elif flu15M[dt][COD][1] == 9:
            cont[4] += 1
        else:
            cont[flu15M[dt][COD][1]] += 1
    for i in range(6):
        if i <= 3:
            afal.write('\n- Dados c/ nota %i: %12i (%6.2f%%)' % (i, cont[i], (cont[i]*100.0/float(ndad))))
        elif i == 4:
            afal.write('\n- Dados c/ nota 9: %12i (%6.2f%%)' % (cont[4], (cont[4]*100.0/float(ndad))))
            if cont[4] > 0:
                aux = str('cota1 %8i' % P.codigo)
                if aux not in CQinfo: CQinfo.append(aux)
        else:
            afal.write('\n- Dados ausentes:  %12i (%6.2f%%)' % (cont[5], (cont[5]*100.0/float(ndad))))

    print '          > Dados disponíveis = %i dados, %6.2f%% da série.' % (cont[0], (cont[0]*100.0/float(ndad)))


    #PREENCHIMENTO DE FALHAS
    if cont[0] < 2:
        aux = str('cota2 %8i' % P.codigo)
        if aux not in CQinfo: CQinfo.append(aux)
        print '          > Não há dados disponíveis suficientes para preenchimento.'

    else:
        """ Algoritmo de preenchimento de falhas.
    Supondo que um período de falhas se encontre entre os dados 'i' e 'i+t', e que os dados nas posições 'i-1' e 'i+t+1' são dados consistentes,
construo uma função linear, y = Ax + B (x = tempo, y = cota), entre os dados consistentes para substituir os dados do período de falhas. Para localizar
sequências de falhas na série executa-se o seguinte procedimento:
    (1) Criar uma lista vazia, XY;
    (2) Percorrer cronologicamente a série de dados, de i = 0 até i = ndad-1. A cada incremento de 'i', apendar datahora e valor do registro na lista XY;
    (3) Se o dado 'i' é consistente e XY contém apenas dois elementos ('i' e 'i-1'), então não há falhas no interior de XY. Reinicia XY contendo apenas
        o dado 'i';
    (4) Se o dado 'i' é falha não faz nada (ele já foi apendado no item (2));
    (5) Se o dado 'i' é consistente e XY contém 3 ou mais elementos (já considerando que o dado 'i' foi apendado em XY) então aplica-se a interpolação
        linear para re-estimar o valor de cota nos registros 1 a N-2 da lista XY. Estes valores devem ser subtituidos no dicionário principal de dados
        de cota e a nota deles deve ser trocada para 8, para indicar que eles são dados estimados.
    Feito isto a lista XY é reinicializada contendo apenas o registro consistente em 'i'. """
        XY, Nsub = [], 0
        for i in range(ndad):
            valor, nota = flu15M[datas[i]][COD][0], flu15M[datas[i]][COD][1]
            XY.append( [i, valor, nota] )

            if nota == 0:
                if XY[0][-1] != 0:    #Se a série de dados inicia com um registro inconsistente, nada é feito.
                    pass
                else:
                    Nitp = len(XY)
                    if 2 < Nitp < 2+P.NDAC:    # Quantidade de dados a serem subtituidos não deve superar o nº de auto-correlação
                        XY = interpola_linear(XY)
                        for j in range(1,Nitp-1):
                            dt, valor = datas[XY[j][0]], XY[j][1]
                            flu15M[dt][COD][0] = round(valor,2)
                            flu15M[dt][COD][1] = 8    # Código para dado substituido/preenchido
                            Nsub += 1
                XY = [ [i, valor, nota] ]

        if Nsub > 0:
            afal.write('\n- Dados preenchidos:  %12i (%6.2f%%)' % (Nsub, (Nsub*100.0/float(ndad))))
            print '          > Dados preenchidos = %i dados, %6.2f%% da série.' % (Nsub, (Nsub*100.0/float(ndad)))


#Vazão nos postos fluviométricos
""" A vazão é calculada por curvas de descarga na maioria dos postos fluviométricos. Entretanto, em Santa Cruz do Timbó e União da Vitória o cálculo da vazão considera o efeito de 
remanso, sendo necessário prover além do registro de cota no próprio posto o registro no posto imediatamente a jusante. """
afal.write('\n\n     COMPATIBILIDADE DA VAZÃO:\n')
for iP, P in enumerate(Lfluvs):

    COD = P.codigo
    if COD in [26105047, 26105114]:    # Não estima a vazão para Foz do Timbó e Porto Vitória
        pass
    else:
        cdesc = curva_descarga(COD)    # Curva de descarga do posto fluviométrico
    ncompat = 0                    # Contador de dados onde vazão do banco e vazão calculada diferem em mais de 5%
    arqM = open(str('CotaVazao_15M/cot15M_%8i.txt' % P.codigo),'w')    # Arquivo de série de 15 minutos


    #Recalculando séries de vazão e computando 'compatibilidade' com o banco
    if COD == 26125049:    # Santa Cruz do Timbó
        for dt in datas:
            Hsct, notasct, Qbanco = flu15M[dt][COD]
            Hft, notaft = flu15M[dt][26105047][0], flu15M[dt][26105047][1]    # Foz do Timbó
            if notasct in [0,8] and notaft in [0,8]:
                Qcalc = cdesc.vazao([Hft,Hsct],dt)
                if notasct == 8 or notaft == 8:    # Registro de nível foi alterado, portanto a vazão também deve ser alterada.
                    Qbanco, flu15M[dt][COD][2] = Qcalc, Qcalc
            else:
                Qcalc = None

            if Qbanco != None:
                if Qcalc != None:
                    if abs(Qcalc-Qbanco)/Qbanco > 0.02:    # Vazões compatíveis se diferença menor que 2%
                        afal.write('- %s (%i), %s: Qbanco = %.3f, Qcalc = %.3f\n' % (P.nome, COD, dt, Qbanco, Qcalc))
                        ncompat += 1
                else:
                    """ Há um valor de vazão no banco, mas a vazão calculada não é consistente. Neste caso reprovo a vazão do banco."""
                    flu15M[dt][COD][2] = None
            else:
                flu15M[dt][COD][2] = Qcalc

            aux = (dt.strftime('%Y %m %d %H %M'), N2F(flu15M[dt][26105047][0], -999.999), N2F(flu15M[dt][26105047][1], 9),
                   N2F(flu15M[dt][COD][0], -999.999), N2F(flu15M[dt][COD][1], 9), N2F(flu15M[dt][COD][2], -99999.9))
            arqM.write('%s %8.3f %1i %8.3f %1i %8.1f\n' % aux)
            

    elif COD == 26145104:    # União Da Vitória
        for dt in datas:
            Huva, notauva, Qbanco = flu15M[dt][COD]
            Hpv, notapv = flu15M[dt][26105114][0], flu15M[dt][26105114][1]    # Porto Vitória
            if notauva in [0,8] and notapv in [0,8]:
                Qcalc = cdesc.vazao([Hpv,Huva],dt)
                if notauva == 8 or notapv == 8:    # Registro de nível foi alterado, portanto a vazão também deve ser alterada.
                    Qbanco, flu15M[dt][COD][2] = Qcalc, Qcalc
            else:
                Qcalc = None

            if Qbanco != None:
                if Qcalc != None:
                    if abs(Qcalc-Qbanco)/Qbanco > 0.02:    # Vazões compatíveis se diferença menor que 2%
                        afal.write('- %s (%i), %s: Qbanco = %.3f, Qcalc = %.3f\n' % (P.nome, COD, dt, Qbanco, Qcalc))
                        ncompat += 1
                else:
                    """ Há um valor de vazão no banco, mas a vazão calculada não é consistente. Neste caso reprovo a vazão do banco."""
                    flu15M[dt][COD][2] = None
            else:
                flu15M[dt][COD][2] = Qcalc

            aux = (dt.strftime('%Y %m %d %H %M'), N2F(flu15M[dt][26105114][0], -999.999), N2F(flu15M[dt][26105114][1], 9),
                   N2F(flu15M[dt][COD][0], -999.999), N2F(flu15M[dt][COD][1], 9), N2F(flu15M[dt][COD][2], -99999.9))
            arqM.write('%s %8.3f %1i %8.3f %1i %8.1f\n' % aux)

    else:    # Demais postos
        if COD in [26105047, 26105114]:    #Foz do Timbó e Porto Vitória
            for dt in datas:
                aux = (dt.strftime('%Y %m %d %H %M'), N2F(flu15M[dt][COD][0], -999.999), N2F(flu15M[dt][COD][1], 9))
                arqM.write('%s %8.3f %1i -99999.9\n' % aux)
        else:
            for dt in datas:
                H, nota, Qbanco = flu15M[dt][COD]
                if nota in [0,8]:
                    Qcalc = cdesc.vazao(H,dt)
                    if nota == 8:    # Registro de nível foi alterado, portanto a vazão também deve ser alterada.
                        Qbanco, flu15M[dt][COD][2] = Qcalc, Qcalc
                else:
                    Qcalc = None

                if Qbanco != None:
                    if Qcalc != None:
                        if abs(Qcalc-Qbanco)/Qbanco > 0.02:    # Vazões compatíveis se diferença menor que 2%
                            afal.write('- %s (%i), %s: Qbanco = %.3f, Qcalc = %.3f\n' % (P.nome, COD, dt, Qbanco, Qcalc))
                            ncompat += 1
                    else:
                        """ Há um valor de vazão no banco, mas a vazão calculada não é consistente. Neste caso reprovo a vazão do banco."""
                        flu15M[dt][COD][2] = None
                else:
                    flu15M[dt][COD][2] = Qcalc

                aux = (dt.strftime('%Y %m %d %H %M'), N2F(flu15M[dt][COD][0], -999.999), N2F(flu15M[dt][COD][1], 9),
                    N2F(flu15M[dt][COD][2], -99999.9))
                arqM.write('%s %8.3f %1i %8.1f\n' % aux)


    # Status da compatibilidade
    if ncompat == 0:
        print '     - %s (%i): Vazões compatíveis.'  % (P.nome, COD)
    else:
        print '     - %s (%i): Incompatibilidade em %i registros.' % (P.nome, COD, ncompat)
        aux = str('vazao %8i' % P.codigo)
        if aux not in CQinfo: CQinfo.append(aux)


    # Gravando série horária de vazão
    if COD in [26105047, 26105114]: continue
    arqH = open(str('Vazao_01H/vaz01H_%8i.txt' % P.codigo),'w')        # Arquivo de série horária
    acm, n = 0.0, 0
    for dt in datas:
        if flu15M[dt][COD][2] != None:
            acm += flu15M[dt][COD][2]
            n   += 1
        if dt.minute == 0:
            if n == 0:
                valor = -99999.9
            else:
                valor = acm / n
            arqH.write('%s %8.1f\n' % (dt.strftime('%Y %m %d %H'), valor))
            acm, n = 0.0, 0

    arqM.close()
    arqH.close()
    print '          > Regravou arquivos com séries de cota e vazão.'

# Removendo dados de cota e vazão da memória
del cotvaz, Lfluvs
afal.close()
#=======================================================================================================================================










# PARTE 3: Reportando ocorrência de inconsistências nas séries de dados
#---------------------------------------------------------------------------------------------------------------------------------------
if len(CQinfo) == 0:    # Se não houver casos que precisam ser reportados encerra o programa
    print ''
exit()


""" Ao longo deste programa as séries de chuva e cota foram submetidas a testes para verificação de sua consistência. Os registros que este programa detectou como falha receberam 
nota 9. Entretanto isto só ocorre quando a nota do registro (que vem do banco) é 0, ou seja, foi aprovado. Nestes casos é importante receber uma notificação para avaliar o 
ocorrido. Isto pode ajudar na identificação de problemas com as estações ou com o CQD automático do banco, ou ainda mesmo com os testes implementadas neste programa. Também foi 
avaliada a compatibilidade entre a vazão calculada pelas curvas de descarga e a vazão presente no banco de dados. Os casos em que esses valores diferem em mais de 2% também serão 
reportados pois indicam alguma mudança no método de estimativa da vazão.
    Para informar os casos de divergência no CQD do banco ou no cálculo da vazão foi criada a lista CQinfo onde foram apendadas strings com as informações da variáveis e dos postos 
onde houve problemas. Estas string serão repassadas por e-mail utilizando o programa sendEmail (/simepar/hidro/sendEmail). Além disso o arquivo de registro de falhas será renomeado 
com a inserção da data de referência da rodada para garantir que ele não seja sobrescrito. """

print '\n----- ENVIO DE RELATORIO DO CQD -----'
# Criando cópia do arquivo com o log do CQD e dos arquivos de dados brutos
system(str('cp controle_qualidade.txt cqd_%s.txt' % dtref.strftime('%Y%m%d%H')))
system(str('rar a dados_%s.rar chuva_15M.txt cotavazao_15M.txt' % dtref.strftime('%Y%m%d%H')))

# Criando comando do sendEmail e enviando relatorio
#comando = '/simepar/hidro/sendEmail -f "CQD SISPSHI2 <hidro@simepar.br>" -t "Angelo <angelo@simepar.br>, mino.sorribas@simepar.br" -o message-charset=utf-8'
comando = '/simepar/hidro/sendEmail -f "CQD SISPSHI2 <hidro@simepar.br>" -t "Jose Eduardo <jose.eduardo@simepar.br>" -o message-charset=utf-8'
comando += str(' -u "Dados inconsistentes em %s"' % dtref)    # Assunto do e-mail
comando += ' -m "Relação de variáveis e estações onde foram encontradas inconsistências:'
for l in CQinfo:
    comando += str('\n%s' % l)
comando +='" -s mail'
system(comando)
print '----- ENVIO DE RELATORIO DO CQD -----\n'
#=======================================================================================================================================


print ''

