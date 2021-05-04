from datetime import datetime, timedelta
import pandas as pd
import sys
import HydroErr as he

#Numero da bacia e leitura das forçantes
bn = 3
bnome = 'Sao_Bento'
arq = open(f'./PEQ_hr/{bn:02d}_{bnome}_peq_hr.csv')
areainc = float(arq.readline())
df = pd.read_csv(f'./PEQ_hr/{bn:02d}_{bnome}_peq_hr.csv', skiprows=[0],
                 index_col = 'datahora', parse_dates = True)

#df = df.loc['2014']
cmb = df['pme']
etp = df['etp']
qmont = df['qmon']
qobs = df['qjus']
Q0 = qobs[0]

def Fracionamento(datas, Qobs, Qalta, Qmedia, Qbaixa):

    # Amplitudes
    AQbax = Qbaixa2 - Qmin
    AQmed = Qalta2 - Qbaixa2
    AQalt = Qalta2 + AQbax

    ND = len(datas)    # Quantidade de dados no período de simulação

    # Computando nova série de vazão modelada
    Qmod = {}
    for i in range(ND):
        dt = datas[i]

        # Vazão consistente mais próxima, se a atual não for consistente
        if Qobs[dt] == None:

            # Vazão consistente anterior (sempre está uma hora atrás, pois se ela era None já está preenchida)
            if i == 0:
                Q1 = None
            else:
                j1 = i-1
                Q1 = Qobs[datas[j1]]

            # Vazão consistente posterior (agora sim busca um valor consistente até chegar ao fim da série) ...
            if i == ND-1:    #... a menos que seja o último!
                Q2 = None
            else:
                for j2 in range(i+1,ND):
                    if Qobs[datas[j2]] != None: break
                Q2 = Qobs[datas[j2]]

            # Sem dados!
            if Q1 == None and Q2 == None:
                erro = str('\n     Não há dado de vazão observada em %s, entre %s e %s,' % (nome, datas[0], datas[-1]))
                erro += 'para aplicar método de fracionamento do hidrograma.\n'
                raise ValueError(erro)

            # Reconstituindo ...
            if Q1 == None:
                Qobs[dt] = Q2
            elif Q2 == None:
                Qobs[dt] = Q1
            else:
                Qobs[dt] = (Q2-Q1)*(i-j1)/(j2-j1) + Q1

        # Seguindo com o método do fracionamento
        if Qobs[dt] <= Qbaixa2:    # Faixa de vazões baixas
            peso_media = ( ((Qobs[dt]-Qmin)/AQbax)**2 ) * 0.5
            peso_baixa = 1.0 - peso_media
            peso_alta  = 0.0

        elif Qobs[dt] > Qbaixa2 and Qobs[dt] <= Qalta2:    # Faixa de vazões médias
            peso_alta  = ( ((Qobs[dt]-Qbaixa2)/(AQmed))**2.5 ) * 0.5
            peso_baixa = ( ((Qalta2-Qobs[dt])/(AQmed))**2.5 ) * 0.5
            peso_media = 1.0 - (peso_alta + peso_baixa)

        elif Qobs[dt] > Qalta2 and Qobs[dt] <= AQalt:    # Faixa de vazões média-altas
            peso_media = ( ((AQalt-Qobs[dt])/AQbax)**2 ) * 0.5
            peso_alta  = 1.0 - peso_media
            peso_baixa = 0.0

        else:    # (Qobs > AQalt) Vazões muito altas
            peso_alta, peso_media, peso_baixa = 1.0, 0.0, 0.0

        # Vazão modelada
        Qmod[dt] = peso_alta*Qalta[dt] + peso_media*Qmedia[dt] + peso_baixa*Qbaixa[dt]

    return Qmod

def ExecutaSACSIMPLES(param, datas, evap, cmb, qmont, area, condinic, retorna_estados=False):
    param[10] = int(param[10])    # NRC deve ser um inteiro daqui pra frente

    # Condição inicial do solo da bacia
    Rsolo = [condinic[0], condinic[1]]
    if Rsolo[0] > param[0] or Rsolo[0] < 0:
        erro = '\n     Volume de água na camada superior é inconsistente!'
        erro += str('\n     Condição inicial = %f mm; Máximo comportado = %f mm.\n' % (Rsolo[0], param[0]))
        raise ValueError(erro)
    if Rsolo[1] > param[1] or Rsolo[1] < 0:
        erro = '\n     Volume de água na camada inferior é inconsistente!'
        erro += str('\n     Condição inicial = %f mm; Máximo comportado = %f mm.\n' % (Rsolo[1], param[1]))
        raise ValueError(erro)

    # Condição inicial dos reservatórios de propagação
    Rprop = condinic[2:]
    if len(Rprop) != param[10]:
        erro = '\n     Número de reservatórios na condição inicial é diferente do parâmetro do modelo.'
        erro += str('\n     Valores na C.I. = %i;    NRC = %i.\n' % (len(Rprop), param[10]))
        raise ValueError(erro)
    for i in range(param[10]):
        if Rprop[i] < 0:
            erro = str('\n     Cond. inicial do reservatório %i de propação é nula!\n' % (i+1))
            raise ValueError(erro)

    # Inicializando dicionários de dados simulados
    Qmod, Stados = {}, {}

    # Ciclo temporal da simulação
    for dt in datas:
        Rsolo, VolBac = SAC_Simples(param,Rsolo,evap[dt],cmb[dt])
        VolBac  = VolBac * area * 1000    #Convertendo volume da bacia de mm para m³
        try:
            VolMont = max(qmont[dt] * 3600, 0.0) #Volume proveniente de montante em 1 hora.
        except TypeError:
            print('\n\n    Vazao de montante é None.\n', dt, '\n')
            raise
        Rprop, VolMod = CRCL(param, Rprop, VolBac, VolMont)

        # Estados do modelo ao final do passo de integração
        Stados[dt] = [Rsolo[0], Rsolo[1]].extend(Rprop)    # Não fazer Rsolo.extend(Rprop). Pode vincular Stados a Rsolo.

        # Vazão modelada, m³/s
        Qmod[dt] = VolMod / 3600.0

    # Retornando dados modelados
    if retorna_estados:
        return Qmod, Stados
    else:
        del Stados
        return Qmod

