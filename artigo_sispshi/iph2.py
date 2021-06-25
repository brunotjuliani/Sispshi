import pandas as pd
import numpy as np
from numpy import array
from math import log, exp
from  time import time

X = (
        ('RMAX', 0.10, 20.0),
        ('Io', 1.0, 300.0),
        ('fIb', 1.0e-3, 0.20),
        ('H', 1.0e-5, 0.950),
        ('alfa', 0.010, 20.0),
        ('Ksup', 1.00, 200.0),
        ('Ksub', 25.0, 1000.0),
        ('Aimp', 1.0e-4, 0.40),
        ('NH', 1.510, 100.490))
Xnomes = [i[0] for i in X]
Xmin = [i[1] for i in X]
Xmax = [i[2] for i in X]

def IPH2(area, dt, PME, ETP, params, q0=None, Qmon=None):

    if type(params) is np.ndarray:
        params = dict(zip(Xnomes, params))
    #parâmetros de calibração do modelo
    RMAX    =   params['RMAX']#parâmetros de calibração do modelo
    Io      =   params['Io']
    fIb     =   params['fIb']
    H       =   params['H']
    alfa    =   params['alfa']
    Ksup    =   params['Ksup']
    Ksub    =   params['Ksub']
    Aimp    =   params['Aimp']
    NH      =   params['NH']

    #FASE BACIA
    #===========================================================================================================================
    #Manipulação de parâmetros
    Ib = Io * fIb
    Ks = exp(-1./Ksup)
    Kb = exp(-1./Ksub)
    ln_H = log(H)
    NH = int(round(NH,0))

    #aux = 10*" %12.6f" + "\n"
    #arq.write(aux % (prm["RMAX"], prm["Io"], prm["Ib"], prm["H"], prm["alfa"], prm["Ks"], prm["Kb"], prm["Aimp"], prm["NH"], ln_H))

    #Constantes do modelo computadas sobre os valores dos parâmetros
    Smax = -1 * Io / ln_H
    BI   = Io / ln_H / (Io - Ib)
    AI   = -1 * Io * BI
    AT   = 0.0
    BT   = -1 * Io / Ib / ln_H
    AIL  = -1 * AI / BI
    BIL  = 1.0 / BI
    ATL  = 0.0
    BTL  = 1.0 / BT

    #Inserindo valores padrão de parâmetros que podem não ser fornecidos
    if "xET0" not in params: xET0 = 1.0

    #Fator de conversão de mm/h para m3/s - dt em horas
    conv = area / 3.6*dt

    #aux = 8*" %12.6f" + "\n"
    #arq.write(aux % (Smax, BI, AI, BT, AIL, BIL, BTL, conv))

    #Inicializações
    S  = 0.5 * Smax
    R  = 0.5 * RMAX
    RI = AIL + BIL * S
    # if Qmon is None:
    #     Qmon = np.zeros(len(PME))
    # if q0 == None:
    #     QT = Qmon[0] / conv
    # else:
    #     QT = max(q0 - Qmon[0], 0.0) / conv
    QT = 0.0
    QS = 0.0
    PV = [0.0 for i in range(NH)]
    HIST = [1./NH for i in range(NH)]    #Bacia retangular pro histograma tempo-área

    lenCMB = len(PME)

    qbac = [None for i in range(lenCMB)]

    #arq.write(" %12.6f %12.6f %12.6f %12.6f\n" % (S, R, RI, QT))


    #Iterando o modelo a cada registro da série de dados
    for i in range(lenCMB):

        P = PME[i]
        E = ETP[i] * xET0

        #arq.write("%6i %12.6f %12.6f\n" % (i+1, P, E))

        # 1   - Perdas por evaporação e interceptação
        #-------------------------------------------------------------------------------------------------------------------
        #    A evaporação potencial é retirada da precipitação quando for inferior a esta, e em caso contrário, a evaporação
        # potencial não satisfeita é atendida pelo reservatório de interceptação (cobertura vegetal e depressões). Quando
        # este último reservatório está totalmente esgotado, o déficit de evaporação potencial passa a ser atendido pela
        # água contida no solo, através da relação linear entre a evapotranspiração e a porcentagem de umidade do solo, dado
        # por:
        # E(t) = EP(t) * ( S(t) / Smax ),    onde E(t) é a evapotranspiração da superfície no tempo t; EP(t) é a evapotrans-
        # piração potencial; S(t) é o estado de umidade da camada superior do solo.
        #    Quando a precipitação é maior que a evaporação potencial, a diferença é retida por interceptação até que sua
        # capacidade máxima Rmax seja satisfeita.
        #-------------------------------------------------------------------------------------------------------------------
        if P < E:
            EP = E - P
            P  = 0.0

            if EP <= R:
                R = R - EP

            else:
                EP = EP - R
                R  = 0.0
                ER = EP * S/Smax
                S  = S - ER

                if S < 0.0:
                    ER = ER + S
                    S  = 0.0

                RI = AIL + BIL*S
                T  = ATL + BTL*S
                ER = ER + P

            #aux = "%6i A" + 8*" %12.6f" + "\n"
            #arq.write(aux % (i+1, P, E, R, S, T, EP, ER, RI))

        else:
            P  = P - E
            ER = E
            RD = RMAX - R

            if P <= RD:
                R = R + P
                P = 0.0

            else:
                P = P - RD
                R = RMAX

            #aux = "%6i B" + 4*" %12.6f" + "\n"
            #arq.write(aux % (i+1, P, E, R, RD))

        # 2   - Separação dos volumes
        #-------------------------------------------------------------------------------------------------------------------
        #    A parcela de precipitação resultante pode gerar escoamento superficial ou infiltrar no solo, entretanto a
        # parcela de água que precipita sobre áreas impermeáveis da bacia gera escoamento superficial direto sem que ocorra
        # infiltrações. A fração da bacia coberta por áreas impermeáveis é dada pelo parâmetro AIMP.
        #    Da parcela de água que precipitou sobre a área permeável da bacia é necessário calcular o volume percolado para
        # o aquífero e o volume que gera escoamento superficial. Pela equação da continuidade tem-se o seguinte:
        # dS/dt = I(t) - T(t),    sendo S o estado de umidade do solo (mm), I(t) a infiltração e T(t) a percolação.
        #    A infiltração é contabilizada pela equação de Horton e a percolação por uma fórmula proposta por Berthelot:
        # I(t) = Ib + (Io - Ib)*(h**dt),    T(t) = Ib*(1 - h**dt),    onde Ib é a capacidade de infiltração quando o solo
        # está saturado, Io é a capacidade de infiltração do solo quando a umidade é So, h = e**(-k), e k é um parâmetro que
        # caracteriza o decaimento da curva exponencial de infiltração e depende das caracteristicas do solo.
        #-------------------------------------------------------------------------------------------------------------------
        AT1 = 1.0
        Par = P

        if P < RI:
            CR  = (P/RI)**2 / ((P/RI)+alfa)
            P   = P*(1.0 - CR)
            S1  = (S*(2.0 - 1.0/BT) + 2.0*P) / (2.0 + 1.0/BT)
            RI1 = AIL + BIL*S1

            if P < RI1:
                T  = ATL + BTL*S1
                VE = 0.0
                VI = P

            else:
                SX   = AI + BI*P
                ATX  = 2.0*BT*(SX-S) / (2.0*P*BT + 2.0*AT - SX - S)    #AT = 0
                AT1  = AT1 - ATX
                RAUX = P
                VAUX = P*ATX

                RI1 = Ib + (RAUX-Ib) * H**AT1
                S1  = AI + BI*RI1
                T   = ATL + BTL*S1
                VI  = Ib*AT1 + (RAUX-Ib)*(H**AT1 -1.0)/ln_H + VAUX
                VE  = P*AT1 - VI + VAUX

            #aux = "%6i C" + 8*" %12.6f" + "\n"
            #arq.write(aux % (i+1, Par, CR, P, S1, RI1, T, VE, VI))

        else:
            RAUX = RI
            VAUX = 0.0

            RI1 = Ib + (RAUX-Ib) * H**AT1
            S1  = AI + BI*RI1
            T   = ATL + BTL*S1
            VI  = Ib*AT1 + (RAUX-Ib)*(H**AT1 -1.0)/ln_H + VAUX
            VE  = P*AT1 - VI + VAUX

            #aux = "%6i D" + 7*" %12.6f" + "\n"
            #arq.write(aux % (i+1, RAUX, VAUX, S1, RI1, T, VE, VI))

        VP = S - S1 + VI
        VE = VE*(1.0-Aimp) + Par*Aimp

        #arq.write("%6i E %12.6f %12.6f\n" % (i+1, VP, VE))

        # 3   - Propagação dos escoamentos
        #-------------------------------------------------------------------------------------------------------------------
        #    O escoamento superficial é propagado pelo modelo Clark o qual utiliza um histograma tempo-área para simular o
        # deslocamento da água ao longo da bacia e o método de reservatório linear para o efeito de atenuação. Para o esco-
        # amento subterrâneo apenas o método de reservatório linear é utilizado. A matriz do histograma, HTA, é na realidade
        # dois vetores. Na primeira coluna devem estar os pesos do histograma para cada seção e na segunda coluna os volumes
        # do escoamento superficial acumulados para cada seção da bacia.
        #-------------------------------------------------------------------------------------------------------------------
        for KT in range(NH):
            PV[KT] = PV[KT] + VE*HIST[KT]

        VE = PV[0]

        for KT in range(NH-1):
            PV[KT] = PV[KT+1]

        PV[-1] = 0.0

        QS = QS*Ks + VE*(1.0-Ks)
        QT = QT*Kb + VP*(1.0-Kb)
        S  = S1
        RI = RI1

        #arq.write("%6i F %12.6f %12.6f %12.6f %12.6f\n" % (i+1, QS, QT, S, RI))

        qbac[i] = (QS + QT) * conv

    return qbac
