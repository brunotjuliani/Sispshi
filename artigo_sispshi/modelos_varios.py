from numpy import array
from math import log, exp
from random import random

    
# Modelos hidrológicos ----------------------------------------------------------------------------------
def SACSMA(dados, prm0):
    prm = {}
    
    # Parametros fixos    
    if 'ParFixos' in dados:
        for par in dados['ParFixos']:
            prm[par] = dados['ParFixos'][par]
    
    # Parametros a serem calibrados
    for q,par in enumerate(dados['calibra']):
        prm[par] = prm0[q]
    
    
    #~ prm = {'UZTWM': prm0[0], 'UZFWM': prm0[1],    'UZK': prm0[2],  'ZPERC': prm0[3],   'REXP': prm0[4], 
           #~ 'LZTWM': prm0[5], 'LZFSM': prm0[6],  'LZFPM': prm0[7],   'LZSK': prm0[8],   'LZPK': prm0[9], 
           #~ 'PFREE': prm0[10], 'SIDE': prm0[11], 'PCTIM': prm0[12], 'ADIMP': prm0[13], 'Kprop': prm0[14], 
             #~ 'lag': prm0[15] }
    
    #Inicializando armazenamentos da fase bacia
    UZTWC = prm["UZTWM"] * 0.5
    UZFWC = prm["UZFWM"] * 0.5
    LZTWC = prm["LZTWM"] * 0.5
    LZFPC = prm["LZFPM"] * 0.5
    LZFSC = prm["LZFSM"] * 0.5
    ADIMC = 0.0
    
    #Inserindo valores padrão de parâmetros que podem não ser fornecidos
    if "RSERV" not in prm: prm["RSERV"] = 0.30
    if "RIVA" not in prm: prm["RIVA"] = 0.0
    if "xET0" not in prm: prm["xET0"] = 1.0
    
    #Lista onde os dados de vazão gerada pela fase bacia serão armazenados
    qbac = []
    
    #Passo de tempo horário (1/24 dias)
    DT = 1./24.
    
    #Número de segundos no passo de tempo
    secs = 86400 * DT
    
    #Fator de conversão; X [mm/DT] * conv = Y [m3/s]
    conv = dados['area'] * 1000 / secs
    
    #Area permeável
    PAREA = 1.0 - prm["PCTIM"] - prm["ADIMP"]
    
    #Armazenamento total da zona inferior
    LZMAX = prm["LZTWM"] + prm["LZFPM"] + prm["LZFSM"]
    
    #Tamanho relativo do armazenamento primário comparado com o armazenamento livre inferior total
    HPL = prm["LZFPM"] / (prm["LZFPM"] + prm["LZFSM"])
    #arq = open('in_python.txt', 'w')

    lenCMB = len(dados['CMB'])
    
    #FASE BACIA
    #===========================================================================================================================
    #Iterando o modelo a cada registro da série de dados
    for i in range(lenCMB):
        
        #Demanda potencial de evapotranspiração e chuva média na bacia ajustados
        EDMND = dados['ETp'][i] * prm["xET0"]
        PXV = dados["CMB"][i]
        
        #Calculando a perda por evapotranspiração, na zona superior, no intervalo
        # EDMND = Demanda de evapotranspiração | Evapotranspiração de referência | Evapotranspiração Potencial [mm]
        # RED   = Diferença entre a EDMND e evapotranspiração ocorrida no intervalo (mm)
        # E1    = Evaporação ocorrida na zona de tensão superior (mm)
        # E2    = Evaporação ocorrida na zona livre superior (mm)
        # UZRAT = Fração de água em toda a zona superior
        E1 = EDMND * (UZTWC / prm["UZTWM"])
        RED = EDMND - E1
        if RED < 0:
            print(i, RED, EDMND, E1, UZTWC, prm["UZTWM"], (UZTWC / prm["UZTWM"]))
            x=input()
        E2 = 0.0
        
        #Descontando a evaporação da zona de tensão superior, porém não pode ser evaporada mais água do que há nesta camada.
        if UZTWC < E1:
            E1 = UZTWC
            UZTWC = 0.0
            RED = EDMND - E1
            
            #Descontando o resíduo da PET na zona livre superior
            if UZFWC < RED:
                E2 = UZFWC
                UZFWC = 0.0
                RED = RED - E2
                
            else:
                E2 = RED
                UZFWC = UZFWC - E2
                RED = 0.0
            
        else:
            UZTWC = UZTWC - E1
            
            #Verificando demanda de água pela zona de tensão superior
            if (UZTWC/prm["UZTWM"]) < (UZFWC/prm["UZFWM"]):
                #Fração da água na zona livre superior excedeu a fração na zona de tensão superior, então transfere-se água
                #da zona livre para a de tensão.
                UZRAT = (UZTWC + UZFWC) / (prm["UZTWM"] + prm["UZFWM"])
                UZTWC = UZRAT * prm["UZTWM"]
                UZFWC = UZRAT * prm["UZFWM"]
        
        #Verificando se os armazenamentos da zona superior secaram
        if UZTWC < 1e-6: UZTWC = 0.0
        if UZFWC < 1e-6: UZFWC = 0.0
        
        
        #Calculando a perda por evapotranspiração, na zona inferior, no intervalo
        # E3     = Evaporação ocorrida na zona de tensão inferior (mm)
        # RATLZT = Fração de água na zona de tensão inferior
        # RATLZ  = Fração de água em toda a zona inferior
        # DEL    = Coluna de água transferida da zona livre para a zona de tensão
        E3 = RED * (LZTWC / (prm["UZTWM"] + prm["LZTWM"]))
        
        if LZTWC < E3:
            E3 = LZTWC
            LZTWC = 0.0
            
        else:
            LZTWC = LZTWC - E3
        
        #Verificando demanda de agua pela zona de tensão inferior
        RATLZT = LZTWC / prm["LZTWM"]
        RATLZ = (LZTWC + LZFPC + LZFSC - prm["RSERV"]) / (LZMAX - prm["RSERV"])
        
        if RATLZT < RATLZ:
            
            #Recarregando a zona de tensão inferior com água da zona livre inferior, se houver mais água lá.
            DEL = (RATLZ-RATLZT) * prm["LZTWM"]
            
            #Transfere água da zona livre inferior suplementar (LZFSC) para a zona de tensão inferior (LZTWC)
            LZTWC = LZTWC + DEL
            LZFSC = LZFSC - DEL
            
            if LZFSC < 0.0:
                
                #Se a transferência excedeu LZFSC então o resto vem da zona livre inferior primária (LZFPC)
                LZFPC = LZFPC + LZFSC
                LZFSC = 0.0
        
        #Verificando se o armazenamento da LZTWC secou
        if LZTWC < 1e-6: LZTWC = 0.0
        
        
        #Calculando a perda por evapotranspiração da zona impermeável no intervalo
        # E5 = Evaporação ocorrida na zona impermeavel (mm)
        E5 = E1 + (RED + E2) * ((ADIMC - E1 - UZTWC) / (prm["UZTWM"] + prm["LZTWM"]))
        
        #Descontando a evaporação do armazenamento da área impermeável
        if ADIMC < E5:        
            E5 = ADIMC
            ADIMC = 0.0
            
        else:        
            ADIMC = ADIMC - E5
        
        #Determinando fração do volume da evapotranspiração na área impermeavel, relativo a toda a evapotranspiração
        #ocorrida na bacia.
        E5 = E5 * prm["ADIMP"]
        
        #Calculando os escoamentos de percolação e superficial.
        # TWX   = Umidade em excesso na zona de tensão superior, no intervalo (mm)
        # ROIMP = Escoamento superficial da área impermeável
        TWX = PXV + UZTWC - prm["UZTWM"]
        
        if TWX < 0.0:
            #Se não houve excesso de água na zona de tensão superior...
            UZTWC = UZTWC + PXV
            TWX = 0.0
            
        else:
            #... do contrário a zona de tensão superior fica saturada
            UZTWC = prm["UZTWM"]
        
        #Umidade disponível (água que não infiltrou) na zona de tensão superior, vai para o armazenamento da zona impermeável.
        ADIMC = ADIMC + PXV - TWX
        
        #Calculando o escoamento superficial da área impermeável
        ROIMP = PXV * prm["PCTIM"]
        
        #arq.write("A %6i %11.6f %11.6f %11.6f %11.6f %11.6f %11.6f" % (i+1, ADIMC, UZTWC, UZFWC, LZTWC, LZFPC, LZFSC))
        #arq.write(" %11.6f %11.6f %11.6f %11.6f %11.6f %11.6f %11.6f\n" % (EDMND, E1, E2, E3, E5, PXV, TWX))
        
        #Inicializando acumuladores do intervalo DT
        SBF   = 0.0    #Escoamento de base
        SSUR  = 0.0    #Escoamento superficial
        SIF   = 0.0    #Escoamento interno (subsuperficial)
        SPERC = 0.0    #Percolação
        SDRO  = 0.0    #Run-off direto
        SPBF  = 0.0    #Escoamento de base da zona livre inferior primária
        
        #Determinando os incrementos computacionais de tempo para o intervalo básico de tempo.
        #Nenhum incremento irá exceder 5.0 milimetros de UZFWC+TWX.
        # NINC = Número de incrementos de tempo em que o intervalo de tempo será dividido para posterior contabilidade
        #        da umidade do solo.
        # DINC = Comprimento de cada incremento em dias
        # PINC = Quantidade de umidade disponível para cada incremento
        NINC = int(round(1.0 + 0.20 * (UZFWC + TWX), 0))
        DINC = (1.0 / NINC) * DT
        PINC = TWX / NINC
        
        #Calculando frações de deplecionamento da água para o tempo de incremento, sendo que as taxas de depleção são
        #para um dia.
        # DUZ  = Depleção de água da zona superior, por incremento
        # DLZP  = Depleção de água da zona inferior primária, por incremento
        # DLZS  = Depleção de água da zona inferior suplementar, por incremento
        DUZ  = 1.0 - ((1.0 - prm["UZK"])**DINC)
        DLZP = 1.0 - ((1.0 - prm["LZPK"])**DINC)
        DLZS = 1.0 - ((1.0 - prm["LZSK"])**DINC)
        
        
        #Início do loop para os incrementos do intervalo de tempo
        for j in range(NINC):
            
            ADSUR = 0.0
            
            #Calculando escoamento superficial direto da área impermeável adicional
            # ADDRO = Volume (coluna) de run-off direto da área impermeável adicional
            RATIO = (ADIMC - UZTWC) / prm["LZTWM"]
            if RATIO < 0: RATIO = 0.0
            ADDRO = PINC * RATIO**2
            
            #Calculando o escoamento de base da zona livre inferior primária e o acumulado do intervalo de tempo
            # BF = Escoamento de base
            BF = LZFPC * DLZP
            
            if LZFPC < BF:
                BF = LZFPC
                LZFPC = 0.0
                
            else:
                LZFPC = LZFPC - BF
                
            SBF = SBF + BF
            SPBF = SPBF + BF

            #Calculando o escoamento de base da zona livre inferior suplementar e o acumulado do intervalo de tempo
            BF = LZFSC * DLZS
            
            if LZFSC < BF:
                BF = LZFSC
                LZFSC = 0.0
                
            else:
                LZFSC = LZFSC - BF
                
            SBF = SBF + BF
            
            #Calculando o volume percolado (se não houver água disponível, pula esta etapa)
            if (PINC + UZFWC) <= 0.010:
                UZFWC = UZFWC + PINC
                
            else:
                #Há água, calcula percolação.
                # PERC = Volume percolado no incremento de tempo
                # DEFR = Taxa de deficiência de umidade da zona inferior do solo
                PERCM = prm["LZFPM"] * DLZP + prm["LZFSM"] * DLZS
                PERC = PERCM * (UZFWC/prm["UZFWM"])
                DEFR = 1.0 - ((LZTWC + LZFPC + LZFSC) / LZMAX)
                PERC = PERC * (1.0 + prm["ZPERC"] * DEFR**prm["REXP"])
                
                ##Há água, calcula percolação.
                ## PERC = Volume percolado no incremento de tempo
                ## DEFR = Taxa de deficiência de umidade da zona inferior do solo
                ## A = Parâmetro apresentado em SINGH (1995) para melhorar a calibração de ZPERC
                #PERCM = prm["LZFPM"] * DLZP + prm["LZFSM"] * DLZS
                #DEFR = 1.0 - ((LZTWC + LZFPC + LZFSC) / LZMAX)
                #A = ((prm["UZFWM"] - PERCM) / (PERCM * prm["ZPERC"])) ** (1.0/prm["REXP"])
                #if DEFR <= A:
                #    PERC = (PERCM + (prm["UZFWM"] - PERCM) * (DEFR/A)**prm["REXP"]) * UZFWC/prm["UZFWM"]
                #else:
                #    PERC = UZFWC
                
                #OBS: A percolação ocorre da zona livre superior antes de PINC ser adicionado
               
                if PERC > UZFWC:
                    #Percolação não pode exceder o armazenamento da zona livre superior
                    PERC = UZFWC
                
                UZFWC = UZFWC - PERC
                
                #Verifica se a percolação excedeu a deficiência da zona inferior
                CHECK = LZTWC + LZFPC + LZFSC + PERC - LZMAX
                
                if CHECK > 0.0:
                    #Volume dos armazenamentos das zonas inferiores mais percolação não deve exceder a capacidade
                    #máxima da zona inferior.
                    PERC = PERC - CHECK
                    
                    #Devolvendo excesso à zona superior
                    UZFWC = UZFWC + CHECK
                
                #Acumulando a percolação dos incrementos
                SPERC = SPERC + PERC
                
                #Calculando o escoamento interno e o acumulado
                # DEL = Escoamento interno
                #OBS: A quantidade PINC ainda não foi adicionada
                DEL = UZFWC * DUZ
                SIF = SIF + DEL
                UZFWC = UZFWC - DEL
                
                #Distribuir a água percolada entre as zonas inferiores, sendo que a zona de tensão deve ser preenchida antes,
                #com excessão da percolação ocorrida na área PFREE.
                # PERCT = Percolação que vai para a zona de tensão inferior
                # PERCF = Percolação que vai direto para a zona livre inferior
                PERCT = PERC * (1.0 - prm["PFREE"])
                
                if (PERCT + LZTWC) > prm["LZTWM"]:
                    #Excesso irá para a zona livre inferior
                    PERCF = PERCT + LZTWC - prm["LZTWM"]
                    LZTWC = prm["LZTWM"]
                    
                else:
                    #Zona de tensão inferior recebe água percolada
                    LZTWC = LZTWC + PERCT
                    PERCF = 0.0
                    
                #Distribuir a água percolada para a zona livre inferior entre os armazenamentos de água livre.
                # RATLP = Fração de água na zona livre inferior primária
                # RATLS = Fração de água na zona livre inferior suplementar
                # FRACP = Fração da percolação que vai para zona livre primária
                # PERCP = Quantidade da percolação que vai para a zona livre primária
                # PERCS = Quantidade da percolação que vai para a zona livre suplementar
                # EXCESS = Eventual excesso da capacidade máxima da zona livre inferior primária
                PERCF = PERCF + PERC * prm["PFREE"]
                
                if PERCF > 0.0:
                    #Distribuindo percolação
                    RATLP = LZFPC / prm["LZFPM"]
                    RATLS = LZFSC / prm["LZFSM"]
                    FRACP = min(1.0, (HPL * 2.0 * (1.0-RATLP)) / ((1.0-RATLP) + (1.0-RATLS)))
                    PERCP = PERCF * FRACP
                    PERCS = PERCF - PERCP
                    
                    #Adicionando o excesso de percolação na zona suplementar
                    LZFSC = LZFSC + PERCS
                    
                    if LZFSC > prm["LZFSM"]:
                        #A adição do excesso da percolação não pode exceder a capacidade máxima da zona livre suplementar
                        PERCS = PERCS - LZFSC + prm["LZFSM"]
                        LZFSC = prm["LZFSM"]
                        
                    #Adicionando o excedente de percolação na zona primária
                    LZFPC = LZFPC + (PERCF - PERCS)
                    
                    #Verificar para ter certeza que o armazenamento livre primário não excedeu a capacidade máxima
                    if LZFPC > prm["LZFPM"]:
                        EXCESS = LZFPC - prm["LZFPM"]
                        LZTWC = LZTWC + EXCESS
                        LZFPC = prm["LZFPM"]
                        
                #Distribuir PINC entre a zona superior livre e escoamento superficial
                if PINC > 0.0:
                
                    #Verificar se o acréscimo de PINC excede a capacidade máxima da zona livre superior
                    if (PINC+UZFWC) > prm["UZFWM"]:
                    
                        #Calcular o escoamento superficial e a soma dos incrementos
                        # SUR   = Escoamento superficial
                        # ADSUR = Quantidade do escoamento direto que provém da porção ADIMP que não está gerando
                        #         escoamento superficial direto no momento
                        # ADDRO/PINC = Fração da área ADIMP que está gerando escoamento superficial direto no momento
                        SUR = PINC + UZFWC - prm["UZFWM"]
                        UZFWC = prm["UZFWM"]
                        SSUR = SSUR + SUR*PAREA
                        ADSUR = SUR * (1.0 - ADDRO/PINC)
                        SSUR = SSUR + ADSUR * prm["ADIMP"]
                        
                    else:
                        #Não excedeu, ou seja, toda a água infiltra, logo não haverá escoamento superficial
                        UZFWC = UZFWC + PINC

            #Balanço de água da área impermeável
            ADIMC = ADIMC + PINC - ADDRO - ADSUR
            
            if ADIMC > (prm["UZTWM"] + prm["LZTWM"]):
                ADDRO = ADDRO + ADIMC - (prm["UZTWM"] + prm["LZTWM"])
                ADIMC = prm["UZTWM"] + prm["LZTWM"]
                
            else:
                #Acumulando escoamento superficial direto do incremento
                SDRO = SDRO + ADDRO * prm["ADIMP"]
                
            if ADIMC < 1e-6: ADIMC = 0.0
            
            #arq.write("B %6i %11.6f %11.6f %11.6f %11.6f %11.6f %11.6f\n" % (j+1, SBF, SSUR, SIF, SPERC, SDRO, SPBF))
        
        #Fim do loop para os incrementos do intervalo de tempo       

        #Calcula os acumulados e ajusta a quantidade de run-off pela área em que ele foi gerado
        # EUSED = Evaporação ocorrida na fração de área PAREA, durante o intervalo de tempo
        EUSED = E1 + E2 + E3
        SIF = SIF * PAREA

        #Separando componente do escoamento de base que vai para o canal, da componente que não vai para o canal
        # TBF = é o escoamento de base total
        # BFCC = componente do escoamento de base que vai para o canal
        # BFNCC = componente do escoamento de base que NÃO vai para o canal
        TBF = SBF * PAREA
        BFCC = TBF * prm["SIDE"]
        BFP = SPBF * PAREA * prm["SIDE"]
        BFS = BFCC - BFP
        if BFS < 0.0: BFS = 0.0
        BFNCC = TBF - BFCC

        #Calculando escoamento afluente da bacia para o canal no intervalo de tempo
        # TCI  = Escoamento afluente total
        # GRND = Escoamento subterrâneo
        # SURF = Escoamento superficial
        TCI = ROIMP + SDRO + SSUR + SIF + BFCC
        GRND = SIF + BFCC   #interflow is part of ground flow
        SURF = TCI - GRND

        #Calcula da evapotranspiração da vegetação ciliar
        # E4 = Evapotranspiração da mata ciliar (mm)
        E4 = (EDMND - EUSED) * prm["RIVA"]

        #Subtrai a evapotranspiração da mata ciliar do escoamento afluente para o canal
        if E4 > TCI:
            E4 = TCI
            TCI = 0.0
            
        else:
            TCI = TCI - E4

        GRND = GRND - E4
        if GRND < 0.0:
           SURF = SURF + GRND
           GRND = 0.0
           if SURF < 0.0: SURF = 0.0
    
        #Calcula a evapotranspiração total que ocorreu efetivamente
        # TET = Evapotranspiração total ocorrida (mm)
        EUSED = EUSED * PAREA
        TET = EUSED + E5 + E4

        #Verifica se armazenamento da área impermeável é igual ou maior que da zona de tensão superior
        if ADIMC < UZTWC: ADIMC = UZTWC
        
        #Apenda vazão gerada pela bacia na respectiva lista
        qbac.append(TCI*conv)
        
    return PropagaCanal(dados["Qmont"], dados["q0"], prm['lag'], prm['Kprop'], qbac, NRSV = 2)
    #Concluída a fase bacia
    #===========================================================================================================================