def SAC_Simples(Param,Ssolo,PET,PREC):

    #Calculando a perda por evapotranspiração, na zona superior, no intervalo
    E1 = PET * (Ssolo[0]/Param[0])    #E1  = Evapotranspiração ocorrida na zona superior (mm)

    #Descontando a evapotranspiração da zona superior do solo, porém não pode ser perdida mais água
    #do que há nesta camada.
    if E1 > Ssolo[0]:
        E1 = Ssolo[0]
        Ssolo[0] = 0.0
    else:
        Ssolo[0] = Ssolo[0] - E1
    RED = PET - E1    #RED = Resíduo da evapotranspiração para ser descontada na camada inferior do solo

    #Calculando a perda por evapotranspiração, na zona inferior, no intervalo
    # E2  = Evapotranspiração ocorrida na zona inferior (mm)
    E2 = RED * ((Ssolo[1]/Param[1]) ** Param[7])

    #Descontando a evapotranspiração da zona inferior do solo, porém não pode ser perdida mais água
    #do que há nesta camada.
    if E2 > Ssolo[1]:
        E2 = Ssolo[1]
        Ssolo[1] = 0.0
    else:
        Ssolo[1] = Ssolo[1] - E2

    #Calculando os escoamentos de percolação e superficial.
    # TWX   = Umidade em excesso na zona superior, no intervalo (mm)
    # ROIMP = Escoamento superficial da área impermeável
    try:
        ROIMP = PREC * ((Ssolo[0]/Param[0]) ** Param[5])
        PREC = PREC - ROIMP
    except TypeError:
        print('PREC recebeu valor None!')
        ROIMP, PREC = 0.0, 0.0

    if (PREC + Ssolo[0]) > Param[0]:
        TWX = PREC + Ssolo[0] - Param[0]
        Ssolo[0] = Param[0]
    else:
        TWX = 0.0
        Ssolo[0] = Ssolo[0] + PREC

    #Inicializando acumuladores do intervalo DT
    SBF   = 0.0                #Escoamento de base
    SSUR  = 0.0                #Escoamento superficial
    SIF   = 0.0                #Escoamento interno (subsuperficial)
    SPERC = 0.0                #Percolação

    #Determinando os incrementos computacionais de tempo para o intervalo básico de tempo.
    #Nenhum incremento irá exceder 5.0 milimetros de Ssolo[0]+TWX.
    # NINC = Número de incrementos de tempo em que o intervalo de tempo será dividido para posterior
    #        contabilidade da umidade do solo.
    # DINC = Comprimento de cada incremento em dias
    # PINC = Quantidade de umidade disponível para cada incremento
    NINC = int( round(1.0 + 0.20*(Ssolo[0]+TWX), 0) )
    DINC = (1.0/NINC) / 24.0    # "/ 24" = "* (1/24)". "1/24" é o DT [dias], ou seja, dados horários.
    PINC = TWX/NINC

    #Calculando frações de deplecionamento da água para o tempo de incremento, sendo que as taxas de
    #depleção são para um dia.
    # DUZ  = Depleção de água da zona superior, por incremento
    # DLZ  = Depleção de água da zona inferior, por incremento
    DUZ  = 1.0 - ( (1.0-Param[2])**DINC )
    DLZ  = 1.0 - ( (1.0-Param[3])**DINC )


    # INICIANDO CICLO DE INTEGRAÇÃO PARA CADA INCREMENTO, PARA O INTERVALO DE TEMPO
    for I in range(NINC):

        #Calculando o escoamento de base da zona inferior e o acumulado do intervalo de tempo
        # BF = Escoamento de base
        BF   = Ssolo[1] * DLZ
        SBF  = SBF + BF
        Ssolo[1] = Ssolo[1] - BF

        #Calculando o volume percolado
        # UZRAT = Umidade da camada superior do solo
        # LZRAT = Umidade da camada inferior do solo
        # PERC = Volume percolado no incremento de tempo
        UZRAT = Ssolo[0] / Param[0]
        LZRAT = Ssolo[1] / Param[1]
        PERC  = DLZ * Param[1] * (1.0 + Param[4] * ((1.0-LZRAT)**Param[6])) * UZRAT

        #Verificando se o volume percolado está realmente disponível na camada superior
        if PERC > Ssolo[0]:
            PERC = Ssolo[0]

        #Verificando se a camada inferior comporta o volume percolado
        if (PERC+Ssolo[1]) > Param[1]:
            PERC = Param[1] - Ssolo[1]

        #Transferindo água percolada
        Ssolo[0] = Ssolo[0] - PERC
        Ssolo[1] = Ssolo[1] + PERC
        SPERC = SPERC + PERC

        #Calculando o escoamento interno e o acumulado
        # DEL = Escoamento interno
        #OBS: A quantidade PINC ainda não foi adicionada
        DEL  = Ssolo[0] * DUZ
        SIF  = SIF + DEL
        Ssolo[0] = Ssolo[0] - DEL

        #Distribuir PINC entre a zona superior e o escoamento superficial
        SUR = 0.0
        if PINC > 0.0:
            #Se houver excesso, vira escoamento superficial
            if (PINC+Ssolo[0]) > Param[0]:
                SUR = PINC + Ssolo[0] - Param[0]
                Ssolo[0] = Param[0]
            #Do contrário, adiciona tudo na camada superior
            else:
                Ssolo[0] = Ssolo[0] + PINC
            SSUR = SSUR + SUR

    # FIM DO CICLO DE INTEGRAÇÃO PARA CADA INCREMENTO, PARA O INTERVALO DE TEMPO

    #Descontando volume do escoamento de base que vai para o aquífero
    # BFCC = componente do escoamento de base que vai para o canal
    BFCC = SBF * Param[8]

    #Calculando escoamento afluente da bacia para o canal no intervalo de tempo
    # TCI  = Escoamento afluente total
    # GRND = Escoamento subterrâneo
    # SURF = Escoamento superficial
    TCI = ROIMP + SSUR + SIF + BFCC

    return Ssolo, TCI

