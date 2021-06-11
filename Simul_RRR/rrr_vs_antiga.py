from datetime import datetime, timedelta
import pandas as pd
import sys
import HydroErr as he

#Numero da bacia e leitura das forçantes
bn = 12
bnome = 'Foz_do_Areia_mod'
arq = open(f'../PEQ_hr/{bn:02d}_{bnome}_peq_hr.csv')
areas = arq.readline()
areainc = float(areas.split(',')[0])
areatot = float(areas.split(',')[1])
df = pd.read_csv(f'../PEQ_hr/{bn:02d}_{bnome}_peq_hr.csv', skiprows=[0],
                 index_col = 'datahora', parse_dates = True)


#df = df.loc['2014']
cmb = df['pme']
etp = df['etp']
qmont = df['qmon']
qobs = df['qjus']
Q0 = qobs[0]

def RRR(Param,Atot,Ainc,Store,PET,PREC,QIN):
    """ Executa a integração de 1 passo de tempo (horário) do modelo 3R.
    'Param' = lista com os 11 parâmetros do modelo
    'Atot' e 'Ainc' = valores da área total e da área incremental da sub-bacia, respectivamente em km².
    'Store' = lista com o volume dos 4 reservatórios do modelo (2 do solo e 2 de propagação) em mm.
    'PET'   = valor da evapotranspiração [mm] potencial para a hora a ser integrada.
    'PREC'  = valor da chuva [mm] média na bacia para a hora a ser integrada.
    'QIN'   = valor da vazão [m³/s] contribuinte das bacias a montante na hora a ser integrada

    Irá retornar a lista de armazenamentos atualizada e a vazão simulada (mm/h)."""
    try:
        NSTEP = int(round(PREC*0.5,0)) + 1    # NSTEP é a quantidade de passos de integração dentro.
        if NSTEP < 3: NSTEP = 3
    except TypeError:
        print('PREC recebeu valor None!')
        NSTEP, PREC = 3, 0.0


    h  = 1.0 / float(NSTEP)    # h = StepSize
    hh = h / 2.0
    h6 = h / 6.0
    Linp = [ PET, PREC, max(QIN, 0.0) ]    # Lista dos inputs
    """ O volume proveniente das bacias de montante precisa ser testado quanto ao seu sinal. Não pode ser negativo!
    Em alguns casos, o modelo está tão descolado do observado que após a ancoragem parte da série simulada torna-se negativa, e
    isto é propagado a jusante. Por este motivo há a operação 'max' na atribuição do valor VolMont acima. """
    dSdt1 = derivs(Param, Atot, Ainc, Store, Linp)    # Estimativa inicial das derivadas; dSdt1 = dydx

    for k in range(NSTEP):    # Executa NSTEP passos
        # Primeiro Passo do RK4
        yt = [Store[i] + hh*dSdt1[i] for i in range(4)]

        # Segundo Passo do RK4
        dSdt2 = derivs(Param, Atot, Ainc, yt, Linp)       # dSdt2 = dyt
        yt = [Store[i] + hh*dSdt2[i] for i in range(4)]

        # Terceiro Passo do RK4
        dSdt3 = derivs(Param, Atot, Ainc, yt, Linp)       # dSdt3 = dym
        yt = [Store[i] + h*dSdt3[i] for i in range(4)]
        dSdt3 = [dSdt2[i] + dSdt3[i] for i in range(4)]

        # Quarto Passo do RK4
        dSdt2 = derivs(Param, Atot, Ainc, yt, Linp)
        for i in range(4):
            Store[i] = Store[i] + h6 * (dSdt1[i] + dSdt2[i] + 2*dSdt3[i])

    # Computando vazão simulada
    if Store[3] >= 0.0:
        Qout = Param[9] * (Store[3]**Param[10])
        Qout = Qout * Atot/3.6
    else:
        Qout = 0.0

    return Store, Qout

def derivs(Param, Atot, Ainc, S, Linp):
    """ Cálculo das derivadas dos estados (reservatórios) do modelo 3R. """
    dSdt = [0.0 for i in range(4)]

    # Forçando consistência!
    for i in range(4):
        if S[i] < 0: S[i] = 0.0
    if S[0] > Param[0]: S[0] = Param[0]
    if S[1] > Param[1]: S[1] = Param[1]

    # Fração de água (umidade) nos reservatórios do solo
    FAS1 = S[0]/Param[0]
    FAS2 = S[1]/Param[1]

    # Escoamentos da fase bacia
    ESUP = Linp[1]*(FAS1**Param[5])                                        #Escoamento Superficial
    PERC = Param[3]*Param[1]*(1.0+Param[4]*((1.0-FAS2)**Param[6]))*FAS1    #Percolação
    EVAP = Linp[0]*FAS1                                                    #Evaporação
    ESUB = Param[2]*S[0]                                                   #Escoamento Subsuperficial
    TRAN = (Linp[0]-EVAP)*(FAS2**Param[7])                                 #Transpiração
    ESOL = Param[3]*S[1]                                                   #Escoamento Subsolo
    EBAS = Param[8]*ESOL + ESUB                                            #Escoamento de Base
    VBAC = ESUP + EBAS                                                     #Vazão gerada na bacia

    #Variação no armazenamento da camada superior do solo
    dSdt[0] = Linp[1] - ESUP - PERC - EVAP - ESUB

    #Variação no armazenamento da camada inferior do solo
    dSdt[1] = PERC - TRAN - ESOL

    #Variação no armazenamento do primeiro tramo
    try:
        dSdt[2] = VBAC*Ainc/Atot + Linp[2]*3.6/Atot - Param[9]*(S[2]**Param[10])
    except TypeError:
        print('\n\n', repr(dSdt[2]))
        print(repr(VBAC), repr(Ainc), repr(Atot))
        print(repr(Linp[2]))
        print(repr(Param[9]), repr(S[2]), repr(Param[10]))
        print('\n\n')
        exit()

    #Variação no armazenamento do tramo final
    dSdt[3] = Param[9]*(S[2]**Param[10]) - Param[9]*(S[3]**Param[10])

    return dSdt