def IPH2(dados, prm0):
    """ 
    """
    prm = {}
    # Parametros fixos
    
    # Parametros fixos    
    if 'ParFixos' in dados:
        for par in dados['ParFixos']:
            prm[par] = dados['ParFixos'][par]
    
    # Parametros a serem calibrados
    for q,par in enumerate(dados['calibra']):
        prm[par] = prm0[q]

    
    
    #FASE BACIA
    #===========================================================================================================================    
    #Manipulação de parâmetros
    prm["Ib"] = prm["Io"] * prm["fIb"]
    prm["Ks"] = exp(-1./prm["Ksup"])
    prm["Kb"] = exp(-1./prm["Ksub"])
    prm["ln(H)"] = log(prm["H"])
    prm["NH"] = int(round(prm["NH"],0))
    
    #aux = 10*" %12.6f" + "\n"
    #arq.write(aux % (prm["RMAX"], prm["Io"], prm["Ib"], prm["H"], prm["alfa"], prm["Ks"], prm["Kb"], prm["Aimp"], prm["NH"], prm["ln(H)"]))
    
    #Constantes do modelo computadas sobre os valores dos parâmetros
    Smax = -1 * prm["Io"] / prm["ln(H)"]
    BI   = prm["Io"] / prm["ln(H)"] / (prm["Io"] - prm["Ib"])
    AI   = -1 * prm["Io"] * BI
    AT   = 0.0
    BT   = -1 * prm["Io"] / prm["Ib"] / prm["ln(H)"]
    AIL  = -1 * AI / BI
    BIL  = 1.0 / BI
    ATL  = 0.0
    BTL  = 1.0 / BT
    
    #Inserindo valores padrão de parâmetros que podem não ser fornecidos
    if "xET0" not in prm: prm["xET0"] = 1.0
    
    #Fator de conversão de mm/h para m3/s
    conv = dados["area"] / 3.6
    
    #aux = 8*" %12.6f" + "\n"
    #arq.write(aux % (Smax, BI, AI, BT, AIL, BIL, BTL, conv))
    
    #Inicializações
    S  = 0.5 * Smax
    R  = 0.5 * prm["RMAX"]
    RI = AIL + BIL * S
    if dados["q0"] == None:
        QT = dados["Qmont"][0] / conv
    else:
        QT = max(dados["q0"] - dados["Qmont"][0], 0.0) / conv
    QS = 0.0
    PV = [0.0 for i in range(prm["NH"])]
    HIST = [1./prm["NH"] for i in range(prm["NH"])]    #Bacia retangular pro histograma tempo-área
    
    lenCMB = len(dados["CMB"])
    
    qbac = [None for i in range(lenCMB)]
    
    #arq.write(" %12.6f %12.6f %12.6f %12.6f\n" % (S, R, RI, QT))
    
    
    #Iterando o modelo a cada registro da série de dados
    for i in range(lenCMB):
        
        P = dados["CMB"][i]
        E = dados["ETp"][i] * prm["xET0"]
        
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
            RD = prm["RMAX"] - R

            if P <= RD:
                R = R + P
                P = 0.0
                
            else:
                P = P - RD
                R = prm["RMAX"]
            
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
            CR  = (P/RI)**2 / ((P/RI)+prm["alfa"])
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

                RI1 = prm["Ib"] + (RAUX-prm["Ib"]) * prm["H"]**AT1
                S1  = AI + BI*RI1
                T   = ATL + BTL*S1
                VI  = prm["Ib"]*AT1 + (RAUX-prm["Ib"])*(prm["H"]**AT1 -1.0)/prm["ln(H)"] + VAUX
                VE  = P*AT1 - VI + VAUX
            
            #aux = "%6i C" + 8*" %12.6f" + "\n"
            #arq.write(aux % (i+1, Par, CR, P, S1, RI1, T, VE, VI))

        else:
            RAUX = RI
            VAUX = 0.0

            RI1 = prm["Ib"] + (RAUX-prm["Ib"]) * prm["H"]**AT1
            S1  = AI + BI*RI1
            T   = ATL + BTL*S1
            VI  = prm["Ib"]*AT1 + (RAUX-prm["Ib"])*(prm["H"]**AT1 -1.0)/prm["ln(H)"] + VAUX
            VE  = P*AT1 - VI + VAUX
            
            #aux = "%6i D" + 7*" %12.6f" + "\n"
            #arq.write(aux % (i+1, RAUX, VAUX, S1, RI1, T, VE, VI))

        VP = S - S1 + VI
        VE = VE*(1.0-prm["Aimp"]) + Par*prm["Aimp"]
        
        #arq.write("%6i E %12.6f %12.6f\n" % (i+1, VP, VE))

        # 3   - Propagação dos escoamentos
        #-------------------------------------------------------------------------------------------------------------------
        #    O escoamento superficial é propagado pelo modelo Clark o qual utiliza um histograma tempo-área para simular o
        # deslocamento da água ao longo da bacia e o método de reservatório linear para o efeito de atenuação. Para o esco-
        # amento subterrâneo apenas o método de reservatório linear é utilizado. A matriz do histograma, HTA, é na realidade
        # dois vetores. Na primeira coluna devem estar os pesos do histograma para cada seção e na segunda coluna os volumes
        # do escoamento superficial acumulados para cada seção da bacia.
        #-------------------------------------------------------------------------------------------------------------------
        for KT in range(prm["NH"]):
            PV[KT] = PV[KT] + VE*HIST[KT]
        
        VE = PV[0]

        for KT in range(prm["NH"]-1):
            PV[KT] = PV[KT+1]
        
        PV[-1] = 0.0

        QS = QS*prm["Ks"] + VE*(1.0-prm["Ks"])
        QT = QT*prm["Kb"] + VP*(1.0-prm["Kb"])
        S  = S1
        RI = RI1
        
        #arq.write("%6i F %12.6f %12.6f %12.6f %12.6f\n" % (i+1, QS, QT, S, RI))
        
        qbac[i] = (QS + QT) * conv
    
    return qbac