# Propagação por Cascata de Reservatórios
def CRCL(Param,Sprop,VOLbac,VOLmont):
    Vprop = [[0.0, 0.0, 0.0] for i in range(Param[10])]

    #Calculando fluxos no início do passo de tempo e adicionando volumes de entrada
    for i in range(Param[10]):
        Vprop[i][0] = Param[9] * Sprop[i]
        Sprop[i] += VOLbac/Param[10]    #Volume produzido pela bacia incremental
    Sprop[0] += VOLmont    #Volume contribuinte de montante

    #Balanço de massa no primeiro reservatório
    Vprop[0][1] = Param[9] * Sprop[0]
    Vprop[0][2] = 0.50 * (Vprop[0][0] + Vprop[0][1])
    Sprop[0]   -= Vprop[0][2]

    #Propagando água entre reservatórios
    for i in range(1,Param[10]):
        Sprop[i]   += Vprop[i-1][2]
        Vprop[i][1] = Param[9] * Sprop[i]
        Vprop[i][2] = 0.50 * (Vprop[i][0] + Vprop[i][1])
        Sprop[i]   -= Vprop[i][2]

    return Sprop, Vprop[Param[10]-1][2]

bdsimuls = {
    1:[116,{'BACIA':1, 'MODELO':'SACFRACAO', 'PARAM':'5,6,7', 'CMBOBS':'MEDIA', 'CMBPREV':'ENSWRFMED', 'QMONTPREV':'0'}],
    2:[216,{'BACIA':2, 'MODELO':'SACFRACAO', 'PARAM':'5,6,7', 'CMBOBS':'MEDIA', 'CMBPREV':'ENSWRFMED', 'QMONTPREV':'0'}],
    3:[316,{'BACIA':3, 'MODELO':'SACFRACAO', 'PARAM':'5,6,7', 'CMBOBS':'PC_D2', 'CMBPREV':'ENSWRFMED', 'QMONTPREV':'0'}],
    4:[416,{'BACIA':4, 'MODELO':'SACSIMPLES', 'PARAM':'5,6,7', 'CMBOBS':'PM_D2', 'CMBPREV':'ENSWRFMED', 'QMONTPREV':'0'}],
    5:[516,{'BACIA':5, 'MODELO':'SACFRACAO', 'PARAM':'5,6,7', 'CMBOBS':'PM_D2', 'CMBPREV':'ENSWRFMED', 'QMONTPREV':'0'}],
    6:[616,{'BACIA':6, 'MODELO':'SACFRACAO', 'PARAM':'5,6,7', 'CMBOBS':'PM_D2', 'CMBPREV':'ENSWRFMED', 'QMONTPREV':'216'}],
    7:[716,{'BACIA':7, 'MODELO':'SACFRACAO', 'PARAM':'1,2,3', 'CMBOBS':'PM_D2', 'CMBPREV':'ENSWRFMED', 'QMONTPREV':'116,316'}],
    8:[816,{'BACIA':8, 'MODELO':'SACSIMPLES', 'PARAM':'5,6,7', 'CMBOBS':'PM_D2', 'CMBPREV':'ENSWRFMED', 'QMONTPREV':'416,616,716'}],
    9:[916,{'BACIA':9, 'MODELO':'SACSIMPLES', 'PARAM':'5,6,7', 'CMBOBS':'PC_D4', 'CMBPREV':'ENSWRFMED', 'QMONTPREV':'516,816'}],
    10:[1015,{'BACIA':10, 'MODELO':'SACSIMPLES', 'PARAM':'5,6,7', 'CMBOBS':'PC_D2', 'CMBPREV':'ENSWRFMED', 'QMONTPREV':'0'}],
    11:[1115,{'BACIA':11, 'MODELO':'SACSIMPLES', 'PARAM':'5,6,7', 'CMBOBS':'PC_D2', 'CMBPREV':'ENSWRFMED', 'QMONTPREV':'0'}],
    13:[1315,{'BACIA':13, 'MODELO':'SACSIMPLES', 'PARAM':'5,6,7', 'CMBOBS':'MEDIA', 'CMBPREV':'ENSWRFMED', 'QMONTPREV':'0'}],
    14:[1415,{'BACIA':14, 'MODELO':'SACSIMPLES', 'PARAM':'5,6,7', 'CMBOBS':'PC_D4', 'CMBPREV':'ENSWRFMED', 'QMONTPREV':'0'}],
    15:[1515,{'BACIA':15, 'MODELO':'SACFRACAO', 'PARAM':'5,6,7', 'CMBOBS':'THSEN', 'CMBPREV':'ENSWRFMED', 'QMONTPREV':'0'}],
    21:[2112,{'BACIA':21, 'MODELO':'SACFRACAO', 'PARAM':'1,2,3', 'CMBOBS':'MEDIA', 'CMBPREV':'0', 'QMONTPREV':'2010'}]
    }
cmbobs = bdsimuls[bn][1]['CMBOBS']
params_3 = bdsimuls[bn][1]['PARAM'].split(',')
par1 = int(params_3[0])
par2 =int(params_3[1])
par3 = int(params_3[2])

# Ordem obrigatória dos parâmetros:
# param[0] =  UZWM: capacidade máxima de armazenamento da camada superior do solo (mm);
# param[1] =  LZWM: capacidade máxima de armazenamento da camada inferior do solo (mm);
# param[2] =   UZK: taxa de transferência lateral da camada superior do solo (%/dia);
# param[3] =   LZK: taxa de transferência lateral da camada inferior do solo (%/dia);
# param[4] = ZPERC: coeficiente da equação de percolação (adim.);
# param[5] =  IMPX: expoente da equação de escoamento direto proveniente da área impermeável (adim.);
# param[6] =  REXP: expoente da equação de percolação (adim.);
# param[7] =  TRNX: expoente da equação para cálculo da transpiração (adim.)
# param[8] =  SIDE: fração do escoamento subterrâneo que chega ao canal (%);
# param[9] =  beta: fração do volume do reservatório de canal que escoa por passo de tempo (%);
# param[10]=   NRC: número de reservatórios conceituais (inteiro).

