import pandas as pd
import numpy as np
from numpy import array
from math import log, exp
from  time import time

X = (
        ('Sat', 50.0, 2500.0),
        ('AI', 0.5, 5.0),
        ('CAPC', 0.30, 0.50),
        ('Crec', 0.0, 20.0),
        ('kkt', 10, 1000),
        ('k2t', 0.04, 3.0),
        ('tc', 0.042, 1.0),
        ('solo0', 0.01, 0.99),
        ('pc', 0.5, 1.2))

Xnomes = [i[0] for i in X]
Xmin = [i[1] for i in X]
Xmax = [i[2] for i in X]

def SMAP(area, dt, PME, ETP, params, iostate=False):
    """
    #--------------------------------------------------------------------------
    # Modelo SMAP - Soil Moisture Accounting Procedure
    # descrito em:
    #
    # LOPES, J.E.G.; BRAGA JR., B.P.F.; CONEJO, J.G.L. (1981) “Simulação
    # hidrológica: Aplicações de um modelo simplificado”. In: Anais do III
    # Simpósio Brasileiro de Recursos Hídricos, v.2, 42-62, Fortaleza.
    #
    # Autoria:  Mino Sorribas, 9/2017 (Python)
    #          (Adaptado de Rodrigo Paiva (RP), 1/2006, MATLAB)
    #--------------------------------------------------------------------------

    #--------------------------------------------------------------------------
    # Descrição das variáveis de entrada:
    #
    # state(.) = vetor com as variáveis de estado (saidas), sendo:
    #   i       state(i)
    #   0       Rsolo = volume armazenado no reservatório do solo (mm)
    #   1       Rsup  = volume armazenado no reservatório superficial (mm)
    #   2       Rsub  = volume armazenado no reservatório subterrâneo (mm)
    #   3       Rchn  = volume armazenado no canal (mm)
    #   4       Q  = vazão total escoado na bacia(m^3/s)
    #
    # input(.) = vetor com as entradas do modelo chuva vazão, sendo:
    #   i       input(i)
    #   0       P = precipitação (mm)
    #   1       Ep = evapotranspiração potencial(mm)
    #
    # PAR(.) = vetor com os parâmetros do modelo chuva vazão, sendo:
    #   i       PAR(i)
    #   0       Sat  - Capacidade do reservatório do solo(mm)
    #   1       AI   - Abstração inicial(mm)
    #   2       CAPC - Capacidade de campo do solo(fração)
    #   3       Crec - Parâmetro que controla a recarga subterrânea(admensional)
    #   4       kkt  - número de dias sem recarga em que a vazão de base reduz
    #                  a metade de seu valor
    #   5       k2t  - número de dias sem chuva excedente em que o escoamento
    #                  direto reduz a metade de seu valor
    #   6       tc   - tempo de concentracao (para escoamento em canal) (dias)
    #   7       Area - área de drenagem da bacia hidrográfica(km2) (FIXO)
    #--------------------------------------------------------------------------

    #--------------------------------------------------------------------------
    # Calibracao:
    #    Sat [100,2000], K2t[0.2-10], Crec[0,20], Kkt[30-180]
    #    CAPC [0.3,0.5], AI[2.5-5], tc[0.04-1]
    #
    #    K2t =   0,2 dia (.06 dia⁻1)
    #        1 dia   (.5000)
    #        2 dias  (.7070)
    #        3 dias  (.7937)
    #        4 dias  (.8409)
    #        5 dias  (.8706)
    #
    #    Kkt =  30 dias muito rápido    (.9772)
    #        60 dias     rápido      (.9885)
    #        90 dias     médio       (.9923)
    #        120 dias    lento
    #        180 dias    muito lento (.9962)
    #        Ai =  2,5 mm      Campo
    #              3,7 mm      Mata
    #              5,0 mm      Floresta densa
    #
    #        Capc =  30 %    Arenoso
    #                40 %    Misto
    #                50 %    Argiloso
    #
    #--------------------------------------------------------------------------

    #--------------------------------------------------------------------------
    #    -Descrição das variáveis locais:
    #  kk = Constante de recessão do escoamento de base(1/dia)
    #  k2 = Constante de recessão do escoamento superficial(1/dia)
    #  Es = escoamento superficial (mm)
    #  Er = evapotranspiração real (mm)
    #  Eb = escoamento de base (mm)
    #  Ed = escoamento direto (mm)
    #  S = abstração potêncial(mm)
    #  Tu = teor de umidade no solo (Rsolo/Sat)
    #  Rec = recarga subterrânea (mm)
    #  kt = Constante de recessão para propagacao em canal (1/dia)
    #
    #--------------------------------------------------------------------------
    """

    if type(params) is np.ndarray:
        params = dict(zip(Xnomes, params))

    Sat  = params['Sat']
    AI   = params['AI']    #sugere-se AI=0 para modelos horarios!
    CAPC = params['CAPC']
    Crec = params['Crec']
    kkt  = params['kkt']
    k2t  = params['k2t']
    tc   = params['tc']
    solo0= params['solo0']
    pc   = params['pc']

    solo0= 0.5

    # Get inputs
    Pin  = PME  # chuva
    Epin = ETP  # evapotranspiracao

    # # Get measurements
    # meas = dados['Qexut']

    # Set time-step conversions from daily to dt
    if dt>86400:
        print('erro: dt dados > dt calculo')
    cdt = 86400./dt
    kk0 = 0.5**(1/kkt) #para condicao inicial
    kkt = kkt*cdt
    k2t = k2t*cdt
    tc  = tc*cdt

    # More conversion factors
    #CAPC = CAPC/100  #capacidade de campo, ja entra em adimensional[0-1]
    Crec = Crec/100   #recarga, converte % para adimensional
    kk   = 0.5**(1/kkt)  #F(t)=F(0)*0.5**(t/t_half_life) #decaimento a cada passo de tempo
    k2   = 0.5**(1/k2t)
    kt   = 0.5**(1./tc) #smap horario


    sec_per_dt = dt
    mm_to_cms = area*1000./sec_per_dt #convert mm/dt to m3/s


    # Get initial state:
    # if 'state' in dados:
    #     Rsolo = dados['state']['Rsolo']
    #     Rsup  = dados['state']['Rsup']
    #     Rsub  = dados['state']['Rsub']
    #     Rchn  = dados['state']['Rchn']
    #     Q     = dados['state']['Q']

    # else: #specific discharge or initial measurement (Discharge)
    qesp = 0.02            #m3/s.km2
    Q    = qesp*area
    # if 'q0' in dados:
    #     Q = dados['q0']
    Rsolo = solo0*Sat         #supoe 50% do armaz. max
    Ebin  = Q               #vazao de base inicial
    Rsub  = Ebin/(1-kk0)/area*86.4 #mm
    Rsup  = 0.
    Rchn  = 0.              #canal seco

    #-----------------------------------------------------------
    # SMAP TIME LOOP!!!
    Qx,stx = [],[]
    #~ Qx.append(Q) #salva condicao inicial SE FIZER ISSO, VETOR FICARÁ LEN(QEXUT) + 1
    #~ stx.append([Rsolo,Rsup,Rsub,Rchn,Q])

    nt = len(Pin)
    #print(Rsub,Ebin*mm_to_cms,kk0)

    for t in range(nt):

        # Forcantes
        P  = Pin[t]*pc
        Ep = Epin[t]

        # Teor de umidade do solo
        Tu = Rsolo/Sat

        # Escoamento superficial
        Es = 0.
        if P > AI:  #AI = 0.2*S
            S  = Sat - Rsolo
            Es =(P-AI)*(P-AI)/(P-AI+S)

        # Evapotranspiração real
        Er = Ep
        if (P-Es)<=Ep:
            Er = (P-Es)+(Ep-(P-Es))*Tu

        # Recarga do Reservatório subterrâneo
        Rec = 0.
        if Rsolo>(CAPC*Sat):
            Rec = Crec*Tu*(Rsolo-(CAPC*Sat))

        # Volume armazenado no solo
        Rsolo = max(Rsolo+P-Es-Er-Rec,0.0)
        if Rsolo>Sat:
            Es  = Es + Rsolo - Sat  #inclui escoamento por saturacao
            Rsolo = Sat

        #---PROPAGACAO EM RESERVATORIOS LINEARES
        # Superficial
        alfa = 0. #0.4
        Rsup = Rsup + Es*(1-alfa)       #incremento da saturacao
        Qsup = Rsup*(1.-k2)    #vazão superficial por res. linear
        if Qsup>Rsup: Qsup = Rsup
        Rsup = Rsup - Qsup    #superficial

        # Subterraneo
        Rsub = Rsub + Rec #incremento de recarga
        Rsub = Rsub + Es*alfa     #incremento subsuperficial
        Qbas = Rsub*(1.-kk)    #vazao de base
        if Qbas>Rsub: Qbas = Rsub
        Rsub = Rsub - Qbas     #subterraneo

        # Canal (SMAP HORARIO)
        Rchn = Rchn + Rsup     #propaga superficial
        Qchn = Rchn*(1.-kt)    #vazao de base
        if Qchn>Rchn: Qchn = Rchn
        Rchn = Rchn - Qchn

        # Vazão Total da Bacia (mm/dt)
        Qbac = (Qchn+Qbas)

        # Converte em m3/s (mm/dt) (km2) (seg/dt)^-1
        Qbac = Qbac*mm_to_cms

        # Salva lista
        #Qx.append(Rsolo)
        Qx.append(Qbac)


        #if t<10:
        #    print([Rsolo,Rsup,Rsub,Rchn,Qbac])
        stx.append([Rsolo,Rsup,Rsub,Rchn,Qbac])

    output = array(Qx)

    # Fim da subrotina smap horario
    if iostate==True: output = stx

    return output