def IPH2RL(dados, prm0):
    """ 
    """
    prm = {}
    # Parametros fixos
    
    # Parametros fixos    
    if 'ParFixos' in dados:
        for par in dados['ParFixos']:
            prm[par] = dados['ParFixos'][par]
    
    # Parametros a serem calibrados
    for q,par in enumerate(dados['calibra']):
        prm[par] = prm0[q]

    
    
    #FASE BACIA
    #===========================================================================================================================    
    #Manipulação de parâmetros
    prm["Ib"] = prm["Io"] * prm["fIb"]
    prm["Ks"] = exp(-1./prm["Ksup"])
    prm["Kb"] = exp(-1./prm["Ksub"])
    prm["ln(H)"] = log(prm["H"])
    prm["NH"] = int(round(prm["NH"],0))
    
    #aux = 10*" %12.6f" + "\n"
    #arq.write(aux % (prm["RMAX"], prm["Io"], prm["Ib"], prm["H"], prm["alfa"], prm["Ks"], prm["Kb"], prm["Aimp"], prm["NH"], prm["ln(H)"]))
    
    #Constantes do modelo computadas sobre os valores dos parâmetros
    Smax = -1 * prm["Io"] / prm["ln(H)"]
    BI   = prm["Io"] / prm["ln(H)"] / (prm["Io"] - prm["Ib"])
    AI   = -1 * prm["Io"] * BI
    AT   = 0.0
    BT   = -1 * prm["Io"] / prm["Ib"] / prm["ln(H)"]
    AIL  = -1 * AI / BI
    BIL  = 1.0 / BI
    ATL  = 0.0
    BTL  = 1.0 / BT
    
    #Inserindo valores padrão de parâmetros que podem não ser fornecidos
    if "xET0" not in prm: prm["xET0"] = 1.0
    
    #Fator de conversão de mm/h para m3/s
    conv = dados["area"] / 3.6
    
    #aux = 8*" %12.6f" + "\n"
    #arq.write(aux % (Smax, BI, AI, BT, AIL, BIL, BTL, conv))
    
    #Inicializações
    S  = 0.5 * Smax
    R  = 0.5 * prm["RMAX"]
    RI = AIL + BIL * S
    if dados["q0"] == None:
        QT = dados["Qmont"][0] / conv
    else:
        QT = max(dados["q0"] - dados["Qmont"][0], 0.0) / conv
    QS = 0.0
    PV = [0.0 for i in range(prm["NH"])]
    HIST = [1./prm["NH"] for i in range(prm["NH"])]    #Bacia retangular pro histograma tempo-área
    
    lenCMB = len(dados["CMB"])
    
    qbac = [None for i in range(lenCMB)]
    
    #arq.write(" %12.6f %12.6f %12.6f %12.6f\n" % (S, R, RI, QT))
    
    
    #Iterando o modelo a cada registro da série de dados
    for i in range(lenCMB):
        
        P = dados["CMB"][i]
        E = dados["ETp"][i] * prm["xET0"]
        
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
            RD = prm["RMAX"] - R

            if P <= RD:
                R = R + P
                P = 0.0
                
            else:
                P = P - RD
                R = prm["RMAX"]
            
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
            CR  = (P/RI)**2 / ((P/RI)+prm["alfa"])
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

                RI1 = prm["Ib"] + (RAUX-prm["Ib"]) * prm["H"]**AT1
                S1  = AI + BI*RI1
                T   = ATL + BTL*S1
                VI  = prm["Ib"]*AT1 + (RAUX-prm["Ib"])*(prm["H"]**AT1 -1.0)/prm["ln(H)"] + VAUX
                VE  = P*AT1 - VI + VAUX
            
            #aux = "%6i C" + 8*" %12.6f" + "\n"
            #arq.write(aux % (i+1, Par, CR, P, S1, RI1, T, VE, VI))

        else:
            RAUX = RI
            VAUX = 0.0

            RI1 = prm["Ib"] + (RAUX-prm["Ib"]) * prm["H"]**AT1
            S1  = AI + BI*RI1
            T   = ATL + BTL*S1
            VI  = prm["Ib"]*AT1 + (RAUX-prm["Ib"])*(prm["H"]**AT1 -1.0)/prm["ln(H)"] + VAUX
            VE  = P*AT1 - VI + VAUX
            
            #aux = "%6i D" + 7*" %12.6f" + "\n"
            #arq.write(aux % (i+1, RAUX, VAUX, S1, RI1, T, VE, VI))

        VP = S - S1 + VI
        VE = VE*(1.0-prm["Aimp"]) + Par*prm["Aimp"]
        
        #arq.write("%6i E %12.6f %12.6f\n" % (i+1, VP, VE))

        # 3   - Propagação dos escoamentos
        #-------------------------------------------------------------------------------------------------------------------
        #    O escoamento superficial é propagado pelo modelo Clark o qual utiliza um histograma tempo-área para simular o
        # deslocamento da água ao longo da bacia e o método de reservatório linear para o efeito de atenuação. Para o esco-
        # amento subterrâneo apenas o método de reservatório linear é utilizado. A matriz do histograma, HTA, é na realidade
        # dois vetores. Na primeira coluna devem estar os pesos do histograma para cada seção e na segunda coluna os volumes
        # do escoamento superficial acumulados para cada seção da bacia.
        #-------------------------------------------------------------------------------------------------------------------
        for KT in range(prm["NH"]):
            PV[KT] = PV[KT] + VE*HIST[KT]
        
        VE = PV[0]

        for KT in range(prm["NH"]-1):
            PV[KT] = PV[KT+1]
        
        PV[-1] = 0.0

        QS = QS*prm["Ks"] + VE*(1.0-prm["Ks"])
        QT = QT*prm["Kb"] + VP*(1.0-prm["Kb"])
        S  = S1
        RI = RI1
        
        #arq.write("%6i F %12.6f %12.6f %12.6f %12.6f\n" % (i+1, QS, QT, S, RI))
        
        qbac[i] = (QS + QT) * conv
    
    return PropagaCanal(dados["Qmont"], dados["q0"], prm['lag'], prm['Kprop'], qbac, NRSV = 2)