PARAM1 = {
           1:
             {'MEDIA':
                      { 1: [ 206.540,  189.260, 0.18190, 0.01160, 297.000, 5.99990, 1.00010, 4.22680, 1.00000, 0.03831,  4],
                        2: [ 458.980,  817.550, 0.10000, 0.00280, 794.140, 0.55370, 1.02500, 0.91850, 0.81350, 0.04260, 15],
                        3: [ 423.990,  718.830, 0.10000, 0.00650, 620.500, 5.88330, 1.00070, 1.27730, 0.35840, 0.11435, 15],
                        4: [ 157.210,  204.720, 0.21170, 0.00770, 899.140, 5.99910, 2.67440, 1.04060, 1.00000, 0.02650,  3],
                        5: [ 237.480,  264.290, 0.15020, 0.00460, 893.100, 5.99940, 1.00000, 5.98900, 0.00010, 0.04628,  4],
                        6: [ 348.050,   94.550, 0.10730, 0.03300, 772.090, 1.71650, 4.57060, 0.14750, 0.78960, 0.22610, 15],
                        7: [ 118.740,   39.300, 0.18880, 0.19970, 801.070, 5.81300, 1.00030, 0.91950, 0.11880, 0.21294, 15],
                        8: [ 189.890,  178.510, 0.14480, 0.00790, 899.700, 5.99750, 1.11680, 3.66210, 0.99990, 0.04945,  4],
                        9: [ 100.930,  698.510, 0.26160, 0.00120, 819.900, 2.12060, 4.34020, 0.70760, 1.00000, 0.00730,  1],
                       10: [ 164.040,  197.660, 0.22130, 0.00910, 899.860, 5.98870, 3.06970, 1.07110, 1.00000, 0.03302,  4]
                      }},
           2:
             {'MEDIA':
                      { 1: [  23.192,  199.157, 0.10000, 0.01249, 318.422, 0.61597, 1.00003, 1.90313, 1.00000, 0.07162, 15],
                        2: [  78.016,  120.558, 0.10014, 0.04165, 899.103, 5.98100, 1.00013, 1.56117, 0.64593, 0.09255,  2],
                        3: [  73.708,  252.817, 0.10001, 0.00311, 897.895, 1.57607, 1.00003, 1.28454, 0.99897, 0.04637,  8],
                        4: [  79.720,  393.015, 0.10000, 0.00306, 227.387, 1.47183, 3.41222, 0.92158, 1.00000, 0.01694,  3],
                        5: [  38.905,  165.111, 0.10005, 0.00104, 766.405, 1.44751, 3.18514, 0.10002, 0.02137, 0.02265,  5],
                        6: [  64.648,  106.439, 0.10001, 0.09416,  98.055, 1.14802, 1.96992, 0.18678, 0.51955, 0.01841,  1],
                        7: [ 381.593,  217.773, 0.10000, 0.19999, 238.277, 0.61211, 4.89041, 5.83999, 0.21813, 0.11195,  7],
                        8: [  44.679,   69.266, 0.41314, 0.12194, 102.578, 0.78247, 1.00011, 0.10024, 0.58801, 0.00906,  1],
                        9: [  80.668,  290.233, 0.18295, 0.00541, 150.712, 1.01065, 2.00764, 0.62209, 0.99996, 0.01886,  4],
                       10: [  55.282,  326.658, 0.10000, 0.00543, 190.778, 1.50399, 3.00918, 1.25115, 1.00000, 0.02076,  4]
                      }},
           3:
             {'PC_D2':
                      { 1: [  52.950,  211.400, 0.47720, 0.04730, 316.170, 5.92690, 1.30330, 1.31750, 0.60360, 0.10499, 10],
                        2: [  74.130,  185.540, 0.10000, 0.03100, 899.050, 5.86800, 1.00000, 1.25010, 0.50030, 0.31910, 15],
                        3: [  15.100,  283.580, 0.10050, 0.00430, 898.600, 5.99300, 1.00100, 1.06930, 0.76720, 0.33296, 15],
                        4: [ 141.640,  279.390, 0.10000, 0.00910,  26.250, 2.22880, 1.00040, 0.47250, 0.61610, 0.00985,  2],
                        5: [  35.480,  191.850, 0.69720, 0.06420, 189.460, 5.98300, 2.07480, 0.11700, 0.61980, 0.05004,  5],
                        6: [ 133.620,  113.250, 0.10000, 0.02020,  89.090, 5.51190, 1.00010, 3.69950, 0.00040, 0.01311,  2],
                        7: [ 202.220,  147.400, 0.10000, 0.11700, 503.810, 4.75540, 5.99960, 5.83510, 0.17700, 0.18635, 15],
                        8: [  44.920,  180.030, 0.46800, 0.07120, 268.630, 5.98150, 2.62170, 0.10050, 0.48730, 0.04521,  4],
                        9: [  99.350,  262.260, 0.15950, 0.00670,  63.200, 3.06860, 1.00000, 0.53750, 0.70470, 0.02759,  7],
                       10: [  97.980,  246.660, 0.10000, 0.02660,  21.330, 1.35830, 1.00000, 0.55400, 0.65030, 0.01922,  4]
                      }},
           4:
             {'PM_D2':
                      { 1: [  89.590,  187.110, 0.10000, 0.05370, 899.860, 5.99980, 1.00020, 2.38890, 0.81060, 0.01262,  2],
                        2: [  18.230,  207.180, 0.54010, 0.05130, 890.840, 5.98890, 4.36100, 0.45200, 0.72240, 0.20249, 15],
                        3: [  12.360,  247.810, 0.10150, 0.00410, 899.770, 5.99980, 1.00010, 0.57070, 0.76490, 0.31976, 15],
                        4: [   6.400,  224.350, 0.10030, 0.06300, 898.970, 5.99970, 1.06080, 0.27820, 0.88960, 0.01266,  1],
                        5: [   4.290,  253.770, 0.15060, 0.10370, 617.400, 2.65780, 1.84610, 0.10000, 0.72780, 0.01189,  3],
                        6: [   9.500,  219.420, 0.10130, 0.06860, 899.820, 5.96610, 1.00120, 0.16670, 0.79790, 0.07531,  6],
                        7: [  80.430,  100.340, 0.11650, 0.05510, 900.000, 6.00000, 5.99790, 0.43310, 0.30460, 0.16020, 15],
                        8: [   8.770,  208.100, 0.10000, 0.07590, 882.840, 5.68960, 1.05050, 0.10000, 0.83540, 0.01087,  1],
                        9: [   6.790,  235.650, 0.10000, 0.05620, 852.900, 6.00000, 1.00010, 0.32290, 0.79240, 0.02021,  1],
                       10: [   6.060,  206.000, 0.10260, 0.05620, 209.770, 6.00000, 1.00420, 0.41770, 0.91680, 0.01192,  1]
                      }},
           5:
             {'PM_D2':
                      { 1: [ 119.311,  206.077, 0.10440, 0.03852,  21.920, 2.13252, 1.00000, 2.72916, 0.96941, 0.17517,  9],
                        2: [ 271.044,  228.338, 0.10125, 0.01551, 188.765, 1.68151, 1.00014, 0.63953, 0.74834, 0.10041,  5],
                        3: [ 147.475,  312.808, 0.10000, 0.00701, 899.980, 5.99919, 1.00001, 1.08777, 0.33953, 0.16354, 15],
                        4: [ 111.986,  371.065, 0.17676, 0.02851,  24.738, 2.50066, 5.42296, 0.25707, 0.91454, 0.08714,  4],
                        5: [ 129.282,  158.719, 0.19701, 0.17829,  12.287, 3.22150, 2.10726, 3.90002, 0.54356, 0.41208, 15],
                        6: [ 141.658,  166.868, 0.18535, 0.04551,  67.330, 2.88636, 2.64709, 0.30007, 1.00000, 0.24840,  9],
                        7: [  95.858,   64.917, 0.18242, 0.14599, 899.946, 5.07512, 5.99989, 0.70760, 0.16257, 0.40086, 15],
                        8: [ 145.285,  204.530, 0.18990, 0.09123,  31.833, 2.79717, 5.99962, 0.40888, 0.44048, 0.25962, 10],
                        9: [ 122.929,  147.897, 0.17968, 0.05852,  35.120, 1.71728, 1.09641, 0.90364, 0.64002, 0.17724, 10],
                       10: [ 107.988,  186.851, 0.14220, 0.04912,  20.029, 1.70846, 1.02016, 0.99646, 0.76026, 0.09419,  5]
                      }},
           6:
             {'PM_D2':
                      { 1: [  53.443,  172.698, 0.11042, 0.03019, 375.753, 5.99980, 1.00017, 5.99981, 0.24204, 0.08080, 13],
                        2: [ 158.425,  220.789, 0.10000, 0.02808, 402.390, 5.32519, 4.67696, 0.10000, 0.10971, 0.02411,  2],
                        3: [  36.971,  447.841, 0.10011, 0.00356, 899.596, 5.94492, 1.00083, 1.84996, 0.04156, 0.12538,  8],
                        4: [  88.338,  230.987, 0.10000, 0.01410, 744.545, 5.99959, 2.61020, 2.13913, 0.00000, 0.03335,  5],
                        5: [  77.107,  172.436, 0.31099, 0.03503, 899.856, 5.98998, 1.00008, 1.95871, 0.77170, 0.08226, 12],
                        6: [ 470.543,  119.313, 0.10016, 0.15333, 336.886, 1.27141, 1.00005, 0.26221, 0.10062, 0.02072,  2],
                        7: [ 131.500,  117.145, 0.10000, 0.02801, 576.070, 5.43063, 2.51106, 0.10010, 0.00000, 0.03798,  3],
                        8: [  98.674,  118.860, 0.22902, 0.04786, 591.398, 5.97061, 1.00006, 0.10006, 0.37709, 0.04007,  5],
                        9: [ 268.296,  402.633, 0.10005, 0.00691, 899.969, 2.18999, 1.00000, 4.66520, 0.00000, 0.11744, 15],
                       10: [  42.005,  283.608, 0.10000, 0.01068, 568.506, 5.99979, 5.40528, 0.79157, 0.00000, 0.02285,  4]
                      }},
           7:
             {'PM_D2':
                      { 1: [  13.850,  155.547, 0.10006, 0.08980, 898.443, 5.99822, 1.15240, 0.20344, 0.35045, 0.01881,  2],
                        2: [ 105.267,  145.490, 0.10009, 0.02505, 898.681, 5.99004, 1.00051, 0.45220, 0.28367, 0.08347,  3],
                        3: [  13.957,  176.137, 0.10000, 0.00827, 899.957, 5.99703, 1.00002, 1.71418, 0.11845, 0.38074, 14],
                        4: [   7.798,  180.296, 0.10005, 0.05330, 883.963, 5.97523, 1.00055, 0.10000, 0.38096, 0.02562,  2],
                        5: [   8.540,  161.437, 0.10005, 0.11195, 874.671, 5.98111, 1.00119, 0.10000, 0.28215, 0.01781,  2],
                        6: [ 167.034,  316.512, 0.10001, 0.06435, 206.260, 1.34540, 1.00016, 0.33919, 0.18805, 0.05019,  2],
                        7: [  10.158,  541.564, 0.50475, 0.02811, 859.709, 6.00000, 4.98899, 0.10013, 0.24597, 0.20086,  7],
                        8: [   8.900,  151.943, 0.28549, 0.14468, 875.513, 5.94141, 1.02556, 0.10000, 0.22259, 0.02042,  2],
                        9: [   6.722,  183.018, 0.10070, 0.05913, 900.000, 6.00000, 1.00673, 0.17884, 0.29424, 0.01609,  1],
                       10: [  53.100,  147.672, 0.10002, 0.05666, 896.220, 5.98900, 1.00105, 0.10000, 0.39414, 0.02334,  2]
                      }},
           8:
             {'PM_D2':
                      { 1: [   7.076,  204.064, 0.10000, 0.09231, 831.789, 5.99266, 1.02362, 1.73137, 0.12353, 0.01789,  1],
                        2: [  10.890,  202.913, 0.10024, 0.02453, 899.660, 6.00000, 1.00154, 0.69317, 0.16525, 0.44397,  8],
                        3: [  66.398,  290.542, 0.10000, 0.01400, 827.886, 5.38218, 1.01287, 0.66941, 0.08122, 0.04485,  1],
                        4: [   9.364,  255.353, 0.10328, 0.04136, 872.274, 6.00000, 1.00366, 0.39987, 0.16087, 0.02937,  1],
                        5: [  29.967,  229.428, 0.22196, 0.14537,  25.563, 5.99233, 1.00104, 2.43184, 0.06392, 0.01716,  1],
                        6: [  78.909,  681.933, 0.36559, 0.02915, 712.105, 0.13460, 1.64445, 0.65624, 0.17555, 0.18454,  3],
                        7: [  15.908,  686.558, 0.40670, 0.00971, 874.594, 0.10047, 3.44079, 0.41423, 0.31501, 0.10199,  1],
                        8: [  29.361,  176.824, 0.20236, 0.18445,  46.428, 5.17204, 1.00000, 2.26697, 0.05304, 0.02732,  1],
                        9: [   8.016,  166.742, 0.10081, 0.15823, 795.741, 5.96943, 1.01107, 1.67920, 0.09571, 0.01990,  1],
                       10: [  74.046,  298.380, 0.11482, 0.03517, 210.707, 2.48327, 1.09393, 0.45958, 0.16985, 0.03093,  1]
                      }},
           9:
             {'PC_D4':
                      { 1: [  50.922,  272.891, 0.10000, 0.06405,  39.321, 5.99990, 1.00000, 0.10000, 0.11124, 0.03406,  1],
                        2: [  74.506,  321.293, 0.10003, 0.05380, 175.100, 5.45580, 3.64763, 0.27831, 0.05876, 0.06014,  1],
                        3: [ 435.945,  174.072, 0.10000, 0.18994, 344.390, 4.18584, 1.97327, 0.10031, 0.00445, 0.03725,  1],
                        4: [  55.526,  252.813, 0.10017, 0.05702,  84.801, 5.99998, 1.00000, 0.10000, 0.10177, 0.04502,  1],
                        5: [  46.112,  267.013, 0.10000, 0.14784,  16.939, 5.99864, 1.00006, 0.95649, 0.06473, 0.03333,  1],
                        6: [ 148.730,  556.943, 0.10000, 0.04477, 205.104, 4.82530, 2.76671, 0.29663, 0.10624, 0.06895,  1],
                        7: [  79.364,  142.656, 0.10000, 0.04042, 770.481, 5.98754, 1.57705, 0.10002, 0.07295, 0.13302,  2],
                        8: [  45.815,  392.487, 0.10000, 0.06952,  34.778, 5.99954, 1.00002, 0.21201, 0.08980, 0.05048,  1],
                        9: [  40.234,  281.944, 0.10000, 0.06361,  64.235, 5.94335, 1.07833, 0.10001, 0.08680, 0.06085,  1],
                       10: [  98.389,  262.332, 0.10111, 0.05352, 118.992, 4.62048, 1.32796, 0.10001, 0.10563, 0.04147,  1]
                      }},
          10:
             {'PC_D2':
                      { 1: [  51.776,  119.148, 0.43514, 0.04847, 129.144, 2.51354, 1.07313, 2.63203, 0.99988, 0.26605,  8],
                        2: [   6.244,  222.691, 0.74931, 0.03887, 895.848, 5.91824, 1.07820, 1.06580, 0.56680, 0.89655,  5],
                        3: [  20.370,  454.346, 0.10623, 0.00442, 265.413, 5.99010, 1.00062, 2.10829, 0.49325, 0.21664, 15],
                        4: [  68.635,  199.729, 0.21739, 0.01730, 899.809, 2.13929, 5.99905, 0.72538, 0.99999, 0.22584,  8],
                        5: [  58.442,  111.789, 0.29325, 0.05300,  89.329, 2.49639, 3.01826, 1.17727, 0.66605, 0.21012,  7],
                        6: [  65.433,   97.848, 0.26008, 0.04533, 331.581, 2.53266, 3.12226, 0.96887, 0.94925, 0.42684, 15],
                        7: [  44.501,   94.121, 0.21056, 0.13928, 131.058, 5.99104, 5.98780, 0.64503, 0.20394, 0.43629, 15],
                        8: [  61.293,  142.008, 0.26879, 0.04569, 281.948, 2.41435, 5.99703, 0.82544, 0.54601, 0.26066,  9],
                        9: [  84.101,  195.216, 0.19108, 0.01993, 900.000, 2.43033, 5.99999, 0.61391, 1.00000, 0.26309,  7],
                       10: [  68.745,  199.404, 0.23147, 0.02104, 804.890, 2.06731, 5.99895, 0.86406, 1.00000, 0.23114,  8]
                      }},
          11:
             {'PC_D2':
                      { 1: [ 176.810,  164.544, 0.12012, 0.06869,  18.859, 1.33371, 1.00004, 1.14623, 0.54494, 0.20534,  7],
                        2: [ 120.677,  260.693, 0.17480, 0.03031, 132.896, 5.98241, 1.00003, 0.78917, 0.44099, 0.21605,  9],
                        3: [   8.420,  322.746, 0.10000, 0.00707, 899.748, 5.99983, 1.00000, 1.01492, 0.32730, 0.38485, 15],
                        4: [ 189.381,  163.676, 0.10001, 0.03698,  48.835, 1.18093, 1.46549, 0.39664, 0.56507, 0.16119,  6],
                        5: [ 208.199,  231.482, 0.23873, 0.12962,  14.902, 1.29135, 1.84051, 0.10004, 0.46850, 0.20378,  6],
                        6: [ 171.650,  244.772, 0.10000, 0.04273,  34.753, 1.39450, 4.44404, 0.13375, 0.72177, 0.26794,  9],
                        7: [ 494.676,   76.395, 0.10000, 0.20000, 899.963, 0.97991, 6.00000, 0.34591, 0.12491, 0.45963, 15],
                        8: [ 209.724,  219.893, 0.10116, 0.06128,  25.139, 1.07207, 3.01103, 0.18381, 0.44451, 0.18767,  7],
                        9: [ 167.877,  153.714, 0.10000, 0.04715,  33.390, 1.32954, 1.00032, 0.44276, 0.55421, 0.12800,  4],
                       10: [ 188.320,  150.251, 0.10000, 0.04895,  29.036, 1.18903, 1.00009, 0.39601, 0.62023, 0.16603,  6]
                      }},
          13:
             {'MEDIA':
                      { 1: [ 116.106,  206.955, 0.19485, 0.03922,  25.353, 1.31928, 1.00055, 0.91329, 0.96880, 0.05918,  2],
                        2: [  58.767,  190.101, 0.10000, 0.01281,  50.190, 5.99813, 1.00002, 0.56180, 0.99998, 0.02467,  1],
                        3: [  26.253,  263.818, 0.10000, 0.00451, 269.995, 5.99989, 1.00000, 0.52310, 0.92750, 0.18799, 12],
                        4: [ 201.442,  226.480, 0.12067, 0.01223, 899.535, 1.04199, 4.71865, 0.55885, 0.99995, 0.08032,  3],
                        5: [ 187.979,  261.120, 0.20057, 0.12577,   8.003, 1.15733, 1.00002, 1.65485, 0.73937, 0.20526,  6],
                        6: [ 127.437,  132.375, 0.10704, 0.02659, 305.372, 1.33692, 4.61597, 0.33345, 0.99999, 0.18892,  7],
                        7: [  36.123,  101.165, 0.23887, 0.19981,  45.420, 5.99913, 6.00000, 0.10003, 0.17360, 0.32255, 11],
                        8: [ 219.760,  258.842, 0.16548, 0.03831, 110.412, 1.03577, 5.51550, 0.29193, 0.93104, 0.14970,  5],
                        9: [ 114.106,  205.602, 0.11647, 0.02908,  41.674, 1.54863, 2.54023, 0.33122, 0.99999, 0.08888,  3],
                       10: [ 213.646,  244.649, 0.12352, 0.01120, 899.941, 0.96682, 4.21356, 0.77080, 1.00000, 0.08075,  3]
                      }},
          14:
             {'PC_D4':
                      { 1: [ 152.196,  298.425, 0.30007, 0.02408,  15.396, 2.54508, 1.00009, 0.88931, 0.99999, 0.51755, 15],
                        2: [  37.954,  109.678, 0.10000, 0.09208, 899.655, 5.99203, 1.00000, 1.51117, 0.35329, 0.16322,  6],
                        3: [  12.310,  233.344, 0.10000, 0.00738, 899.948, 5.99380, 1.00000, 1.27511, 0.22879, 0.25162, 15],
                        4: [ 111.247,  270.482, 0.17377, 0.00218, 900.000, 2.06722, 5.24113, 0.38840, 0.99995, 0.39872, 15],
                        5: [ 176.701,  158.959, 0.31537, 0.09360,   8.001, 1.73329, 1.00000, 0.28952, 1.00000, 0.48720, 15],
                        6: [  95.173,   62.924, 0.32947, 0.12413, 899.895, 1.93743, 1.00072, 5.99679, 0.78392, 0.48821, 15],
                        7: [  89.309,  194.163, 0.30921, 0.02417, 899.829, 5.99976, 5.99955, 0.46978, 0.95990, 0.35931, 15],
                        8: [ 110.202,  117.746, 0.26718, 0.03507, 544.123, 1.92254, 6.00000, 0.27262, 0.99996, 0.44028, 15],
                        9: [ 134.051,  320.673, 0.13212, 0.00113, 899.872, 2.17986, 4.72997, 0.34598, 0.99978, 0.40027, 15],
                       10: [ 151.415,  388.769, 0.20652, 0.00100, 824.065, 1.61776, 3.37017, 0.64306, 0.99484, 0.44111, 15]
                      }},
          15:
             {'THSEN':
                      { 1: [ 112.276,  234.453, 0.27997, 0.01947, 792.345, 2.18869, 2.65972, 2.51076, 0.99999, 0.23534, 15],
                        2: [  98.352,  228.206, 0.10001, 0.01095, 190.721, 5.61524, 2.54370, 0.60819, 0.99995, 0.03344,  3],
                        3: [  46.583,  372.205, 0.18882, 0.00263, 590.281, 5.99794, 1.00001, 0.48565, 0.99998, 0.04383,  9],
                        4: [ 109.755,  218.442, 0.25048, 0.02147, 899.970, 2.02518, 5.99988, 0.47513, 0.99999, 0.22368, 15],
                        5: [ 120.134,  182.190, 0.34812, 0.08251,  61.726, 2.27230, 3.63096, 2.24541, 0.99977, 0.24477, 15],
                        6: [ 101.067,  140.647, 0.30366, 0.04288, 899.973, 2.73300, 5.99854, 0.25044, 0.99988, 0.21615, 14],
                        7: [  71.812,  186.083, 0.16135, 0.01381, 899.928, 5.22661, 6.00000, 0.32168, 1.00000, 0.19385, 15],
                        8: [ 131.032,  180.602, 0.30239, 0.03757, 899.934, 2.00466, 5.99990, 0.43555, 0.98797, 0.24443, 15],
                        9: [ 114.347,  216.914, 0.24978, 0.02329, 899.990, 2.40478, 5.99998, 0.45580, 1.00000, 0.24507, 15],
                       10: [ 108.399,  237.063, 0.27123, 0.02476, 899.986, 1.65426, 5.99994, 0.66291, 1.00000, 0.21875, 15]
                      }},
          21:
             {'MEDIA':
                      { 1: [   9.866,  151.055, 0.10229, 0.20000, 503.389, 6.00000, 1.00458, 0.10001, 0.02374, 0.76045, 14],
                        2: [  71.438,  162.344, 0.10012, 0.19999, 155.061, 3.89016, 1.80687, 0.12415, 0.00000, 0.48523, 11],
                        3: [  21.682,  281.707, 0.10001, 0.00639, 484.142, 5.97271, 1.00002, 0.10007, 0.04788, 0.53466, 15],
                        4: [  55.756,  163.944, 0.10001, 0.20000, 126.842, 5.93039, 1.70616, 0.10000, 0.01198, 0.45546,  8],
                        5: [   9.984,  214.583, 0.67546, 0.10987, 862.723, 5.98698, 1.07301, 3.16070, 0.10228, 0.78260, 15],
                        6: [  10.280,  213.117, 0.36755, 0.11059, 884.575, 5.89745, 1.01220, 3.41011, 0.10126, 0.78256, 15],
                        7: [  11.114,  221.075, 0.44656, 0.11181, 323.964, 5.74410, 1.00000, 3.29503, 0.10037, 0.78251, 15],
                        8: [  11.048,  152.701, 0.43829, 0.19986, 660.696, 5.47117, 1.07746, 0.10002, 0.03284, 0.45202,  8],
                        9: [  70.407,  308.830, 0.10000, 0.03323, 899.866, 5.99979, 1.00008, 6.00000, 0.00000, 0.58015, 10],
                       10: [  55.419,  278.961, 0.10000, 0.20000,  60.760, 5.99048, 5.99957, 0.10001, 0.01616, 0.42741,  7]
                      }}
         }