bdsimuls = {
    12:[1214,{'BACIA':12, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2', 'CMBPREV':'ENSWRFMED', 'QMONTPREV':'916,1015,1115'}],
    16:[1614,{'BACIA':16, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2', 'CMBPREV':'ENSWRFMED', 'QMONTPREV':'1314'}],
    17:[1714,{'BACIA':17, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2', 'CMBPREV':'ENSWRFMED', 'QMONTPREV':'1514'}],
    18:[1812,{'BACIA':18, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2', 'CMBPREV':'ENSWRFMED', 'QMONTPREV':'0'}],
    19:[1912,{'BACIA':19, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2', 'CMBPREV':'ENSWRFMED', 'QMONTPREV':'0'}],
    20:[2012,{'BACIA':20, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2', 'CMBPREV':'ENSWRFMED', 'QMONTPREV':'/Conceitual/prev_caxias.txt'}]
    }
cmbobs = bdsimuls[bn][1]['CMBOBS']
par1 = bdsimuls[bn][1]['PARAM']


PARAM2 = {
          12:{'2003': [  28.18230,  180.82462, 0.00150, 0.00200, 122.79871, 2.28828, 1.10000, 1.00000, 0.99800, 0.05355, 1.00000],
              2006: [  28.18230,  180.82462, 0.00150, 0.00200, 122.79871, 2.28828, 1.10000, 1.00000, 0.99800, 0.05355, 1.00000],
              2016: [ 112.254, 93.882, 0.0099950, 0.0017676, 499.666, 2.2192589, 2.1914133, 0.4639628, 0.9997856, 0.4239010, 0.5150829]
             },
          16:{'2003': [ 360.05872, 1068.53369, 0.00001, 0.00023, 137.89238, 3.57260, 1.10000, 1.00000, 0.26753, 0.12763, 1.00000],
              2006: [ 360.05872, 1068.53369, 0.00001, 0.00023, 137.89238, 3.57260, 1.10000, 1.00000, 0.26753, 0.12763, 1.00000]
             },
          17:{'2003': [ 150.00000,  400.00000, 0.00050, 0.00100,  90.00000, 2.00000, 1.10000, 1.00000, 0.90909, 0.25000, 1.00000],
              2006: [ 150.00000,  400.00000, 0.00050, 0.00100,  90.00000, 2.00000, 1.10000, 1.00000, 0.90909, 0.25000, 1.00000]
             },
          18:{'2003': [  67.55499,  185.12413, 0.00159, 0.00088, 134.66125, 1.42510, 1.10000, 1.00000, 0.99995, 0.04681, 1.00000],
              2006: [  67.55499,  185.12413, 0.00159, 0.00088, 134.66125, 1.42510, 1.10000, 1.00000, 0.99995, 0.04681, 1.00000]
             },
          19:{'2003': [ 252.69540,  899.27075, 0.00001, 0.00058, 722.00549, 9.32767, 1.10000, 1.00000, 0.09502, 0.14814, 1.00000],
              2006: [ 252.69540,  899.27075, 0.00001, 0.00058, 722.00549, 9.32767, 1.10000, 1.00000, 0.09502, 0.14814, 1.00000]
             },
          20:{'2003': [ 252.69540,  899.27075, 0.00001, 0.00058, 722.00549, 9.32767, 1.10000, 1.00000, 0.09502, 0.14814, 1.00000],
              2006: [ 252.69540,  899.27075, 0.00001, 0.00058, 722.00549, 9.32767, 1.10000, 1.00000, 0.09502, 0.14814, 1.00000]
             }
         }

# Tríade de conjuntos de parâmetros para cada classe de vazão
aux = [ PARAM2[bn][par1] ]
parametros = aux[0]

# Lista das variáveis datahora do período de modelagem
t = df.index[0]
tN = df.index[-1]
datas = []
while t <= tN:
    datas.append(t)
    t += timedelta(hours = 1)

# Estimando volume inicial nos reservatórios do canal
aux = (Q0 * 3.6 / areatot / parametros[9]) ** (1.0/parametros[10])

# Inicializando vetor de estados do modelo
estados = [ parametros[0]*0.5, parametros[1]*0.5, aux, aux ]

# Executando simulação hidrológica ao longo do período
Qmod = {}
for dt in datas:
    estados, Qmod[dt] = RRR(parametros, areatot, areainc, estados,
                        etp[dt], cmb[dt], qmont[dt])
del estados, datas


df['qsim_antigo'] = pd.DataFrame.from_dict(Qmod, orient = 'index')
Qsimulado = df[['qsim_antigo']]

Qsimulado.to_csv(f'../Simul_Antigo/{bn:02d}_{bnome}_sim_ant.csv',
                 date_format='%Y-%m-%dT%H:%M:%SZ', float_format = '%.3f')