def PropagaCanal(Qmont, q0, lag, kprop, qbac, NRSV):
    """ 
    Modelo de propagação em canal Cascata de reservatórios conceituais lineares
    """    
    
    prm = {'Kprop': kprop, 'lag': lag }

    #arq.close()
    lenQBAC = len(qbac)

    #Passo de tempo horário (1/24 dias)
    DT = 1./24.
    
    #Número de segundos no passo de tempo
    secs = 86400 * DT


    #FASE CANAL
    #===========================================================================================================================
    #Número de reservatórios da fase canal
    NRSV = 2
    
    #Vetor de reservatórios e de volumes de propagação
    RSV, PROP = [None for i in range(NRSV)], [None for i in range(NRSV)]

    #Vetor de vazão calculada
    qcalc = []
    
    #Inicializando reservatórios de propagação   
    for i in range(NRSV):
        RSV[i] = (q0 * secs) / prm["Kprop"]
    
    #Executando modelo de propagação por reservatórios conceituais lineares
    for i in range(lenQBAC):
        
        RSV[0] = RSV[0] + (qbac[i] + Qmont[i]) * secs
        PROP[0] = prm["Kprop"] * RSV[0]
        RSV[0] = RSV[0] - PROP[0]
        
        for j in range(1, NRSV):
            RSV[j] = RSV[j] + PROP[j-1]
            PROP[j] = prm["Kprop"] * RSV[j]
            RSV[j] = RSV[j] - PROP[j]
        
        qcalc.append(PROP[-1]/secs)
    
    #Deslocando série em prm["lag"] horas e transformando em m3/s
    prm["lag"] = int(round(prm["lag"],0))
    if prm["lag"] > 0:
        for i in range(len(qcalc)-1, -1, -1):
            
            j = i - prm["lag"]
            
            if j < 0:
                qcalc[i] = qcalc[i]
                
            else:
                qcalc[i] = qcalc[j]
    
    #===========================================================================================================================
    return qcalc    