# Tríade de conjuntos de parâmetros para cada classe de vazão
aux = [ PARAM1[bn][cmbobs][par1],
        PARAM1[bn][cmbobs][par2],
        PARAM1[bn][cmbobs][par3]]
parametros = aux[:]

mtz_pfluvs_sispshi = {
    #[codigo, nome, Hmed, Hdp, Hmax, Hmin, DH15M, DH60M, NDautcor, Qmed, Qdp, Qmax, Q20%, Q80%, Qmin, DQ15M, DQ60M]
    1:[26064948, 'Rio Negro',           1.84, 1.46, 13.10, 0.15, 0.27, 0.34, 25,  76.1,  70.9,  712.0, 106.9,  32.2, 11.2,  10.0,  15.2],
    2:[25334953, 'Porto Amazonas',      1.72, 0.79,  6.91, 0.86, 0.58, 1.57, 15,  80.4,  64.9,  635.5, 112.0,  31.5,  8.6,  42.8, 112.8],
    3:[25564947, 'São Bento',           1.46, 0.91,  5.15, 0.08, 0.10, 0.18, 35,  34.7,  24.9,  202.0,  50.7,  15.7,  4.9,   4.8,  10.1],
    4:[25555031, 'Pontilhão',           2.43, 1.80,  8.76, 0.10, 0.09, 0.16, 40,  51.8,  46.2,  235.8,  93.4,  14.0,  3.0,   1.6,   4.0],
    5:[26125049, 'Santa Cruz do Timbó', 3.08, 1.53,  9.30, 0.91, 0.20, 0.48, 29,  79.1,  85.0,  903.4, 119.3,  19.5,  5.9,  73.6,  77.2],
    6:[25525023, 'São Mateus do Sul',   1.58, 1.16,  6.58, 0.15, 0.10, 0.14, 46, 109.9, 113.0, 1324.8, 157.7,  37.3, 16.5,  15.3,  37.2],
    7:[26055019, 'Divisa',              2.39, 1.59,  8.19, 0.28, 0.06, 0.12, 48, 165.4, 142.7, 1104.5, 235.8,  64.6, 21.9,  17.9,  17.9],
    8:[26025035, 'Fluviopolis',         1.73, 1.09,  6.74, 0.33, 0.05, 0.08, 57, 407.9, 334.0, 2082.8, 622.3, 159.2, 44.0,  15.7,  24.4],
    9:[26145104, 'União da Vitória',    2.80, 1.13,  8.00, 1.31, 0.09, 0.10, 67, 542.1, 456.0, 2737.9, 814.8, 205.7, 49.9,  52.1,  54.1],
    10:[25485116, 'Mad. Gavazzoni',      1.42, 0.37,  8.30, 0.90, 0.25, 0.43,  9,  28.4,  38.5,  811.8, 38.77,  9.18,  2.2,  35.9, 101.3],
    11:[26225115, 'Jangada',             0.84, 0.33,  2.92, 0.32, 0.19, 0.49, 10,  34.6,  47.2,  465.6, 40.20,  8.00,  0.5,  30.2,  76.4],
    13:[26055155, 'Solais Novo',         0.67, 0.40,  4.70, 0.11, 0.46, 0.79, 11,  46.4,  52.6,  492.7, 64.45, 14.78,  1.7,  67.4, 113.0],
    14:[25235306, 'Porto Santo Antônio', 0.70, 0.51,  9.30, 0.05, 0.32, 0.81, 21,  27.5,  50.0,  728.4, 48.25,  4.70,  0.1,  44.8, 147.5],
    15:[25465256, 'Águas do Verê',       1.21, 0.50,  4.63, 0.59, 0.18, 0.23, 17, 214.8, 253.5, 2850.8, 291.8, 62.14, 16.7, 182.4, 186.2],
    21:[25685442, 'Hotel Cataratas',     None, None,  8.00, 0.50, 0.22, 0.64, 11,  None,  None, 30193., 5000., 897.0, 209.8, 960.0, 3800.]
    }

codigo = mtz_pfluvs_sispshi[bn][0]
nome = mtz_pfluvs_sispshi[bn][1]
Hmed = mtz_pfluvs_sispshi[bn][2]
Hdp = mtz_pfluvs_sispshi[bn][3]
Hmax = mtz_pfluvs_sispshi[bn][4]
Hmin = mtz_pfluvs_sispshi[bn][5]
DH15M = mtz_pfluvs_sispshi[bn][6]
DH60M = mtz_pfluvs_sispshi[bn][7]
NDAC = mtz_pfluvs_sispshi[bn][8]
Qmed = mtz_pfluvs_sispshi[bn][9]
Qdp = mtz_pfluvs_sispshi[bn][10]
Qmax = mtz_pfluvs_sispshi[bn][11]
Qalta2 = mtz_pfluvs_sispshi[bn][12]
Qbaixa2 = mtz_pfluvs_sispshi[bn][13]
Qmin = mtz_pfluvs_sispshi[bn][14]
DQ15M = mtz_pfluvs_sispshi[bn][15]
DQ60M = mtz_pfluvs_sispshi[bn][16]


# Lista das variáveis datahora do período de modelagem
t = df.index[0]
tN = df.index[-1]
datas = []
while t <= tN:
    datas.append(t)
    t += timedelta(hours = 1)