def SMAP(dados, prm0, iostate=False):
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

    # tempo
    dt = dados['dt']
    prm = {}
    # Parametros fixos    
    if 'ParFixos' in dados:
        for par in dados['ParFixos']:
            prm[par] = dados['ParFixos'][par]
    
    # Parametros a serem calibrados    
    for q,par in enumerate(dados['calibra']):
        #print(q,par,prm0[q])
        prm[par] = prm0[q]
    
    area = dados['area']

    Sat  = prm['Sat']
    AI   = prm['AI']    #sugere-se AI=0 para modelos horarios!
    CAPC = prm['CAPC']
    Crec = prm['Crec']
    kkt  = prm['kkt']
    k2t  = prm['k2t']    
    tc   = prm['tc']
    solo0= prm['solo0']    
    pc   = prm['pc']

    solo0= 0.5

    # Get inputs
    Pin  = dados['CMB']   # chuva 
    Epin = dados['ETp']   # evapotranspiracao

    # Get measurements
    meas = dados['Qexut']    

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
    if 'state' in dados:
        Rsolo = dados['state']['Rsolo']
        Rsup  = dados['state']['Rsup']
        Rsub  = dados['state']['Rsub']
        Rchn  = dados['state']['Rchn']
        Q     = dados['state']['Q']

    else: #specific discharge or initial measurement (Discharge)        
        qesp = 0.02            #m3/s.km2
        Q    = qesp*area
        if 'q0' in dados:
            Q = dados['q0']        
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


# Parametros dos modelos
#~ Linf_iph  = array([ 0.10,    1.0,  1.0e-3,  1.0e-5,    0.10,     1.00,    25.0,     1.e-4,   1.510     ] )
#~ Lsup_iph  = array([ 20.0,  300.0,    0.20,   0.950,    20.0,   200.00,    800.0,     0.40, 100.490     ] ) 
#~ IPH_param = [     'RMAX',   'Io',   'fIb',     'H',  'alfa',   'Ksup',   'Ksub',   'Aimp',     'NH'   ]

# Parametros do IPH relaxados
Linf_iph  = array([ 0.10,    1.0,  1.0e-3,  1.0e-5,   0.010,     1.00,    25.0,     1.e-4,   1.510     ] )
Lsup_iph  = array([ 20.0,  300.0,    0.20,   0.950,    20.0,   200.00,   1000.0,     0.40, 100.490     ] ) 
IPH_param = [     'RMAX',   'Io',   'fIb',     'H',  'alfa',   'Ksup',   'Ksub',   'Aimp',     'NH'   ]

Linf_iphrl  = array([ 0.10,    1.0,  1.0e-3,  1.0e-5,    0.10,     1.00,    25.0,     1.e-4,   1.510 ,     0.010,   -0.5 ] )
Lsup_iphrl  = array([ 20.0,  300.0,    0.20,   0.950,    20.0,   200.00,    800.0,     0.40, 100.490 ,      1.00,   10.5 ] ) 
IPHRL_param = [     'RMAX',   'Io',   'fIb',     'H',  'alfa',   'Ksup',   'Ksub',   'Aimp',     'NH',   'Kprop',   'lag' ]