# Simulação com parâmetros para vazão alta
estados = [parametros[0][0]*0.5, parametros[0][1]*0.5]
aux = Q0 * 3600 / parametros[0][9]
for i in range(parametros[0][10]):
    estados.append(aux)
Qalta = ExecutaSACSIMPLES(parametros[0], datas, etp, cmb, qmont, areainc,
                          estados)

# Simulação com parâmetros para vazão média
estados = [parametros[1][0]*0.5, parametros[1][1]*0.5]
aux = Q0 * 3600 / parametros[1][9]
for i in range(parametros[1][10]):
    estados.append(aux)
Qmedia = ExecutaSACSIMPLES(parametros[1], datas, etp, cmb, qmont, areainc,
                           estados)


# Simulação com parâmetros para vazão baixa
estados = [parametros[2][0]*0.5, parametros[2][1]*0.5]
aux = Q0 * 3600 / parametros[2][9]
for i in range(parametros[2][10]):
    estados.append(aux)
Qbaixa = ExecutaSACSIMPLES(parametros[2], datas, etp, cmb, qmont, areainc,
                           estados)

# Vazão modelada com ponderação pela classe da vazão
Qmod = Fracionamento(datas, qobs, Qalta, Qmedia, Qbaixa)
del Qalta, Qmedia, Qbaixa, estados
df['qsim_antigo'] = pd.DataFrame.from_dict(Qmod, orient = 'index')
Qsimulado = df[['qsim_antigo']]

Qsimulado.to_csv(f'./Simul_Antigo/{bn:02d}_{bnome}_sim_ant.csv',
                 date_format='%Y-%m-%dT%H:%M:%SZ', float_format = '%.3f')