Linf_sac   = array([   10.0,      5.0,   0.10,     5.0,      1.0,    10.0,     5.0,    10.0,   0.01,  0.001,    0.00,    0.5,    0.00,    0.00,   0.010,    -0.5 ])
Lsup_sac   = array([  300.0,    150.0,   0.75,   350.0,      5.0,   500.0,   400.0,  1000.0,  0.350,  0.050,    0.80,   1.00,    0.10,    0.30,    1.00,    10.5 ]) 
SAC_param  = [      'UZTWM',  'UZFWM',  'UZK', 'ZPERC',   'REXP', 'LZTWM', 'LZFSM', 'LZFPM', 'LZSK', 'LZPK', 'PFREE', 'SIDE', 'PCTIM', 'ADIMP', 'Kprop',    'lag']

#~ Linf_smap   = array([   100.0,      2.5,   0.30,     0.0,      0.97,     0.2,     5.0,    0.0 ])
#~ Lsup_smap   = array([  2000.0,      5.0,   0.50,    20.0,      0.999,   10.0,   400.0,    1.0 ]) 
#~ Smap_param  = [         'Sat',     'AI',  'CAPC',  'Crec',   'kkt',    'k2t',  'area',   'tc' ]

# Parametros do SMAP relaxados
Linf_smap   = array([   50.0,      0.5,   0.30,     0.0,      10,  0.04,    0.042, 0.01, 0.5 ])
Lsup_smap   = array([ 2500.0,      5.0,   0.50,    20.0,    1000,   3.0,    1.0, 0.99,1.2 ]) 
Smap_param  = [         'Sat',     'AI',  'CAPC',  'Crec',   'kkt',    'k2t',   'tc',   'solo0','pc']


Linf_fak   = array([   3,      5 ])
Lsup_fak   = array([  -2.5,    0 ]) 
FAK_param  = [  'a',  'b' ]

Modelos = { 'sacsma' :   { 'nome': 'Sacramento',   'fc': SACSMA,    'Linf': Linf_sac,   'Lsup': Lsup_sac,   'params': SAC_param,   'ndim': 16  }, 
            'iph2' :     { 'nome': 'IPH2',         'fc': IPH2  ,    'Linf': Linf_iph,   'Lsup': Lsup_iph,   'params': IPH_param,   'ndim': 9   }, 
            'iph2rl' :   { 'nome': 'IPH2RL',       'fc': IPH2RL ,   'Linf': Linf_iphrl, 'Lsup': Lsup_iphrl, 'params': IPHRL_param, 'ndim': 11  }, 
            'smap' :     { 'nome': 'SMAP',         'fc': SMAP   ,   'Linf': Linf_smap,  'Lsup': Lsup_smap,  'params': Smap_param,  'ndim':  8  } }