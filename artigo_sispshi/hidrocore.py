from datetime import datetime
import numpy as np

"""
Versão criada em 14/02/2017.
Substitui parâmetros calibrados pelo SCE-UA com Nash Sutcliffe como função objetivo
pelos parâmetros calibrados pelo MOCOM empregando Nash e Pearson como funções objetivo.

Parâmetros calibrados com f9 não foram alterados.
"""

def SACSMA(et0, cmb, qin, prm, area, q0):
    """ Modelo chuva-vazão Sacramento Soil Moisture Accouting.
        Modelo de propagação em canal Cascata de reservatórios conceituais lineares

    Entradas:
    et0 = lista com os dados de evapotranspiração potencial (= et. de referência) [mm em 1 hora];
    cmb = lista com os dados de chuva média na bacia [mm em 1 hora];
    qin = lista com os dados de vazão de montante [m3/s];
    prm = dicionário com os 16-20 parâmetros dos modelos (14-16 da fase bacia <+ 2 multip. dos inputs> + 2 da fase canal);
        {"UZTWM", "UZFWM", "LZTWM", "LZFPM", "LZFSM"} = capacidades máximas dos reservatórios do solo [mm];
        {"UZK", "LZPK", "LZSK"} = taxas de depleção dos reservatórios de água livre [fração/dia]
        {"ZPERC", "REXP"} = coeficiente e expoente da equação de percolação [adim.];
        {"PFREE"} = porção da água percolada que vai direto para os reservatórios de água livre [fração];
        {"PCTIM", "ADIMP"} = porção de área impermeável permanente e de área impermeável adicional [fração];
        {"SIDE"} = porção do escoamento subterrâneo que vai para o canal [fração];
        <{"RSERV", "RIVA"}> = volume na zona inferior não acessível para et. [mm], taxa de evap. da mata ciliar [fração];
        <{"xET0", "xPREC"}> = multiplicadores da evapotranspiração e da chuva média na bacia [adim.];
        {"Kprop"} = taxa de depleção dos reservatórios de propagação [fração/hora];
        {"lag"} = tempo de advecção (deslocamento temporal) da vazão propagada [horas].
    area = área [km2] da sub-bacia simulada (incremental);
    q0 = vazão inicial para os reservatórios do modelo de propagação.
    
    Saída:
    qcalc = lista com os dados de vazão calculado pelo modelo [m3/s].
    """    

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
    if "xPREC" not in prm: prm["xPREC"] = 1.0
    
    #Lista onde os dados de vazão gerada pela fase bacia serão armazenados
    qbac = []
    
    #Passo de tempo horário (1/24 dias)
    DT = 1./24.
    
    #Número de segundos no passo de tempo
    secs = 86400 * DT
    
    #Fator de conversão; X [mm/DT] * conv = Y [m3/s]
    conv = area * 1000 / secs
    
    #Area permeável
    PAREA = 1.0 - prm["PCTIM"] - prm["ADIMP"]
    
    #Armazenamento total da zona inferior
    LZMAX = prm["LZTWM"] + prm["LZFPM"] + prm["LZFSM"]
    
    #Tamanho relativo do armazenamento primário comparado com o armazenamento livre inferior total
    HPL = prm["LZFPM"] / (prm["LZFPM"] + prm["LZFSM"])
    #arq = open('in_python.txt', 'w')


    #FASE BACIA
    #===========================================================================================================================
    #Iterando o modelo a cada registro da série de dados
    for i in range(len(cmb)):
        
        #Demanda potencial de evapotranspiração e chuva média na bacia ajustados
        EDMND = et0[i] #* prm["xET0"]
        PXV = cmb[i] #* prm["xPREC"]
        
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
            raise ValueError('Residuo de evapotranspiracao negativo!')
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
        
    #Concluída a fase bacia
    #===========================================================================================================================
    #arq.close()
    
    
    #FASE CANAL
    #===========================================================================================================================
    #Número de reservatórios da fase canal
    NRSV = 2
    
    #Vetor de reservatórios e de volumes de propagação
    RSV, PROP = [None for i in range(NRSV)], [None for i in range(NRSV)]
    
    #Vetor de vazão calculada
    qcalc = []
    
    #Inicializando reservatórios de propagação
    if q0 is None: q0 = 50.
    
    for i in range(NRSV):
        RSV[i] = (q0 * secs) / prm["Kprop"]
    
    #Executando modelo de propagação por reservatórios conceituais lineares
    for i in range(len(qbac)):
        
        RSV[0] = RSV[0] + (qbac[i] + qin[i]) * secs
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



def IPH2(et0, cmb, qin, prm, area, q0):
    """ Modelo chuva-vazão IPH2.
        Modelo de propagação da vazão de montante por cascata de reservatórios conceituais lineares

    Entradas:
    et0 = lista com os dados de evapotranspiração potencial (= et. de referência) [mm em 1 hora];
    cmb = lista com os dados de chuva média na bacia [mm em 1 hora];
    qin = lista com os dados de vazão de montante [m3/s];
    prm = dicionário com os 9-13 parâmetros dos modelos (9 da fase bacia <+ 2 multip. dos inputs> <+ 2 da propagação>);
        {"RMAX"} = capacidade máxima do reservatório de interceptação [mm];
        {"Io"}   = taxa de infiltração máxima do solo [mm/h];
        {"fIb"}  = fração de Io que corresponde à taxa de infiltração mínima, quando o solo está saturado [fração];
        {"H"}    = parâmetro que define o formato da curva de infiltração na equação de Horton [adim.];
        {"alfa"} = fator de correção para precipitação efetiva [adim.]
        {"Ksup", "Ksub"} = constantes de recessão do escoamento superficial e subterrâneo respectivamente [h];
        {"Aimp"} = porção de área da bacia que é impermeável  [fração];
        {"NH"}   = tempo de concentração = número de ordenadas do Hist. Tempo-Área [h];
        <{"xET0", "xPREC"}> = multiplicadores da evapotranspiração e da chuva média na bacia [adim.];
        <{"Kprop"}> = taxa de depleção dos reservatórios de propagação [fração/hora];
        <{"lag"}> = tempo de advecção (deslocamento temporal) da vazão propagada [horas].
    area = área [km^2] da sub-bacia simulada (incremental);
    q0 = vazão observada em t=0. Serve para inicializar os reservatórios do modelo de propagação
    
    Saída:
    qcalc = lista com os dados de vazão calculado pelo modelo [m3/s].
    """
    from math import log, exp
    #arq = open("in_python.txt", "w")
    #P, E, R, S, T, EP, ER, RI, RD = [0.0 for i in range(9)]
    
    
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
    if "xPREC" not in prm: prm["xPREC"] = 1.0
    
    #Fator de conversão de mm/h para m3/s
    conv = area / 3.6
    
    #aux = 8*" %12.6f" + "\n"
    #arq.write(aux % (Smax, BI, AI, BT, AIL, BIL, BTL, conv))
    
    #Inicializações
    S  = 0.5 * Smax
    R  = 0.5 * prm["RMAX"]
    RI = AIL + BIL * S
    if q0 is None:
        QT = qin[0] / conv
    else:
        QT = max(q0 - qin[0], 0.0) / conv
    QS = 0.0
    PV = [0.0 for i in range(prm["NH"])]
    HIST = [1./prm["NH"] for i in range(prm["NH"])]    #Bacia retangular pro histograma tempo-área
    qbac = [None for i in range(len(cmb))]
    
    #arq.write(" %12.6f %12.6f %12.6f %12.6f\n" % (S, R, RI, QT))
    
    
    #Iterando o modelo a cada registro da série de dados
    for i in range(len(cmb)):
        
        P = cmb[i] #* prm["xPREC"]        
        E = et0[i] #* prm["xET0"]
        
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
    #===========================================================================================================================
    #arq.close()
    
    
    
    #PROPAGAÇAO DA VAZÃO DE MONTANTE
    #===========================================================================================================================
    if "Kprop" in prm:
        
        #Número de reservatórios da fase canal
        NRSV = 2
    
        #Vetor de reservatórios e de volumes de propagação
        RSV, PROP = [None for i in range(NRSV)], [None for i in range(NRSV)]
        
        #Vetor de vazão calculada
        qcalc = []
        
        #Inicializando reservatórios de propagação
        
        if q0 is None: q0 = 50.
        
        for i in range(NRSV):
            RSV[i] = (q0 * 3600) / prm["Kprop"]
        
        #Executando modelo de propagação por reservatórios conceituais lineares
        for i in range(len(qbac)):
            
            RSV[0] = RSV[0] + qin[i] * 3600
            PROP[0] = prm["Kprop"] * RSV[0]
            RSV[0] = RSV[0] - PROP[0]
            
            for j in range(1, NRSV):
                
                RSV[j] = RSV[j] + PROP[j-1]
                PROP[j] = prm["Kprop"] * RSV[j]
                RSV[j] = RSV[j] - PROP[j]
            
            qcalc.append(PROP[-1] / 3600)
        
        #Deslocando série em prm["lag"] horas e transformando em m3/s
        if "lag" in prm:        
            prm["lag"] = int(round(prm["lag"],0))
            
            for i in range(len(qcalc)-1, -1, -1):
                
                j = i - prm["lag"]
                
                if j < 0:
                    qcalc[i] = qcalc[i]
                    
                else:
                    qcalc[i] = qcalc[j]
        
        #Acrescentando vazão gerada na fase bacia
        for i in range(len(qcalc)):
            qcalc[i] += qbac[i]
        
        return qcalc
    
    else:
        return qbac
    #===========================================================================================================================


def SMAP(Epin, Pin, qmont, prm, area, q0):
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
    #          (Versão corrigida baseado em Rodrigo Paiva (RP), 1/2006, MATLAB)
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
    #   7       Area - área de drenagem da bacia hidrográfica(km2)
    #--------------------------------------------------------------------------

    #--------------------------------------------------------------------------
    # Calibracao:
    #    Sat [50,2500], K2t[0.04-3.], Crec[0,20], kkt[10-1000]
    #    CAPC [0.3,0.5], AI[0-5], tc[0.042-1.0]
    #
    #    K2t =   0,2 dia (.06)
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
    dt = 3600
    
    Sat  = prm['Sat']
    AI   = prm['AI']
    CAPC = prm['CAPC']
    Crec = prm['Crec']
    kkt  = prm['kkt']
    k2t  = prm['k2t']
    tc   = prm['tc']
    pc   = prm['pc']
    
    rsolo0=0.5

    '''
    # Get initial state:
    if 'Rsolo' in prm:  <-isso aqui é state, nao param
        Rsolo = prm['Rsolo']
    if 'Rsup' in prm:
        Rsup = prm['Rsup']
    if 'Rsub' in prm:
        Rsub = prm['Rsub']
    if 'Rchn' in prm:
        Rchn = prm['Rchn']
    if 'q0' in prm:
        Q = prm['Q']
    '''
    

    #auxiliar for initial condition
    kk0 = 0.5**(1/kkt)

    # Set time-step and parameter conversions from daily to dt
    cdt = 86400./dt    
    kkt = kkt*cdt       
    k2t = k2t*cdt
    tc  = tc*cdt
    

    # More conversion factors
    #CAPC = CAPC/100 #aqui ja entra em em %[0-1]
    Crec = Crec/100    
    kk   = 0.5**(1/kkt)
    k2   = 0.5**(1/k2t)
    kt   = 0.5**(1./tc) #smap horario
  
    sec_per_dt = dt
    mm_to_cms = area*1000./sec_per_dt #convert mm/dt to m3/s


    #Initial condition
    #specific discharge or initial measurement (Discharge)        
    if q0 is None:
        qesp = 0.015            #m3/s.km2
        Q    = qesp*area
    else:
        Q = q0
    Rsup  = 0.
    Rsolo = rsolo0*Sat         #supoe 50% do armaz. max
    Ebin  = Q
    Rsub  = Ebin/(1-kk0)/area*86.4
    Rchn  = 0.              #canal seco



    
    #-----------------------------------------------------------
    # SMAP TIME LOOP!!!
    Qx,stx = [],[]
    #~ Qx.append(Q) #salva condicao inicial SE FIZER ISSO, VETOR FICARÁ LEN(QEXUT) + 1
    #~ stx.append([Rsolo,Rsup,Rsub,Rchn,Q]) 
    
    nt = len(Pin)
 
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
        Rsup = Rsup + Es      #incremento da saturacao
        Qsup = Rsup*(1.-k2)    #vazão superficial por res. linear 
        if Qsup>Rsup: Qsup = Rsup   
        Rsup = Rsup - Qsup    #superficial

        # Subterraneo        
        Rsub = Rsub + Rec #incremento de recarga
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
        Qx.append(Qbac)
        #~ stx.append([Rsolo,Rsup,Rsub,Rchn,Q])

    # Fim da subrotina smap horario
    return Qx


#def SACSMA_CASCATA(et0, cmb, qin, prm, area, DT):
def SACSMA_CASCATA(et0, cmb, qin, prm, area, q0):
    """ Modelo chuva-vazão Sacramento Soil Moisture Accouting.
        Modelo de propagação em canal Cascata de reservatórios conceituais lineares

    Entradas:
    et0 = lista com os dados de evapotranspiração potencial (= et. de referência) [mm];
    cmb = lista com os dados de chuva média na bacia [mm];
    qin = lista com os dados de vazão de montante [m3/s];
    prm = dicionário com os 16-20 parâmetros dos modelos (14-16 da fase bacia <+ 2 multip. dos inputs> + 2 da fase canal);
        {"UZTWM", "UZFWM", "LZTWM", "LZFPM", "LZFSM"} = capacidades máximas dos reservatórios do solo [mm];
        {"UZK", "LZPK", "LZSK"} = taxas de depleção dos reservatórios de água livre [fração/dia]
        {"ZPERC", "REXP"} = coeficiente e expoente da equação de percolação [adim.];
        {"PFREE"} = porção da água percolada que vai direto para os reservatórios de água livre [fração];
        {"PCTIM", "ADIMP"} = porção de área impermeável permanente e de área impermeável adicional [fração];
        {"SIDE"} = porção do escoamento subterrâneo que vai para o canal [fração];
        <{"RSERV", "RIVA"}> = volume na zona inferior não acessível para et. [mm], taxa de evap. da mata ciliar [fração];
        <{"xET0", "xPREC"}> = multiplicadores da evapotranspiração e da chuva média na bacia [adim.];
        {"k"} = fator de depleção dos reservatórios de propagação - tempo de residência [dias];
        {"n"} = número de reservatórios.
    area = área [km2] da sub-bacia simulada (incremental);
        
    Saída:
    qcalc = lista com os dados de vazão calculado pelo modelo [m3/s].
    """    

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
    if "xPREC" not in prm: prm["xPREC"] = 1.0
    
    #Lista onde os dados de vazão gerada pela fase bacia serão armazenados
    qbac = []
        
    #Número de segundos no passo de tempo
    DT = 1/24.
    secs = 86400 * DT
    
    #Fator de conversão; X [mm/DT] * conv = Y [m3/s]
    conv = area * 1000 / secs
    
    #Area permeável
    PAREA = 1.0 - prm["PCTIM"] - prm["ADIMP"]
    
    #Armazenamento total da zona inferior
    LZMAX = prm["LZTWM"] + prm["LZFPM"] + prm["LZFSM"]
    
    #Tamanho relativo do armazenamento primário comparado com o armazenamento livre inferior total
    HPL = prm["LZFPM"] / (prm["LZFPM"] + prm["LZFSM"])
    #arq = open('in_python.txt', 'w')


    #FASE BACIA
    #===========================================================================================================================
    #Iterando o modelo a cada registro da série de dados
    for i in range(len(cmb)):
        
        #Demanda potencial de evapotranspiração e chuva média na bacia ajustados
        EDMND = et0[i] * prm["xET0"]
        PXV = cmb[i] * prm["xPREC"]
        
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
            raise ValueError('Residuo de evapotranspiracao negativo!')
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
        
    #Concluída a fase bacia
    #===========================================================================================================================
    
    #FASE CANAL
    #===========================================================================================================================
    """ 
    Modelo de propagação em canal representado por n reservatórios lineares em cascata
    Alterado em 9/11/2018 por Arlan Almeida e Mino Sorribas
    
    Esquema numérico simples para a resolução das duas EDOs abaixo, explícito para S(t+1),:
    1. dS(t)/dt = I(t) - Q(t)
    2. S(t) = k.Q(t)
    --> S(t+1) = S(t) + [I(t+1) + I(t)]/2*DT + [I(t+1) + I(t)]/2*DT
       
    Entradas:
    qbac[i] + Qmont[i] - Vazão afluente ao primeiro reservatório [m³/s] <<< Unidade obrigatória para o funcionamento
    k                  - Constante de depleção [dias]
    n                  - Numéro de reservatórios [inteiro adimensional]
    DT                 - Passo de tempo [dias]
    S                  - Armazenamento [m³]
    
    Saida:
    qcalc              - Vazão efluente do último reservatório [m³/s]
    """    
    
    n = prm["n"]
    k = prm["k"]
    
    #O número de reservatórios deve ser inteiro nessa formulação
    n = int(round(n))
    
    #Cria a matriz para os armazenamentos em t e t + DT
    S_reserv = np.zeros((2,n))
    #S_reserv = zeros((2,n))
    
    #Define os volumes iniciais
    V0 = 0. #Passível de discussão
    S_reserv[0] = np.full((1,1), V0)
    qcalc = [S_reserv[0][n-1]/k*(1/86400)]
       
    #Propaga as vazões
    for i in np.arange(1,len(qbac)):
        #Primeiro reservatório
        q0 = qbac[i-1] + qin[i-1]
        q1 = qbac[i] + qin[i]
        rsv = 0
        S_reserv[1][rsv] = ( S_reserv[0][rsv]*(1-DT/(2*k)) + (q1 + q0)*86400/2*DT ) / ( 1 + DT/(2*k) )
        #Propagação nos reservatórios subsequentes
        for rsv in np.arange(1,n):
            S_reserv[1][rsv] = ( S_reserv[0][rsv]*(1-DT/(2*k)) + (S_reserv[1][rsv-1]/k + S_reserv[0][rsv-1]/k)/2*DT ) / ( 1 + DT/(2*k) )
        qcalc.append(S_reserv[1][n-1]/k*(1/86400))
        S_reserv[0] = S_reserv[1]
    #===========================================================================================================================
    return qcalc


# PARAMETROS DAS CONFIGURAÇÕES DE MODELAGEM
#===============================================================================================================================
parametros = [
    
    # Parâmetros CH1 --- pluviometro +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    {
        "idSimul": "CH1-SAC-F1-PLU",
        "config": {
            "id": "CH1",
            "modelo": SACSMA,
            "fobj": "NSE",
            "chuva": "pluviometros",
            "periodo": [datetime(2013, 9, 8, 10, 0, 0), datetime(2016, 1, 1, 0, 0, 0)]
        },
        "parametros": {
             "UZTWM": 32.042307 ,
             "UZFWM": 65.250045 ,
               "UZK": 0.746321  ,
             "ZPERC": 349.699284 ,
              "REXP": 2.198469   ,
             "LZTWM": 167.158283 ,
             "LZFSM": 66.813989,
             "LZFPM": 10.010542,
              "LZSK": 0.159538 ,
              "LZPK": 0.041539 ,
             "PFREE": 0.548213 ,
              "SIDE": 0.863109 ,
             "PCTIM": 0.000000 ,
             "ADIMP": 0.000997 ,
             "Kprop": 0.134130 ,
               "lag": 2.401661 
        }
    },
    {
        "idSimul": "CH1-SAC-F2-PLU",
        "config": {
            "id": "CH1",
            "modelo": SACSMA,
            "fobj": "DesvResid",
            "chuva": "pluviometros",
            "periodo": [datetime(2013, 9, 8, 10, 0, 0), datetime(2016, 1, 1, 0, 0, 0)],
        },
        "parametros": {
            "UZTWM": 21.294,
            "UZFWM": 43.623,
            "UZK": 0.749999,
            "ZPERC": 349.617,
            "REXP": 4.304152,
            "LZTWM": 180.207,
            "LZFSM": 124.391,
            "LZFPM": 10.000,
            "LZSK": 0.120527,
            "LZPK": 0.049999,
            "PFREE": 0.466255,
            "SIDE": 0.938492,
            "PCTIM": 0.000063,
            "ADIMP": 0.025973,
            "Kprop": 0.103948,
            "lag": 1.9
        }
    },
    {
        "idSimul": "CH1-IPH-F1-PLU",
        "config": {
            "id": "CH1",
            "modelo": IPH2,
            "fobj": "NSE",
            "chuva": "pluviometros",
            "periodo": [datetime(2013, 9, 8, 10, 0, 0), datetime(2016, 1, 1, 0, 0, 0)],
        },
        "parametros": {
          "RMAX": 19.999272,
            "Io": 58.813877,
           "fIb": 0.001702 ,
             "H": 0.639594 ,
          "alfa": 0.140491 ,
          "Ksup": 28.165320,
          "Ksub": 55.092941,
          "Aimp": 0.341364 ,
            "NH": 18.050399  
        }
    },
    {
        "idSimul": "CH1-IPH-F2-PLU",
        "config": {
            "id": "CH1",
            "modelo": IPH2,
            "fobj": "DesvResid",
            "chuva": "pluviometros",
            "periodo": [datetime(2013, 9, 8, 10, 0, 0), datetime(2016, 1, 1, 0, 0, 0)],
        },
        "parametros": {
            "RMAX": 17.7031,
            "Io": 18.2108,
            "fIb": 0.00384207,
            "H": 0.821340,
            "alfa": 0.100008,
            "Ksup": 30.6622,
            "Ksub": 219.4026,
            "Aimp": 0.117807,
            "NH": 18.20
        }
    },
        
    
    
    # Parâmetros CH1 --- siprec +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        
        {
        "idSimul": "CH1-SAC-F1-SIPREC",
        "config": {
            "id": "CH1",
            "modelo": SACSMA,
            "fobj": "NSE",
            "chuva": "SIPREC",
            "periodo": [datetime(2013, 9, 8, 10, 0, 0), datetime(2016, 1, 1, 0, 0, 0)]
        },
        "parametros": {
             "UZTWM": 10.001 ,
             "UZFWM": 106.669 ,
               "UZK": 0.672590  ,
             "ZPERC": 5.000 ,
              "REXP": 4.999690 ,
             "LZTWM": 499.772  ,
             "LZFSM": 48.919  ,
             "LZFPM": 999.968 ,
              "LZSK": 0.010004 ,
              "LZPK": 0.002574 ,
             "PFREE": 0.799791 ,
              "SIDE": 0.999989 ,
             "PCTIM": 0.099983 ,
             "ADIMP": 0.093607 ,
             "Kprop": 0.136471  ,
               "lag": 2.9
        }
    },
    {
        "idSimul": "CH1-SAC-F2-SIPREC",
        "config": {
            "id": "CH1",
            "modelo": SACSMA,
            "fobj": "DesvResid",
            "chuva": "SIPREC",
            "periodo": [datetime(2013, 9, 8, 10, 0, 0), datetime(2016, 1, 1, 0, 0, 0)],
        },
        "parametros": {
            "UZTWM": 10.000   ,
            "UZFWM": 149.987   ,
            "UZK":   0.749978     ,
            "ZPERC": 5.000   ,
            "REXP":  4.999475    ,
            "LZTWM": 499.995   ,
            "LZFSM": 399.989    ,
            "LZFPM": 999.992   ,
            "LZSK":  0.010000    ,
            "LZPK":  0.003810    ,
            "PFREE": 0.799994   ,
            "SIDE":  0.999993    ,
            "PCTIM": 0.099996   ,
            "ADIMP": 0.000002   ,
            "Kprop": 0.110494   ,
            "lag":   0.9
        }
    },
    {
        "idSimul": "CH1-IPH-F1-SIPREC",
        "config": {
            "id": "CH1",
            "modelo": IPH2,
            "fobj": "NSE",
            "chuva": "SIPREC",
            "periodo": [datetime(2013, 9, 8, 10, 0, 0), datetime(2016, 1, 1, 0, 0, 0)],
        },
        "parametros": {
          "RMAX": 0.1000 ,
            "Io": 129.1046 ,
           "fIb": 0.00552492,
             "H": 0.008300  ,
          "alfa": 0.100001  ,
          "Ksup": 6.5302  ,
          "Ksub": 25.0004 ,
          "Aimp": 0.085385  ,
            "NH": 29.20  
        }
    },
    {
        "idSimul": "CH1-IPH-F2-SIPREC",
        "config": {
            "id": "CH1",
            "modelo": IPH2,
            "fobj": "DesvResid",
            "chuva": "SIPREC",
            "periodo": [datetime(2013, 9, 8, 10, 0, 0), datetime(2016, 1, 1, 0, 0, 0)],
        },
        "parametros": {
            "RMAX": 0.2022 ,
            "Io":   152.7062 ,
            "fIb":  0.00416711,
            "H":    0.004076  ,
            "alfa": 0.100000  ,
            "Ksup": 8.0685  ,
            "Ksub": 55.8706 ,
            "Aimp": 0.292704  ,
            "NH":   28.87
        }
    },
        
        
        
    # Parâmetros CH2 --- pluviometro +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        
     {
        "idSimul": "CH2-SAC-F1-PLU",
        "config": {
            "id": "CH2",
            "modelo": SACSMA,
            "fobj": "NSE",
            "chuva": "pluviometros",
            "periodo": [datetime(2013, 9, 8, 10, 0, 0), datetime(2016, 1, 1, 0, 0, 0)],
        },
        "parametros": {
             "UZTWM": 19.876963 ,
             "UZFWM": 89.764077 ,
               "UZK": 0.748735  ,
             "ZPERC": 173.658594,
              "REXP": 3.890180  ,
             "LZTWM": 98.334026 ,
             "LZFSM": 138.942943,
             "LZFPM": 10.000683 ,
              "LZSK": 0.194822  ,
              "LZPK": 0.025392  ,
             "PFREE": 0.501885  ,
              "SIDE": 0.653351  ,
             "PCTIM": 0.000004  ,
             "ADIMP": 0.111358  ,
             "Kprop": 0.164647  ,
               "lag": 2.667886  
        }
    },
    {
        "idSimul": "CH2-SAC-F2-PLU",
        "config": {
            "id": "CH2",
            "modelo": SACSMA,
            "fobj": "DesvResid",
            "chuva": "pluviometros",
            "periodo": [datetime(2013, 9, 8, 10, 0, 0), datetime(2016, 1, 1, 0, 0, 0)],
        },
        "parametros": {
            "UZTWM": 10.421,
            "UZFWM": 45.353,
            "UZK": 0.749915,
            "ZPERC": 156.676,
            "REXP": 4.999976,
            "LZTWM": 99.634,
            "LZFSM": 144.728,
            "LZFPM": 10.000,
            "LZSK": 0.152644,
            "LZPK": 0.049952,
            "PFREE": 0.539366,
            "SIDE": 0.789717,
            "PCTIM": 0.000004,
            "ADIMP": 0.040774,
            "Kprop": 0.156822,
            "lag": 2.2
        }
    },
    {
        "idSimul": "CH2-IPH-F1-PLU",
        "config": {
            "id": "CH2",
            "modelo": IPH2,
            "fobj": "NSE",
            "chuva": "pluviometros",
            "periodo": [datetime(2013, 9, 8, 10, 0, 0), datetime(2016, 1, 1, 0, 0, 0)],
        },
        "parametros": {
            "RMAX": 13.889547   ,
              "Io": 35.077542   ,
             "fIb": 0.017976   ,
               "H": 0.248833   ,
            "alfa": 0.288519   ,
            "Ksup": 17.784447   ,
            "Ksub": 259.652273  ,
            "Aimp": 0.143294   ,
              "NH": 14.328654
        }
    },
    {
        "idSimul": "CH2-IPH-F2-PLU",
        "config": {
            "id": "CH2",
            "modelo": IPH2,
            "fobj": "DesvResid",
            "chuva": "pluviometros",
            "periodo": [datetime(2013, 9, 8, 10, 0, 0), datetime(2016, 1, 1, 0, 0, 0)],
        },
        "parametros": {
            "RMAX": 20.0000,
            "Io": 36.4561,
            "fIb": 0.01135342,
            "H": 0.170600,
            "alfa": 0.100003,
            "Ksup": 24.6241,
            "Ksub": 493.9511,
            "Aimp": 0.000100,
            "NH": 12.08
        }
    },       
        
        
       # Parâmetros CH2 --- siprec +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        
        
          {
        "idSimul": "CH2-SAC-F1-SIPREC",
        "config": {
            "id": "CH2",
            "modelo": SACSMA,
            "fobj": "NSE",
            "chuva": "SIPREC",
            "periodo": [datetime(2013, 9, 8, 10, 0, 0), datetime(2016, 1, 1, 0, 0, 0)],
        },
        "parametros": {
             "UZTWM": 10.000  ,
             "UZFWM": 79.253 ,
               "UZK": 0.748794,
             "ZPERC": 28.750 ,
              "REXP": 4.999916,
             "LZTWM": 499.998 ,
             "LZFSM": 399.917 ,
             "LZFPM": 999.998 ,
              "LZSK": 0.010000,
              "LZPK": 0.003118,
             "PFREE": 0.799967,
              "SIDE": 0.999999,
             "PCTIM": 0.020487,
             "ADIMP": 0.000001,
             "Kprop": 0.151096,
               "lag": -0.1
        }
    },
    {
        "idSimul": "CH2-SAC-F2-SIPREC",
        "config": {
            "id": "CH2",
            "modelo": SACSMA,
            "fobj": "DesvResid",
            "chuva": "SIPREC",
            "periodo": [datetime(2013, 9, 8, 10, 0, 0), datetime(2016, 1, 1, 0, 0, 0)],
        },
        "parametros": {
            "UZTWM": 10.000 ,
            "UZFWM": 149.920 ,
            "UZK":   0.558282 ,
            "ZPERC": 5.001 ,
            "REXP":  4.998805 ,
            "LZTWM": 10.000 ,
            "LZFSM": 399.995  ,
            "LZFPM": 999.999 ,
            "LZSK":  0.010000 ,
            "LZPK":  0.004946 ,
            "PFREE": 0.799998 ,
            "SIDE":  0.999996 ,
            "PCTIM": 0.099990 ,
            "ADIMP": 0.000005 ,
            "Kprop": 0.172429 ,
            "lag":   -0.1
        }
    },
    {
        "idSimul": "CH2-IPH-F1-SIPREC",
        "config": {
            "id": "CH2",
            "modelo": IPH2,
            "fobj": "NSE",
            "chuva": "SIPREC",
            "periodo": [datetime(2013, 9, 8, 10, 0, 0), datetime(2016, 1, 1, 0, 0, 0)],
        },
        "parametros": {
            "RMAX": 3.7802    ,
              "Io": 46.2301   ,
             "fIb": 0.19999848  ,
               "H": 0.449807   ,
            "alfa": 0.100001  ,
            "Ksup": 199.9991    ,
            "Ksub": 25.0000   ,
            "Aimp": 0.148809  ,
              "NH": 100.17
        }
    },
    {
        "idSimul": "CH2-IPH-F2-SIPREC",
        "config": {
            "id": "CH2",
            "modelo": IPH2,
            "fobj": "DesvResid",
            "chuva": "SIPREC",
            "periodo": [datetime(2013, 9, 8, 10, 0, 0), datetime(2016, 1, 1, 0, 0, 0)],
        },
        "parametros": {
            "RMAX": 0.1747  ,
            "Io":   30.2335 ,
            "fIb":  0.11735311,
            "H":    0.000068  ,
            "alfa": 0.116706 ,
            "Ksup": 199.9938  ,
            "Ksub": 31.6881 ,
            "Aimp": 0.267118  ,
            "NH":   17.44
        }
    },
        
     # Parâmetros L1 --- pluviometro +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
                  
        
    {
        "idSimul": "L1-SAC-F1-PLU",
        "config": {
            "id": "L1",
            "modelo": SACSMA,
            "fobj": "NSE",
            "chuva": "pluviometros",
            "periodo": [datetime(2011, 12, 2, 12, 0, 0), datetime(2015, 5, 16, 12, 0, 0)]
        },
        "parametros": {
            "UZTWM": 10.002362      ,
            "UZFWM": 148.232169     ,
              "UZK": 0.272616    ,
            "ZPERC": 5.004155       ,
             "REXP": 3.776938    ,
            "LZTWM": 17.540006       ,
            "LZFSM": 5.327289      ,
            "LZFPM": 560.230323     ,
             "LZSK": 0.331015    ,
             "LZPK": 0.030141    ,
            "PFREE": 0.799997    ,
             "SIDE": 0.999819    ,
            "PCTIM": 0.034132    ,
            "ADIMP": 0.250568    ,
            "Kprop": 0.341801    ,
              "lag": 1.481581
        }
    },
    {
        "idSimul": "L1-SAC-F2-PLU",
        "config": {
            "id": "L1",
            "modelo": SACSMA,
            "fobj": "DesvResid",
            "chuva": "pluviometros",
            "periodo": [datetime(2011, 12, 2, 12, 0, 0), datetime(2015, 5, 16, 12, 0, 0)],
        },
        "parametros": {
            "UZTWM": 10.000,
            "UZFWM": 149.947,
            "UZK":   0.100020,
            "ZPERC": 8.548,
            "REXP":  1.002640,
            "LZTWM": 10.000,
            "LZFSM": 399.966,
            "LZFPM": 684.648,
            "LZSK":  0.349994,
            "LZPK":  0.026723,
            "PFREE": 0.799989,
            "SIDE":  0.999999,
            "PCTIM": 0.099998,
            "ADIMP": 0.216113,
            "Kprop": 0.299749,
            "lag":    0.8
        }
    },
    {
        "idSimul": "L1-IPH-F1-PLU",
        "config": {
            "id": "L1",
            "modelo": IPH2,
            "fobj": "NSE",
            "chuva": "pluviometros",
            "periodo": [datetime(2011, 12, 2, 12, 0, 0), datetime(2015, 5, 16, 12, 0, 0)],
        },
        "parametros": {
            "RMAX": 13.256900   ,
              "Io": 99.003259   ,
             "fIb": 0.199905   ,
               "H": 0.008829   ,
            "alfa": 0.100053   ,
            "Ksup": 6.192437    ,
            "Ksub": 312.167119  ,
            "Aimp": 0.389121   ,
              "NH": 4.190168
        }
    },
    {
        "idSimul": "L1-IPH-F2-PLU",
        "config": {
            "id": "L1",
            "modelo": IPH2,
            "fobj": "DesvResid",
            "chuva": "pluviometros",
            "periodo": [datetime(2011, 12, 2, 12, 0, 0), datetime(2015, 5, 16, 12, 0, 0)],
        },
        "parametros": {
            "RMAX": 3.1392    ,
              "Io": 60.8427   ,
             "fIb": 0.03403894, 
               "H": 0.020404  ,
            "alfa": 0.100002  ,
            "Ksup": 12.6929   ,
            "Ksub": 263.6306  ,
            "Aimp": 0.289086  , 
              "NH": 2.16      
        }
    },
        
        
     # Parâmetros L1 --- siprec +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++  
             
    {
        "idSimul": "L1-SAC-F1-SIPREC",
        "config": {
            "id": "L1",
            "modelo": SACSMA,
            "fobj": "NSE",
            "chuva": "SIPREC",
            "periodo": [datetime(2011, 12, 2, 12, 0, 0), datetime(2015, 5, 16, 12, 0, 0)]
        },
        "parametros": {
            "UZTWM": 10.000      ,
            "UZFWM": 149.998      ,
              "UZK": 0.506284   ,
            "ZPERC": 5.000      ,
             "REXP": 4.999971   ,
            "LZTWM": 10.000       ,
            "LZFSM": 399.997      ,
            "LZFPM": 999.997      ,
             "LZSK": 0.010001   ,
             "LZPK": 0.002969   ,
            "PFREE": 0.799999   ,
             "SIDE": 0.999999   ,
            "PCTIM": 0.100000   ,
            "ADIMP": 0.234587   ,
            "Kprop": 0.396412   ,
              "lag": 0.6
        }
    },
    {
        "idSimul": "L1-SAC-F2-SIPREC",
        "config": {
            "id": "L1",
            "modelo": SACSMA,
            "fobj": "DesvResid",
            "chuva": "SIPREC",
            "periodo": [datetime(2011, 12, 2, 12, 0, 0), datetime(2015, 5, 16, 12, 0, 0)],
        },
        "parametros": {
            "UZTWM": 10.000   ,
            "UZFWM": 149.998   ,
            "UZK":   0.466725    ,
            "ZPERC": 5.001   ,
            "REXP":  4.999576    ,
            "LZTWM": 10.003   ,
            "LZFSM": 399.979   ,
            "LZFPM": 1000.000   ,
            "LZSK":  0.010000   ,
            "LZPK":  0.002389   ,
            "PFREE": 0.799950   ,
            "SIDE":  0.999988   ,
            "PCTIM": 0.099999   ,
            "ADIMP": 0.270417   ,
            "Kprop": 0.373900    ,
            "lag":   0.8
        }
    },
    {
        "idSimul": "L1-IPH-F1-SIPREC",
        "config": {
            "id": "L1",
            "modelo": IPH2,
            "fobj": "NSE",
            "chuva": "SIPREC",
            "periodo": [datetime(2011, 12, 2, 12, 0, 0), datetime(2015, 5, 16, 12, 0, 0)],
        },
        "parametros": {
            "RMAX": 0.1000    ,
              "Io": 86.5147   ,
             "fIb": 0.03822012 ,
               "H": 0.009244   ,
            "alfa": 0.118267   ,
            "Ksup": 5.2212    ,
            "Ksub": 95.4259   ,
            "Aimp": 0.400000   ,
              "NH": 3.87
        }
    },
    {
        "idSimul": "L1-IPH-F2-SIPREC",
        "config": {
            "id": "L1",
            "modelo": IPH2,
            "fobj": "DesvResid",
            "chuva": "SIPREC",
            "periodo": [datetime(2011, 12, 2, 12, 0, 0), datetime(2015, 5, 16, 12, 0, 0)],
        },
        "parametros": {
            "RMAX": 0.1000  ,
              "Io": 75.9165 ,
             "fIb": 0.04945703, 
               "H": 0.019740  ,
            "alfa": 0.676485  ,
            "Ksup": 5.3925 ,
            "Ksub": 115.1702 ,
            "Aimp": 0.399999  , 
              "NH": 3.67
        }
    },
        
        
    # Parâmetros L2 --- pluviometro +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        
        
    {
        "idSimul": "L2-SAC-F1-PLU",
        "config": {
            "id": "L2",
            "modelo": SACSMA,
            "fobj": "NSE",
            "chuva": "pluviometros",
            "periodo": [datetime(2011, 12, 22, 15, 0, 0), datetime(2016, 1, 1, 0, 0, 0)],
        },
        "parametros": {
             "UZTWM": 165.265569 ,
             "UZFWM": 71.350285  ,
               "UZK": 0.749333   ,
             "ZPERC": 72.888856  ,
              "REXP": 4.931595   ,
             "LZTWM": 15.301718  ,
             "LZFSM": 64.324773  ,
             "LZFPM": 594.042043 ,
              "LZSK": 0.265824   ,
              "LZPK": 0.006063   ,
             "PFREE": 0.481521   ,
              "SIDE": 0.626220   ,
             "PCTIM": 0.022315   ,
             "ADIMP": 0.035946   ,
             "Kprop": 0.574664   ,
               "lag": 0.993390
        }
    },
    {
        "idSimul": "L2-SAC-F2-PLU",
        "config": {
            "id": "L2",
            "modelo": SACSMA,
            "fobj": "DesvResid",
            "chuva": "pluviometros",
            "periodo": [datetime(2011, 12, 22, 15, 0, 0), datetime(2016, 1, 1, 0, 0, 0)],
        },
        "parametros": {
            "UZTWM": 258.531  ,
            "UZFWM": 66.196   ,
              "UZK": 0.750000 ,
            "ZPERC": 285.812  ,
             "REXP": 4.277556 ,
            "LZTWM": 10.817   ,
            "LZFSM": 200.637  ,
            "LZFPM": 998.244  ,
             "LZSK": 0.010000 ,
             "LZPK": 0.005568 ,
            "PFREE": 0.319375 ,
             "SIDE": 0.801434 ,
            "PCTIM": 0.018509 ,
            "ADIMP": 0.044514 ,
            "Kprop": 0.553865 ,
              "lag": 1.0      
        }
    },
    {
        "idSimul": "L2-IPH-F1-PLU",
        "config": {
            "id": "L2",
            "modelo": IPH2,
            "fobj": "NSE",
            "chuva": "pluviometros",
            "periodo": [datetime(2011, 12, 22, 15, 0, 0), datetime(2016, 1, 1, 0, 0, 0)],
        },
        "parametros": {
            "RMAX": 19.938753    ,
              "Io": 33.464074    ,
             "fIb": 0.066540   ,
               "H": 0.000374   ,
            "alfa": 0.440162   ,
            "Ksup": 12.526756    ,
            "Ksub": 798.597778   ,
            "Aimp": 0.116153   ,
              "NH": 4.058037   ,
           "Kprop": 0.591201   ,
             "lag": 0.684974
              
        }
    },
    {
        "idSimul": "L2-IPH-F2-PLU",
        "config": {
            "id": "L2",
            "modelo": IPH2,
            "fobj": "DesvResid",
            "chuva": "pluviometros",
            "periodo": [datetime(2011, 12, 22, 15, 0, 0), datetime(2016, 1, 1, 0, 0, 0)],
        },
        "parametros": {
            "RMAX": 18.7570  ,
              "Io": 14.8779 ,
             "fIb": 0.01581923 , 
               "H": 0.875486  ,
            "alfa": 0.141005  ,
            "Ksup": 10.9388 ,
            "Ksub": 799.9911 ,
            "Aimp": 0.011282   , 
              "NH": 4.04 ,
           "Kprop": 0.58109   ,
             "lag": 1.4586 
        }
    },
        
    # Parâmetros L2 --- siprec +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    
     {
        "idSimul": "L2-SAC-F1-SIPREC",
        "config": {
            "id": "L2",
            "modelo": SACSMA,
            "fobj": "NSE",
            "chuva": "SIPREC",
            "periodo": [datetime(2011, 12, 22, 15, 0, 0), datetime(2016, 1, 1, 0, 0, 0)],
        },
        "parametros": {
             "UZTWM": 98.913  ,
             "UZFWM": 149.322  ,
               "UZK": 0.689373 ,
             "ZPERC": 44.672  ,
              "REXP": 1.003720 ,
             "LZTWM": 10.015  ,
             "LZFSM": 259.910  ,
             "LZFPM": 999.684  ,
              "LZSK": 0.010000 ,
              "LZPK": 0.003529 ,
             "PFREE": 0.351263 ,
              "SIDE": 0.999982 ,
             "PCTIM": 0.060983 ,
             "ADIMP": 0.034773 ,
             "Kprop": 0.569396 ,
               "lag": 1.0
        }
    },
    {
        "idSimul": "L2-SAC-F2-SIPREC",
        "config": {
            "id": "L2",
            "modelo": SACSMA,
            "fobj": "DesvResid",
            "chuva": "SIPREC",
            "periodo": [datetime(2011, 12, 22, 15, 0, 0), datetime(2016, 1, 1, 0, 0, 0)],
        },
        "parametros": {
            "UZTWM": 10.001 ,
            "UZFWM": 149.990 ,
              "UZK": 0.630558 ,
            "ZPERC": 45.089 ,
             "REXP": 1.000321 ,
            "LZTWM": 10.000 ,
            "LZFSM": 399.979  ,
            "LZFPM": 999.996 ,
             "LZSK": 0.010000 ,
             "LZPK": 0.004888 ,
            "PFREE": 0.799988 ,
             "SIDE": 0.999999 ,
            "PCTIM": 0.068237 ,
            "ADIMP": 0.005581 ,
            "Kprop": 0.564016 ,
              "lag": 0.7
        }
    },
    {
        "idSimul": "L2-IPH-F1-SIPREC",
        "config": {
            "id": "L2",
            "modelo": IPH2,
            "fobj": "NSE",
            "chuva": "SIPREC",
            "periodo": [datetime(2011, 12, 22, 15, 0, 0), datetime(2016, 1, 1, 0, 0, 0)],
        },
        "parametros": {
            "RMAX": 11.9364     ,
              "Io": 21.2098    ,
             "fIb": 0.10423731 ,
               "H": 0.017513   ,
            "alfa": 1.613768   ,
            "Ksup": 12.9352    ,
            "Ksub": 799.9632    ,
            "Aimp": 0.088002   ,
              "NH": 3.00  ,
           "Kprop": 0.579734   ,
             "lag": 1.0
              
        }
    },
    {
        "idSimul": "L2-IPH-F2-SIPREC",
        "config": {
            "id": "L2",
            "modelo": IPH2,
            "fobj": "DesvResid",
            "chuva": "SIPREC",
            "periodo": [datetime(2011, 12, 22, 15, 0, 0), datetime(2016, 1, 1, 0, 0, 0)],
        },
        "parametros": {
            "RMAX": 6.3708  ,
              "Io": 169.5594  ,
             "fIb": 0.00653143  , 
               "H": 0.000282   ,
            "alfa": 0.197967   ,
            "Ksup": 10.5838  ,
            "Ksub": 799.9998  ,
            "Aimp": 0.191720      , 
              "NH": 2.98  ,
           "Kprop": 0.578314   ,
             "lag": 1.4
        }
    },
        
        
        
    # Parâmetros L3 --- pluviometro +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    {
        "idSimul": "L3-SAC-F1-PLU",
        "config": {
            "id": "L3",
            "modelo": SACSMA,
            "fobj": "NSE",
            "chuva": "pluviometros",
            "periodo": [datetime(2013, 9, 8, 10, 0, 0), datetime(2016, 1, 1, 0, 0, 0)],
        },
        "parametros": {
            "UZTWM": 22.372162   ,
            "UZFWM": 47.070599   ,
              "UZK": 0.197736    ,
            "ZPERC": 172.248284  ,
             "REXP": 2.382680    ,
            "LZTWM": 10.021978  ,
            "LZFSM": 59.246167  ,
            "LZFPM": 862.716382 ,
             "LZSK": 0.186759    ,
             "LZPK": 0.006746    ,
            "PFREE": 0.301484    ,
             "SIDE": 0.999982    ,
            "PCTIM": 0.006931    ,
            "ADIMP": 0.176639    ,
            "Kprop": 0.124135    ,
              "lag": -0.438588
        }
    },
    {
        "idSimul": "L3-SAC-F2-PLU",
        "config": {
            "id": "L3",
            "modelo": SACSMA,
            "fobj": "DesvResid",
            "chuva": "pluviometros",
            "periodo": [datetime(2013, 9, 8, 10, 0, 0), datetime(2016, 1, 1, 0, 0, 0)],
        },
        "parametros": {
            "UZTWM": 10.003   ,
            "UZFWM": 14.622  ,
              "UZK": 0.749894  ,
            "ZPERC": 349.950  ,
             "REXP": 4.038436   ,
            "LZTWM": 10.007   ,
            "LZFSM": 80.768   ,
            "LZFPM": 996.651  ,
             "LZSK": 0.185909  ,
             "LZPK": 0.006631  ,
            "PFREE": 0.560075  ,
             "SIDE": 0.999998  ,
            "PCTIM": 0.017650  ,
            "ADIMP": 0.168376  ,
            "Kprop": 0.122676   ,
              "lag": -0.3  
        }
    },
    {
        "idSimul": "L3-IPH-F1-PLU",
        "config": {
            "id": "L3",
            "modelo": IPH2,
            "fobj": "NSE",
            "chuva": "pluviometros",
            "periodo": [datetime(2013, 9, 8, 10, 0, 0), datetime(2016, 1, 1, 0, 0, 0)],
        },
        "parametros": {
            "RMAX": 19.981517  ,
              "Io": 29.337701  ,
             "fIb": 0.117365   ,
               "H": 0.208319   ,
            "alfa": 0.100128   ,
            "Ksup": 18.419015  ,
            "Ksub": 799.658411 ,
            "Aimp": 0.278225   ,
              "NH": 6.082502
        }
    },
    {
        "idSimul": "L3-IPH-F2-PLU",
        "config": {
            "id": "L3",
            "modelo": IPH2,
            "fobj": "DesvResid",
            "chuva": "pluviometros",
            "periodo": [datetime(2013, 9, 8, 10, 0, 0), datetime(2016, 1, 1, 0, 0, 0)],
        },
        "parametros": {
            "RMAX": 11.7361    ,
              "Io": 29.3101    ,
             "fIb": 0.11686286 ,
               "H": 0.209849   ,
            "alfa": 0.100003   ,
            "Ksup": 18.3964    ,
            "Ksub": 800.0000   ,
            "Aimp": 0.230370   ,
              "NH": 6.02 
        }
    },
    
    # Parâmetros L3 --- siprec +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    
    {
        "idSimul": "L3-SAC-F1-SIPREC",
        "config": {
            "id": "L3",
            "modelo": SACSMA,
            "fobj": "NSE",
            "chuva": "SIPREC",
            "periodo": [datetime(2013, 9, 8, 10, 0, 0), datetime(2016, 1, 1, 0, 0, 0)],
        },
        "parametros": {
            "UZTWM": 10.000  ,
            "UZFWM": 149.999  ,
              "UZK": 0.702465  ,
            "ZPERC": 5.000  ,
             "REXP": 1.000060  ,
            "LZTWM": 499.999 ,
            "LZFSM": 399.998 ,
            "LZFPM": 1000.000 ,
             "LZSK": 0.010000  ,
             "LZPK": 0.002828  ,
            "PFREE": 0.799994  ,
             "SIDE": 0.999999  ,
            "PCTIM": 0.100000  ,
            "ADIMP": 0.000000  ,
            "Kprop": 0.237501  ,
              "lag": 1.1
        }
    },
    {
        "idSimul": "L3-SAC-F2-SIPREC",
        "config": {
            "id": "L3",
            "modelo": SACSMA,
            "fobj": "DesvResid",
            "chuva": "SIPREC",
            "periodo": [datetime(2013, 9, 8, 10, 0, 0), datetime(2016, 1, 1, 0, 0, 0)],
        },
        "parametros": {
            "UZTWM": 10.000   ,
            "UZFWM": 62.937 ,
              "UZK": 0.589533  ,
            "ZPERC": 5.000  ,
             "REXP": 4.999687   ,
            "LZTWM": 499.988  ,
            "LZFSM": 5.054   ,
            "LZFPM": 999.989  ,
             "LZSK": 0.010053  ,
             "LZPK": 0.001674  ,
            "PFREE": 0.720234  ,
             "SIDE": 0.999977  ,
            "PCTIM": 0.099994  ,
            "ADIMP": 0.000004  ,
            "Kprop": 0.341241   ,
              "lag": 2.0
        }
    },
    {
        "idSimul": "L3-IPH-F1-SIPREC",
        "config": {
            "id": "L3",
            "modelo": IPH2,
            "fobj": "NSE",
            "chuva": "SIPREC",
            "periodo": [datetime(2013, 9, 8, 10, 0, 0), datetime(2016, 1, 1, 0, 0, 0)],
        },
        "parametros": {
            "RMAX": 0.1000  ,
              "Io": 299.8147  ,
             "fIb": 0.19997452 ,
               "H": 0.014517  ,
            "alfa": 19.951787  ,
            "Ksup": 20.0967  ,
            "Ksub": 799.9997  ,
            "Aimp": 0.400000   ,
              "NH": 8.94
        }
    },
    {
        "idSimul": "L3-IPH-F2-SIPREC",
        "config": {
            "id": "L3",
            "modelo": IPH2,
            "fobj": "DesvResid",
            "chuva": "SIPREC",
            "periodo": [datetime(2013, 9, 8, 10, 0, 0), datetime(2016, 1, 1, 0, 0, 0)],
        },
        "parametros": {
            "RMAX": 0.1000   ,
              "Io": 35.2790  ,
             "fIb": 0.19999340 ,
               "H": 0.000010  ,
            "alfa": 19.982554  ,
            "Ksup": 19.7719  ,
            "Ksub": 788.7787  ,
            "Aimp": 0.399999   ,
              "NH": 7.90
        }
    },
    
    
    
    # Parâmetros P1 --- pluviometro +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    #{
        #"idSimul": "P1-SAC-F1-PLU",
        #"config": {
            #"id": "P1",
            #"modelo": SACSMA,
            #"fobj": "NSE",
            #"chuva": "pluviometros",
            #"periodo": [datetime(2014, 2, 5, 2, 0, 0), datetime(2017, 1, 1, 0, 0, 0)]
        #},
        #"parametros": {
            #"UZTWM": 299.978 , 
            #"UZFWM": 37.626  ,
              #"UZK": 0.117570, 
            #"ZPERC": 5.882   ,
             #"REXP": 1.000312, 
            #"LZTWM": 225.258 , 
            #"LZFSM": 55.413  ,
            #"LZFPM": 698.432 ,
             #"LZSK": 0.186241, 
             #"LZPK": 0.004934, 
            #"PFREE": 0.271737, 
             #"SIDE": 0.999996, 
            #"PCTIM": 0.051520, 
            #"ADIMP": 0.244270, 
            #"Kprop": 0.267261, 
              #"lag": 3.0 #6.5 
        #}
    #},        
    
    #{
        #"idSimul": "P1-SAC-F2-PLU",
        #"config": {
            #"id": "P1",
            #"modelo": SACSMA,
            #"fobj": "DesvResid",
            #"chuva": "pluviometros",
            #"periodo": [datetime(2014, 2, 5, 2, 0, 0), datetime(2017, 1, 1, 0, 0, 0)],
        #},
        #"parametros": {
            #"UZTWM": 300.000    ,
            #"UZFWM": 106.427    ,
              #"UZK": 0.749996   ,
            #"ZPERC": 106.074    ,
             #"REXP": 1.000015   ,
            #"LZTWM": 351.012    ,
            #"LZFSM": 58.866     ,
            #"LZFPM": 963.096    ,
             #"LZSK": 0.171028   ,
             #"LZPK": 0.004815   ,
            #"PFREE": 0.002902   ,
             #"SIDE": 1.000000   ,
            #"PCTIM": 0.048958   ,
            #"ADIMP": 0.300000   ,
            #"Kprop": 0.249839   ,
              #"lag": 3.0 #6.2 
        #}
    #},
    
    {
        "idSimul": "P1-SAC-KGE-PLU",
        "config": {
            "id": "P1",
            "modelo": SACSMA,
            "fobj": "NSE-NSE_LOG-BIAS",
            "chuva": "pluviometros",
            "periodo": [datetime(2014, 2, 5, 2, 0, 0), datetime(2017, 1, 1, 0, 0, 0)]
        },
        "parametros": {
            'UZTWM':   12.56564501,
            'UZFWM':   74.44066559,
            'UZK':      0.35371456,
            'ZPERC':  189.99533010,
            'REXP':     2.91171610,
            'LZTWM':  101.96073038,
            'LZFSM':  102.21387072,
            'LZFPM':  451.05538060,
            'LZSK':     0.09876586,
            'LZPK':     0.01242916,
            'PFREE':    0.36975003,
            'SIDE':     0.96376194,
            'PCTIM':    0.00050291,
            'ADIMP':    0.20689788,
            'Kprop':    0.16994424,
            'lag':      1.72782660
        }
    },        
      
        
    #{
        #"idSimul": "P1-IPH-F1-PLU",
        #"config": {
            #"id": "P1",
            #"modelo": IPH2,
            #"fobj": "NSE",
            #"chuva": "pluviometros",
            #"periodo": [datetime(2014, 2, 5, 2, 0, 0), datetime(2017, 1, 1, 0, 0, 0)],
        #},
        #"parametros": {
            #"RMAX": 19.9999    ,
              #"Io": 69.6487    ,
             #"fIb": 0.00342479 ,
               #"H": 0.346467   ,
            #"alfa": 0.100001   ,
            #"Ksup": 5.0271     ,
            #"Ksub": 799.9924   ,
            #"Aimp": 0.092242  ,
              #"NH": 11.89 
        #}
    #},  

    #{
        #"idSimul": "P1-IPH-F2-PLU",
        #"config": {
            #"id": "P1",
            #"modelo": IPH2,
            #"fobj": "DesvResid",
            #"chuva": "pluviometros",
            #"periodo": [datetime(2014, 2, 5, 2, 0, 0), datetime(2017, 1, 1, 0, 0, 0)],
        #},
        #"parametros": {
            #"RMAX": 19.9999  ,
              #"Io": 38.0471 ,
             #"fIb": 0.00372670 ,
               #"H": 0.644442  ,
            #"alfa": 0.100074   ,
            #"Ksup": 5.3973 ,
            #"Ksub": 799.9899 ,
            #"Aimp": 0.085583  ,
              #"NH": 12.38 
        #}
    #},
 
    {
        "idSimul": "P1-IPH-KGE-PLU",
        "config": {
            "id": "P1",
            "modelo": IPH2,
            "fobj": "NSE-NSE_LOG-BIAS",
            "chuva": "pluviometros",
            "periodo": [datetime(2014, 2, 5, 2, 0, 0), datetime(2017, 1, 1, 0, 0, 0)],
        },
        "parametros": {
           'RMAX': 18.84931997,
            'Io': 14.22083177,
            'fIb': 0.19579322,
            'H': 0.26255685,
            'alfa': 0.10425387,
            'Ksup': 22.62804445,
            'Ksub': 798.76872923,
            'Aimp': 0.02466765,
            'NH': 5.66490632
        }
    },  
   
 {
        "idSimul": "P1-IPH-RMSEI-PLU",
        "config": {
            "id": "P1",
            "modelo": IPH2,
            "fobj": "NSE-NSE_LOG-BIAS",
            "chuva": "pluviometros",
            "periodo": [datetime(2014, 2, 5, 2, 0, 0), datetime(2017, 1, 1, 0, 0, 0)],
        },
        "parametros": {
            'RMAX': 17.36829643,
            'Io': 12.88638829,
            'fIb': 0.19823390,
            'H': 0.49014683,
            'alfa': 0.10369960,
            'Ksup': 12.65878036,
            'Ksub': 799.80772682,
            'Aimp': 0.03411942,
            'NH': 6.88061412
        }
    },  
    # Parâmetros P1 --- siprec +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    
    #{
        #"idSimul": "P1-SAC-F1-SIPREC",
        #"config": {
            #"id": "P1",
            #"modelo": SACSMA,
            #"fobj": "NSE",
            #"chuva": "SIPREC",
            #"periodo": [datetime(2014, 2, 5, 2, 0, 0), datetime(2017, 1, 1, 0, 0, 0)]
        #},
        #"parametros": {
            #"UZTWM":  111.529,
            #"UZFWM":   44.531,
            #"UZK":   0.100001,
            #"ZPERC":   36.043,
            #"REXP":  1.389114,
            #"LZTWM":  462.052,
            #"LZFSM":   24.064,
            #"LZFPM":  594.018,
            #"LZSK":  0.224855,
            #"LZPK":  0.004895,
            #"PFREE": 0.115482,
            #"SIDE":  1.000000,
            #"PCTIM": 0.067370,
            #"ADIMP": 0.196649,
            #"Kprop": 0.264054,
            #"lag":        5.8
        #}
    #},

 #{
        #"idSimul": "P1-SAC-F2-SIPREC",
        #"config": {
            #"id": "P1",
            #"modelo": SACSMA,
            #"fobj": "DesvResid",
            #"chuva": "SIPREC",
            #"periodo": [datetime(2014, 2, 5, 2, 0, 0), datetime(2017, 1, 1, 0, 0, 0)],
        #},
        #"parametros": {
            #"UZTWM":  111.940,
            #"UZFWM":   43.224, 
              #"UZK": 0.100000,
            #"ZPERC":   98.367,
             #"REXP": 2.244226,
            #"LZTWM":  360.761,
            #"LZFSM":   15.993,
            #"LZFPM":  763.784,
             #"LZSK": 0.224349,
             #"LZPK": 0.004506,
            #"PFREE": 0.000687,
             #"SIDE": 1.000000,
            #"PCTIM": 0.072102,
            #"ADIMP": 0.179204,
            #"Kprop": 0.262473,
              #"lag": 5.8
        #}
    #},

     {
        "idSimul": "P1-SAC-KGE-SIPREC",
        "config": {
            "id": "P1",
            "modelo": SACSMA,
            "fobj": "NSE-NSE_LOG-BIAS",
            "chuva": "SIPREC",
            "periodo": [datetime(2014, 2, 5, 2, 0, 0), datetime(2017, 1, 1, 0, 0, 0)]
        },
       "parametros": {
            'UZTWM': 11.01936521,
            'UZFWM': 65.46107935,
            'UZK': 0.39675375,
            'ZPERC': 181.76040756,
            'REXP': 3.07120677,
            'LZTWM': 70.57563981,
            'LZFSM': 244.78150982,
            'LZFPM': 787.42856012,
            'LZSK': 0.11375326,
            'LZPK': 0.01035477,
            'PFREE': 0.51779090,
            'SIDE': 0.72366973,
            'PCTIM': 0.01141659,
            'ADIMP': 0.17839115,
            'Kprop': 0.16200457,
            'lag': 1.96949290        }
    },

#MODELO ARLAN
      {
        "idSimul": "P1-SAC-KGE-CASC",
        "config": {
            "id": "P1",
            "modelo": SACSMA_CASCATA,
            "fobj": "NS-NSE_LOG-BIAS",
            "chuva": "pluviometros",
            "periodo": [datetime(2014, 2, 5, 2, 0, 0), datetime(2017, 1, 1, 0, 0, 0)]
        },
       "parametros": {
            'UZTWM': 46.04026762,
            'UZFWM': 77.27363911,
            'UZK': 0.49110167,
            'ZPERC': 196.76306139,
            'REXP': 1.05743571,
            'LZTWM': 66.57744256,
            'LZFSM': 37.84081664,
            'LZFPM': 336.41515944,
            'LZSK': 0.09917740,
            'LZPK': 0.00980612,
            'PFREE': 0.33732497,
            'SIDE': 0.99948560,
            'PCTIM': 0.02585641,
            'ADIMP': 0.11466680,
            'k': 0.23502060,
            'n': 2.41076647        }
    },
    # IPH siprec
    #{
        #"idSimul": "P1-IPH-F1-SIPREC",
        #"config": {
            #"id": "P1",
            #"modelo": IPH2,
            #"fobj": "NSE",
            #"chuva": "SIPREC",
            #"periodo": [datetime(2014, 2, 5, 2, 0, 0), datetime(2017, 1, 1, 0, 0, 0)],
        #},
        #"parametros": {
            #"RMAX":    19.887655 ,
              #"Io":    51.865484 ,
             #"fIb":    0.002826  ,
               #"H":    0.621479  ,
            #"alfa":    0.338171  ,
            #"Ksup":    4.470388  ,
            #"Ksub":    798.316286,
            #"Aimp":    0.144622  ,
              #"NH":    13.300044
        #}
    #},
   
    #{
        #"idSimul": "P1-IPH-F2-SIPREC",
        #"config": {
            #"id": "P1",
            #"modelo": IPH2,
            #"fobj": "DesvResid",
            #"chuva": "SIPREC",
            #"periodo": [datetime(2014, 2, 5, 2, 0, 0), datetime(2017, 1, 1, 0, 0, 0)],
        #},
        #"parametros": {
            #"RMAX":    20.0000,
              #"Io":    19.1021,
             #"fIb": 0.08770284,
               #"H":   0.549240,
            #"alfa":   0.100000,
            #"Ksup":     5.8993,
            #"Ksub":   800.0000,
            #"Aimp":   0.165782,
              #"NH":      14.36
        #}
    #},
    
    #{
        #"idSimul": "P1-IPH-MOCOM-SIPREC",
        #"config": {
            #"id": "P1",
            #"modelo": IPH2,
            #"fobj": "NSE-NSE_LOG-BIAS",
            #"chuva": "SIPREC",
            #"periodo": [datetime(2014, 2, 5, 2, 0, 0), datetime(2017, 1, 1, 0, 0, 0)],
        #},
        #"parametros": {
            #'RMAX': 19.74947838,   
              #'Io': 14.00881540,   
             #'fIb': 0.19915298,     
               #'H': 0.33551617,  
            #'alfa': 0.17432655,   
            #'Ksup': 12.39815643,   
            #'Ksub': 799.51820535,   
            #'Aimp': 0.01274375,     
              #'NH': 7.71248370 
        #}        ,
        #"observacoes":{
            #'1': 'chuva do siprec deve ser corrigida por fator'
        #}
    #},

        
    # SMAP -------------------------------------------
 {
        "idSimul": "P1-SMAP-KGE-PLU",
        "config": {
            "id": "P1",
            "modelo": SMAP,
            "fobj": "KGE-NSE_LOG-ERRV",
            "chuva": "pluviometros",
            "periodo": [datetime(2014, 2, 5, 2, 0, 0), datetime(2017, 1, 1, 0, 0, 0)],
        },
        "parametros": {
             'Sat': 59.7663446, 
              'AI': 0.50629165,               
            'CAPC': 0.35149839,
            'Crec': 1.49482775,            
             'kkt': 41.48230515,
             'k2t': 0.04144926,              
              'tc': 0.57980708,
              'pc': 0.73338832
       }
    },
        
 {      #usa siprec corrigido!!!
        "idSimul": "P1-SMAP-KGE-SIPREC",
        "config": {
            "id": "P1",
            "modelo": SMAP,
            "fobj": "KGE-NSE_LOG-ERRV",
            "chuva": "siprec",
            "periodo": [datetime(2014, 2, 5, 2, 0, 0), datetime(2017, 1, 1, 0, 0, 0)],
        },
        "parametros": {
             'Sat': 540.9540191, 
              'AI': 0.52655318,               
            'CAPC': 0.41231699,
            'Crec': 10.22033038,            
             'kkt': 26.83398645,
             'k2t': 0.45909563,              
              'tc': 0.13374994,
              'pc': 0.59352623
       },
        "observacoes":{
            '1': 'chuva do siprec deve ser corrigida por fator'
        }
    }, 
    
    # Teste ------------------------------------------- 

 #{
        #"idSimul": "P1-SMAP-MOCOM-PLU-TESTE",
        #"config": {
            #"id": "P1",
            #"modelo": SMAP,
            #"fobj": "NSE-NSE_LOG-BIAS",
            #"chuva": "pluviometros",
            #"periodo": [datetime(2014, 2, 5, 2, 0, 0), datetime(2017, 1, 1, 0, 0, 0)],
        #},
        #"parametros": {
             #'k2t': 5.68008052, 
             #'kkt': 0.97835057, 
              #'AI': 2.57868914, 
             #'Sat': 1228.68307596, 
            #'Crec': 19.93109668, 
            #'CAPC': 0.49855142, 
              #'tc': 0.01399704
       #}
    #},   

    #{
        #"idSimul": "P1-SMAP-MOCOM-SIPREC",
        #"config": {
            #"id": "P1",
            #"modelo": SMAP,
            #"fobj": "NSE-NSE_LOG-BIAS",
            #"chuva": "siprec",
            #"periodo": [datetime(2014, 2, 5, 2, 0, 0), datetime(2017, 1, 1, 0, 0, 0)],
        #},
        #"parametros": {
             #'k2t': 5.68008052, 
             #'kkt': 0.97835057, 
              #'AI': 2.57868914, 
             #'Sat': 1228.68307596, 
            #'Crec': 19.93109668, 
            #'CAPC': 0.49855142, 
              #'tc': 0.01399704
       #}

    #},

    # Parâmetros RMC1 - pluviômetro ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    {
        "idSimul": "RMC1-SAC-F1-PLU",
        "config": {
            "id": "RMC1",
            "modelo": SACSMA,
            "fobj": "NSE",
            "chuva": "pluviometros",
            "periodo": [datetime(2002, 7, 1, 1, 0, 0), datetime(2013, 12, 31, 23, 0, 0)],
        },
        "parametros": {
            "UZTWM": 10.000   ,
            "UZFWM": 102.471   ,
              "UZK": 0.144256   ,
            "ZPERC": 306.893   ,
             "REXP": 4.999994   ,
            "LZTWM": 10.000   ,
            "LZFSM": 23.060   ,
            "LZFPM": 216.538  ,
             "LZSK": 0.010005   ,
             "LZPK": 0.017500   ,
            "PFREE": 0.799998   ,
             "SIDE": 1.000000   ,
            "PCTIM": 0.099999   ,
            "ADIMP": 0.000002   ,
            "Kprop": 0.052528   ,
              "lag": 0.2
        }
    },
    {
        "idSimul": "RMC1-SAC-F2-PLU",
        "config": {
            "id": "RMC1",
            "modelo": SACSMA,
            "fobj": "DesvResid",
            "chuva": "pluviometros",
            "periodo": [datetime(2002, 7, 1, 1, 0, 0), datetime(2013, 12, 31, 23, 0, 0)],
        },
        "parametros": {
            "UZTWM": 10.000   ,
            "UZFWM": 87.475 ,
              "UZK": 0.128670   ,
            "ZPERC": 349.987  ,
             "REXP": 4.999960    ,
            "LZTWM": 10.000   ,
            "LZFSM": 29.019   ,
            "LZFPM": 201.376  ,
             "LZSK": 0.010001   ,
             "LZPK": 0.015401   ,
            "PFREE": 0.799999   ,
             "SIDE": 1.000000   ,
            "PCTIM": 0.099999   ,
            "ADIMP": 0.000000   ,
            "Kprop": 0.056092    ,
              "lag": 1.2
        }
    },      
    {
        "idSimul": "RMC1-IPH-F1-PLU",
        "config": {
            "id": "RMC1",
            "modelo": IPH2,
            "fobj": "NSE",
            "chuva": "pluviometros",
            "periodo": [datetime(2002, 7, 1, 1, 0, 0), datetime(2013, 12, 31, 23, 0, 0)],
        },
        "parametros": {
            "RMAX": 8.6243  ,
              "Io": 249.7517  ,
             "fIb": 0.01555793 ,
               "H": 0.004853   ,
            "alfa": 3.166497   ,
            "Ksup": 51.2366  ,
            "Ksub": 799.2578  ,
            "Aimp": 0.206297   ,
              "NH": 22.73
        } 
    },
    {
        "idSimul": "RMC1-IPH-F2-PLU",
        "config": {
            "id": "RMC1",
            "modelo": IPH2,
            "fobj": "DesvResid",
            "chuva": "pluviometros",
            "periodo": [datetime(2002, 7, 1, 1, 0, 0), datetime(2013, 12, 31, 23, 0, 0)],
        },
        
        "parametros": {
            "RMAX": 7.3233  ,
              "Io": 244.0041  ,
             "fIb": 0.02017490 ,
               "H": 0.000836   ,
            "alfa": 0.388709   ,
            "Ksup": 55.8332  ,
            "Ksub": 799.9998  ,
            "Aimp": 0.201145   ,
              "NH": 23.44
        }
        
    },
        
    # Parâmetros RMC1 --- siprec +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    
    {
        "idSimul": "RMC1-SAC-F1-SIPREC",
        "config": {
            "id": "RMC1",
            "modelo": SACSMA,
            "fobj": "NSE",
            "chuva": "SIPREC",
            "periodo": [datetime(2002, 7, 1, 1, 0, 0), datetime(2013, 12, 31, 23, 0, 0)],
        },
        "parametros": {
            "UZTWM": 10.000    ,
            "UZFWM": 5.000   ,
              "UZK": 0.254907   ,
            "ZPERC": 241.898    ,
             "REXP": 1.885161   ,
            "LZTWM": 10.000    ,
            "LZFSM": 45.392    ,
            "LZFPM": 511.944   ,
             "LZSK": 0.227362   ,
             "LZPK": 0.011880   ,
            "PFREE": 0.800000   ,
             "SIDE": 1.000000   ,
            "PCTIM": 0.100000   ,
            "ADIMP": 0.047714   ,
            "Kprop": 0.045338   ,
              "lag": 2.1
        }
    },
    {
        "idSimul": "RMC1-SAC-F2-SIPREC",
        "config": {
            "id": "RMC1",
            "modelo": SACSMA,
            "fobj": "DesvResid",
            "chuva": "SIPREC",
            "periodo": [datetime(2002, 7, 1, 1, 0, 0), datetime(2013, 12, 31, 23, 0, 0)],
        },
        "parametros": {
            "UZTWM": 10.000    ,
            "UZFWM": 5.014      ,
              "UZK": 0.225218    ,
            "ZPERC": 252.730     ,
             "REXP": 1.186374     ,
            "LZTWM": 10.000     ,
            "LZFSM": 42.767     ,
            "LZFPM": 397.088    ,
             "LZSK": 0.196655    ,
             "LZPK": 0.011577    ,
            "PFREE": 0.799998    ,
             "SIDE": 0.999999    ,
            "PCTIM": 0.099998    ,
            "ADIMP": 0.036457    ,
            "Kprop": 0.049561     ,
              "lag": 2.8
        }
    },      
    {
        "idSimul": "RMC1-IPH-F1-SIPREC",
        "config": {
            "id": "RMC1",
            "modelo": IPH2,
            "fobj": "NSE",
            "chuva": "SIPREC",
            "periodo": [datetime(2002, 7, 1, 1, 0, 0), datetime(2013, 12, 31, 23, 0, 0)],
        },
        "parametros": {
            "RMAX": 1.7501     ,
              "Io": 42.1073    ,
             "fIb": 0.09763711  ,
               "H": 0.002942   ,
            "alfa": 0.100001    ,
            "Ksup": 101.2525   ,
            "Ksub": 799.9999   ,
            "Aimp": 0.114412   ,
              "NH": 21.84
        } 
    },
    {
        "idSimul": "RMC1-IPH-F2-SIPREC",
        "config": {
            "id": "RMC1",
            "modelo": IPH2,
            "fobj": "DesvResid",
            "chuva": "SIPREC",
            "periodo": [datetime(2002, 7, 1, 1, 0, 0), datetime(2013, 12, 31, 23, 0, 0)],
        },
        
        "parametros": {
            "RMAX": 0.5700     ,
              "Io": 51.0484    ,
             "fIb": 0.04647025 ,
               "H": 0.002110   ,
            "alfa": 0.100002    ,
            "Ksup": 131.3826    ,
            "Ksub": 799.9912    ,
            "Aimp": 0.051829   ,
              "NH": 19.45
        }
        
    },
    
    # Parâmetros RMC2 --- pluviometro +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    {
        "idSimul": "RMC2-SAC-F1-PLU",
        "config": {
            "id": "RMC2",
            "modelo": SACSMA,
            "fobj": "NSE",
            "chuva": "pluviometros",
            "periodo": [datetime(2005, 1, 26, 16, 0, 0), datetime(2009, 12, 31, 23, 0, 0)],
        },
        "parametros": {
            "UZTWM": 10.000   ,
            "UZFWM": 33.682   ,
              "UZK": 0.749995    ,
            "ZPERC": 11.643   ,
             "REXP": 1.647026    ,
            "LZTWM": 10.000   ,
            "LZFSM": 21.665   ,
            "LZFPM": 134.178  ,
             "LZSK": 0.349962    ,
             "LZPK": 0.035415    ,
            "PFREE": 0.799999    ,
             "SIDE": 0.999999    ,
            "PCTIM": 0.099988    ,
            "ADIMP": 0.065060    ,
            "Kprop": 0.658193    ,
              "lag": 1.0
        }
    },
    {
        "idSimul": "RMC2-SAC-F2-PLU",
        "config": {
            "id": "RMC2",
            "modelo": SACSMA,
            "fobj": "DesvResid",
            "chuva": "pluviometros",
            "periodo": [datetime(2005, 1, 26, 16, 0, 0), datetime(2009, 12, 31, 23, 0, 0)],
        },
        "parametros": {
            "UZTWM": 10.000   ,
            "UZFWM": 33.787   ,
              "UZK": 0.749991    ,
            "ZPERC": 7.668  ,
             "REXP": 2.611353     ,
            "LZTWM": 10.000   ,
            "LZFSM": 33.191   ,
            "LZFPM": 171.149  ,
             "LZSK": 0.349913    ,
             "LZPK": 0.037765    ,
            "PFREE": 0.799999    ,
             "SIDE": 1.000000    ,
            "PCTIM": 0.100000    ,
            "ADIMP": 0.063280    ,
            "Kprop": 0.661972     ,
              "lag": 1.0
        }
    },      
    {
        "idSimul": "RMC2-IPH-F1-PLU",
        "config": {
            "id": "RMC2",
            "modelo": IPH2,
            "fobj": "NSE",
            "chuva": "pluviometros",
            "periodo": [datetime(2005, 1, 26, 16, 0, 0), datetime(2009, 12, 31, 23, 0, 0)],
        },
        "parametros": {
            "RMAX": 3.1288 , 
              "Io": 88.8028 ,
             "fIb": 0.03275283 ,
               "H": 0.001253   ,
            "alfa": 0.100019   ,
            "Ksup": 5.5211, 
            "Ksub": 799.9968 ,
            "Aimp": 0.373479   ,
              "NH": 2.23
        } 
    },
    {
        "idSimul": "RMC2-IPH-F2-PLU",
        "config": {
            "id": "RMC2",
            "modelo": IPH2,
            "fobj": "DesvResid",
            "chuva": "pluviometros",
            "periodo": [datetime(2005, 1, 26, 16, 0, 0), datetime(2009, 12, 31, 23, 0, 0)],
        },
        
        "parametros": {
            "RMAX": 3.8399  ,
              "Io": 61.9978 ,
             "fIb": 0.05447404,
               "H": 0.015700  ,
            "alfa": 0.100005  ,
            "Ksup": 5.2326    ,
            "Ksub": 799.9922  ,
            "Aimp": 0.399999  ,
              "NH": 2.20
        }      
    },
        
    # Parâmetros RMC2 --- siprec +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    
    {
        "idSimul": "RMC2-SAC-F1-SIPREC",
        "config": {
            "id": "RMC2",
            "modelo": SACSMA,
            "fobj": "NSE",
            "chuva": "SIPREC",
            "periodo": [datetime(2005, 1, 26, 16, 0, 0), datetime(2009, 12, 31, 23, 0, 0)],
        },
        "parametros": {
            "UZTWM": 10.000   ,
            "UZFWM": 63.519  ,
              "UZK": 0.749999    ,
            "ZPERC": 42.377  ,
             "REXP": 4.999583    ,
            "LZTWM": 10.000   ,
            "LZFSM": 60.290   ,
            "LZFPM": 15.158  ,
             "LZSK": 0.051769    ,
             "LZPK": 0.049969    ,
            "PFREE": 0.799999    ,
             "SIDE": 0.999999    ,
            "PCTIM": 0.100000    ,
            "ADIMP": 0.226827    ,
            "Kprop": 0.598141    ,
              "lag": 0.8
        }
    },
    {
        "idSimul": "RMC2-SAC-F2-SIPREC",
        "config": {
            "id": "RMC2",
            "modelo": SACSMA,
            "fobj": "DesvResid",
            "chuva": "SIPREC",
            "periodo": [datetime(2005, 1, 26, 16, 0, 0), datetime(2009, 12, 31, 23, 0, 0)],
        },
        "parametros": {
            "UZTWM": 10.000  ,
            "UZFWM": 73.643 ,
              "UZK": 0.749999   ,
            "ZPERC": 40.734 ,
             "REXP": 4.998992    ,
            "LZTWM": 10.000  ,
            "LZFSM": 60.609  ,
            "LZFPM": 14.118 ,
             "LZSK": 0.054945   ,
             "LZPK": 0.049885   ,
            "PFREE": 0.800000   ,
             "SIDE": 0.999999   ,
            "PCTIM": 0.100000   ,
            "ADIMP": 0.223246   ,
            "Kprop": 0.602295    ,
              "lag": 1.2
        }
    },      
    {
        "idSimul": "RMC2-IPH-F1-SIPREC",
        "config": {
            "id": "RMC2",
            "modelo": IPH2,
            "fobj": "NSE",
            "chuva": "SIPREC",
            "periodo": [datetime(2005, 1, 26, 16, 0, 0), datetime(2009, 12, 31, 23, 0, 0)],
        },
        "parametros": {
            "RMAX": 0.1000  , 
              "Io": 53.2373 ,
             "fIb": 0.01596785,
               "H": 0.010646  ,
            "alfa": 1.077264  ,
            "Ksup": 6.0012 , 
            "Ksub": 799.8762 ,
            "Aimp": 0.399998  ,
              "NH": 2.25
        } 
    },
    {
        "idSimul": "RMC2-IPH-F2-SIPREC",
        "config": {
            "id": "RMC2",
            "modelo": IPH2,
            "fobj": "DesvResid",
            "chuva": "SIPREC",
            "periodo": [datetime(2005, 1, 26, 16, 0, 0), datetime(2009, 12, 31, 23, 0, 0)],
        },
        
        "parametros": {
            "RMAX": 0.1000 ,
              "Io": 113.4306 ,
             "fIb": 0.05632633,
               "H": 0.000010 ,
            "alfa": 19.961093 ,
            "Ksup": 3.7528 ,
            "Ksub": 316.7090 ,
            "Aimp": 0.400000  ,
              "NH": 2.82
        }      
    },
    
    # Parâmetros RMC3 --- pluviometro +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    
    {
        "idSimul": "RMC3-SAC-F1-PLU",
        "config": {
            "id": "RMC3",
            "modelo": SACSMA,
            "fobj": "NSE",
            "chuva": "pluviometros",
            "periodo": [datetime(2005, 1, 8, 16, 0, 0), datetime(2010, 12, 31, 23, 0, 0)],
        },
        "parametros": {
            "UZTWM": 10.000  ,
            "UZFWM": 149.982  ,
              "UZK": 0.178007    ,
            "ZPERC": 34.164  ,
             "REXP": 1.000029    ,
            "LZTWM": 10.000  ,
            "LZFSM": 399.996  ,
            "LZFPM": 999.981  ,
             "LZSK": 0.010001    ,
             "LZPK": 0.006132    ,
            "PFREE": 0.799988    ,
             "SIDE": 0.999998    ,
            "PCTIM": 0.099999    ,
            "ADIMP": 0.102583    ,
            "Kprop": 0.804432    ,
              "lag": 0.7 
        }
    },
    {
        "idSimul": "RMC3-SAC-F2-PLU",
        "config": {
            "id": "RMC3",
            "modelo": SACSMA,
            "fobj": "DesvResid",
            "chuva": "pluviometros",
            "periodo": [datetime(2005, 1, 8, 16, 0, 0), datetime(2010, 12, 31, 23, 0, 0)],
        },
        "parametros": {
            "UZTWM": 10.000  ,
            "UZFWM": 149.992  ,
              "UZK": 0.189642 ,
            "ZPERC": 31.813  ,
             "REXP": 1.000107 ,
            "LZTWM": 10.001  ,
            "LZFSM": 399.968  ,
            "LZFPM": 999.990  ,
             "LZSK": 0.010003 ,
             "LZPK": 0.006963 ,
            "PFREE": 0.799992 ,
             "SIDE": 0.999999 ,
            "PCTIM": 0.100000 ,
            "ADIMP": 0.100962 ,
            "Kprop": 0.807036  ,
              "lag": 1.2 
        }
    },      
    {
        "idSimul": "RMC3-IPH-F1-PLU",
        "config": {
            "id": "RMC3",
            "modelo": IPH2,
            "fobj": "NSE",
            "chuva": "pluviometros",
            "periodo": [datetime(2005, 1, 8, 16, 0, 0), datetime(2010, 12, 31, 23, 0, 0)],
        },
        "parametros": {
            "RMAX": 1.9714   , 
              "Io": 51.3965  ,
             "fIb": 0.05334719 ,
               "H": 0.256044   ,
            "alfa": 0.100001   ,
            "Ksup": 1.5318  , 
            "Ksub": 799.9959  ,
            "Aimp": 0.251255   ,
              "NH": 1.99 
        } 
    },
    {
        "idSimul": "RMC3-IPH-F2-PLU",
        "config": {
            "id": "RMC3",
            "modelo": IPH2,
            "fobj": "DesvResid",
            "chuva": "pluviometros",
            "periodo": [datetime(2005, 1, 8, 16, 0, 0), datetime(2010, 12, 31, 23, 0, 0)],
        },
        
        "parametros": {
            "RMAX": 0.7377    ,
              "Io": 64.1106   ,
             "fIb": 0.04242429,
               "H": 0.162674  ,
            "alfa": 0.100003  ,
            "Ksup": 1.6093    ,
            "Ksub": 799.9946 ,
            "Aimp": 0.248739  ,
              "NH": 2.34 
        }      
    },
        
    # Parâmetros RMC3 --- siprec +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    
     
    {
        "idSimul": "RMC3-SAC-F1-SIPREC",
        "config": {
            "id": "RMC3",
            "modelo": SACSMA,
            "fobj": "NSE",
            "chuva": "SIPREC",
            "periodo": [datetime(2005, 1, 8, 16, 0, 0), datetime(2010, 12, 31, 23, 0, 0)],
        },
        "parametros": {
            "UZTWM": 10.000   ,
            "UZFWM": 150.000    ,
              "UZK": 0.283451    ,
            "ZPERC": 29.838    ,
             "REXP": 1.000095    ,
            "LZTWM": 10.000    ,
            "LZFSM": 399.998  ,
            "LZFPM": 999.997  ,
             "LZSK": 0.010001    ,
             "LZPK": 0.006735    ,
            "PFREE": 0.799998    ,
             "SIDE": 1.000000    ,
            "PCTIM": 0.100000    ,
            "ADIMP": 0.154215    ,
            "Kprop": 0.799932    ,
              "lag": 0.9
        }
    },
    {
        "idSimul": "RMC3-SAC-F2-SIPREC",
        "config": {
            "id": "RMC3",
            "modelo": SACSMA,
            "fobj": "DesvResid",
            "chuva": "SIPREC",
            "periodo": [datetime(2005, 1, 8, 16, 0, 0), datetime(2010, 12, 31, 23, 0, 0)],
        },
        "parametros": {
            "UZTWM": 10.000 ,
            "UZFWM": 149.762  ,
              "UZK": 0.279315 ,
            "ZPERC": 30.609   ,
             "REXP": 1.001167 ,
            "LZTWM": 10.001  ,
            "LZFSM": 399.859  ,
            "LZFPM": 999.916  ,
             "LZSK": 0.010002 ,
             "LZPK": 0.006498 ,
            "PFREE": 0.799985 ,
             "SIDE": 0.999998 ,
            "PCTIM": 0.100000 ,
            "ADIMP": 0.155131 ,
            "Kprop": 0.798960  ,
              "lag": 0.8
        }
    },      
    {
        "idSimul": "RMC3-IPH-F1-SIPREC",
        "config": {
            "id": "RMC3",
            "modelo": IPH2,
            "fobj": "NSE",
            "chuva": "SIPREC",
            "periodo": [datetime(2005, 1, 8, 16, 0, 0), datetime(2010, 12, 31, 23, 0, 0)],
        },
        "parametros": {
            "RMAX": 0.8714  , 
              "Io": 261.8830  ,
             "fIb": 0.04278992 ,
               "H": 0.001081  ,
            "alfa": 18.415591  ,
            "Ksup": 1.7167 , 
            "Ksub": 799.9971 ,
            "Aimp": 0.311243   ,
              "NH": 1.86
        } 
    },
    {
        "idSimul": "RMC3-IPH-F2-SIPREC",
        "config": {
            "id": "RMC3",
            "modelo": IPH2,
            "fobj": "DesvResid",
            "chuva": "SIPREC",
            "periodo": [datetime(2005, 1, 8, 16, 0, 0), datetime(2010, 12, 31, 23, 0, 0)],
        },
        
        "parametros": {
            "RMAX": 0.1000 ,
              "Io": 292.0670 ,
             "fIb": 0.11094316,
               "H": 0.301236 ,
            "alfa": 19.610382 ,
            "Ksup": 2.0480 ,
            "Ksub": 799.9883 ,
            "Aimp": 0.343740  ,
              "NH": 2.11
        }      
    },
    
    # Parâmetros RMC4 --- pluviometro +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    
    
   {
        "idSimul": "RMC4-SAC-F1-PLU",
        "config": {
            "id": "RMC4",
            "modelo": SACSMA,
            "fobj": "NSE",
            "chuva": "pluviometros",
            "periodo": [datetime(2007, 7, 23, 0, 0, 0), datetime(2015, 6, 29, 0, 0, 0)],
        },
        "parametros": {
            "UZTWM": 10.169   ,
            "UZFWM": 39.996   ,
              "UZK": 0.100008     ,
            "ZPERC": 349.971   ,
             "REXP": 4.995838     ,
            "LZTWM": 14.969    ,
            "LZFSM": 14.929     ,
            "LZFPM": 165.022   ,
             "LZSK": 0.349953     ,
             "LZPK": 0.011610     ,
            "PFREE": 0.624939     ,
             "SIDE": 0.999996     ,
            "PCTIM": 0.099987     ,
            "ADIMP": 0.000008     ,
            "Kprop": 0.024829     ,
              "lag": 8.0
        }
    },

    {
        "idSimul": "RMC4-SAC-F2-PLU",
        "config": {
            "id": "RMC4",
            "modelo": SACSMA,
            "fobj": "DesvResid",
            "chuva": "pluviometros",
            "periodo": [datetime(2007, 7, 23, 0, 0, 0), datetime(2015, 6, 29, 0, 0, 0)],
        },
        "parametros": {
            "UZTWM": 10.058  ,
            "UZFWM": 39.850  ,
              "UZK": 0.100000 ,
            "ZPERC": 349.998  ,
             "REXP": 4.999967 ,
            "LZTWM": 11.586   ,
            "LZFSM": 14.358   ,
            "LZFPM": 170.183  ,
             "LZSK": 0.349998 ,
             "LZPK": 0.011815 ,
            "PFREE": 0.672607 ,
             "SIDE": 1.000000 ,
            "PCTIM": 0.100000 ,
            "ADIMP": 0.000001 ,
            "Kprop": 0.024766  ,
              "lag": 7.8
        }
    },  
    {
        "idSimul": "RMC4-IPH-F1-PLU",
        "config": {
            "id": "RMC4",
            "modelo": IPH2,
            "fobj": "NSE",
            "chuva": "pluviometros",
            "periodo": [datetime(2007, 7, 23, 0, 0, 0), datetime(2015, 6, 29, 0, 0, 0)],
        },
        "parametros": {
            "RMAX": 11.681295  , 
              "Io": 13.546472  ,
             "fIb": 0.008940   ,
               "H": 0.841269   ,
            "alfa": 0.236369   ,
            "Ksup": 103.297760 , 
            "Ksub": 799.998053 ,
            "Aimp": 0.399985   ,
              "NH": 88.817696
        } 
    },
    {
        "idSimul": "RMC4-IPH-F2-PLU",
        "config": {
            "id": "RMC4",
            "modelo": IPH2,
            "fobj": "DesvResid",
            "chuva": "pluviometros",
            "periodo": [datetime(2007, 7, 23, 0, 0, 0), datetime(2015, 6, 29, 0, 0, 0)],
        },
        
        "parametros": {
            "RMAX": 9.0773  ,
              "Io": 79.1438 ,
             "fIb": 0.00647246,
               "H": 0.004590  ,
            "alfa": 0.100001 ,
            "Ksup": 118.7739 ,
            "Ksub": 651.7455 ,
            "Aimp": 0.056043  ,
              "NH": 92.93
        }      

    },
        
    # Parâmetros RMC4 --- siprec +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    
    {
        "idSimul": "RMC4-SAC-F1-SIPREC",
        "config": {
            "id": "RMC4",
            "modelo": SACSMA,
            "fobj": "NSE",
            "chuva": "SIPREC",
            "periodo": [datetime(2007, 7, 23, 0, 0, 0), datetime(2015, 6, 29, 0, 0, 0)],
        },
        "parametros": {
            "UZTWM": 10.000   ,
            "UZFWM": 47.206  ,
              "UZK": 0.145579     ,
            "ZPERC": 21.744   ,
             "REXP": 2.357924     ,
            "LZTWM": 10.000    ,
            "LZFSM": 6.423     ,
            "LZFPM": 193.474   ,
             "LZSK": 0.021749     ,
             "LZPK": 0.011240     ,
            "PFREE": 0.799999     ,
             "SIDE": 0.999999     ,
            "PCTIM": 0.100000     ,
            "ADIMP": 0.000000     ,
            "Kprop": 0.024967     ,
              "lag": 10.1
        }
    },

    {
        "idSimul": "RMC4-SAC-F2-SIPREC",
        "config": {
            "id": "RMC4",
            "modelo": SACSMA,
            "fobj": "DesvResid",
            "chuva": "SIPREC",
            "periodo": [datetime(2007, 7, 23, 0, 0, 0), datetime(2015, 6, 29, 0, 0, 0)],
        },
        "parametros": {
            "UZTWM": 10.000  ,
            "UZFWM": 40.668 ,
              "UZK": 0.152946  ,
            "ZPERC": 72.499  ,
             "REXP": 1.088089  ,
            "LZTWM": 10.000   ,
            "LZFSM": 16.705   ,
            "LZFPM": 263.979  ,
             "LZSK": 0.031631  ,
             "LZPK": 0.002501  ,
            "PFREE": 0.799988  ,
             "SIDE": 0.999999  ,
            "PCTIM": 0.100000  ,
            "ADIMP": 0.000011  ,
            "Kprop": 0.023477   ,
              "lag": 10.0
        }
    },  
    {
        "idSimul": "RMC4-IPH-F1-SIPREC",
        "config": {
            "id": "RMC4",
            "modelo": IPH2,
            "fobj": "NSE",
            "chuva": "SIPREC",
            "periodo": [datetime(2007, 7, 23, 0, 0, 0), datetime(2015, 6, 29, 0, 0, 0)],
        },
        "parametros": {
            "RMAX": 0.2098   , 
              "Io": 46.9373  ,
             "fIb": 0.00533212 ,
               "H": 0.071294   ,
            "alfa": 0.100052  ,
            "Ksup": 136.5410  , 
            "Ksub": 799.9905  ,
            "Aimp": 0.071359   ,
              "NH": 80.00
        } 
    },
    {
        "idSimul": "RMC4-IPH-F2-SIPREC",
        "config": {
            "id": "RMC4",
            "modelo": IPH2,
            "fobj": "DesvResid",
            "chuva": "SIPREC",
            "periodo": [datetime(2007, 7, 23, 0, 0, 0), datetime(2015, 6, 29, 0, 0, 0)],
        },
        
        "parametros": {
            "RMAX": 0.2482  ,
              "Io": 48.5938 ,
             "fIb": 0.00536624,
               "H": 0.079253  ,
            "alfa": 0.154150 ,
            "Ksup": 132.4285 ,
            "Ksub": 799.9925 ,
            "Aimp": 0.052097  ,
              "NH": 79.68
        }      

    },
        
        
    # Parâmetros IG1 --- pluviometro +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    {
        "idSimul": "IG1-SAC-F1-PLU",
        "config": {
            "id": "IG1",
            "modelo": SACSMA,
            "fobj": "NSE",
            "chuva": "pluviometros",
            "periodo": [datetime(2011, 1, 1, 0, 0, 0), datetime(2015, 12, 31, 0, 0, 0)],
        },
        "parametros": {
            "UZTWM": 10.003   ,
            "UZFWM": 75.929  ,
              "UZK": 0.749891      ,
            "ZPERC": 307.011   ,
             "REXP": 4.764904      ,
            "LZTWM": 48.591    ,
            "LZFSM": 54.884     ,
            "LZFPM": 215.751   ,
             "LZSK": 0.349987      ,
             "LZPK": 0.037125      ,
            "PFREE": 0.693692      ,
             "SIDE": 0.500006      ,
            "PCTIM": 0.000044      ,
            "ADIMP": 0.101911      ,
            "Kprop": 0.148970      ,
              "lag": -0.2
        } 
    },
    {
        "idSimul": "IG1-SAC-F2-PLU",
        "config": {
            "id": "IG1",
            "modelo": SACSMA,
            "fobj": "DesvResid",
            "chuva": "pluviometros",
            "periodo": [datetime(2011, 1, 1, 0, 0, 0), datetime(2015, 12, 31, 0, 0, 0)],
        },
        "parametros": {
            "UZTWM": 10.451  ,
            "UZFWM": 75.465 ,
              "UZK": 0.749939  ,
            "ZPERC": 260.144  ,
             "REXP": 2.141598  ,
            "LZTWM": 70.590   ,
            "LZFSM": 37.262   ,
            "LZFPM": 138.692  ,
             "LZSK": 0.349991  ,
             "LZPK": 0.040150  ,
            "PFREE": 0.637557  ,
             "SIDE": 0.500001  ,
            "PCTIM": 0.000001  ,
            "ADIMP": 0.104062  ,
            "Kprop": 0.150432   ,
              "lag": 0.5
        } 
    },  

    {
        "idSimul": "IG1-IPH-F1-PLU",
        "config": {
            "id": "IG1",
            "modelo": IPH2,
            "fobj": "NSE",
            "chuva": "pluviometros",
            "periodo": [datetime(2011, 1, 1, 0, 0, 0), datetime(2015, 12, 31, 0, 0, 0)],
        },
        "parametros": {
            "RMAX": 20.0000   , 
              "Io": 69.5411  ,
             "fIb": 0.02846557 ,
               "H": 0.047124   ,
            "alfa": 0.100012   ,
            "Ksup": 17.0433  , 
            "Ksub": 744.9146  ,
            "Aimp": 0.000844   ,
              "NH": 1.53 ,
           "Kprop": 0.997668  ,
             "lag": 0.5
        } 
    },
    {
        "idSimul": "IG1-IPH-F2-PLU",
        "config": {
            "id": "IG1",
            "modelo": IPH2,
            "fobj": "DesvResid",
            "chuva": "pluviometros",
            "periodo": [datetime(2011, 1, 1, 0, 0, 0), datetime(2015, 12, 31, 0, 0, 0)],
        },
        
        "parametros": {
            "RMAX": 20.0000  ,
              "Io": 106.1670  ,
             "fIb": 0.02539537 ,
               "H": 0.006586   ,
            "alfa": 0.100005   ,
            "Ksup": 18.6320  ,
            "Ksub": 799.9988  ,
            "Aimp": 0.064894 ,
              "NH": 4.01 ,
           "Kprop": 0.222966,
             "lag": 0.1 
        }      

    },
        
        
    # Parâmetros IG1 --- siprec +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    
    {
        "idSimul": "IG1-SAC-F1-SIPREC",
        "config": {
            "id": "IG1",
            "modelo": SACSMA,
            "fobj": "NSE",
            "chuva": "SIPREC",
            "periodo": [datetime(2011, 1, 1, 0, 0, 0), datetime(2015, 12, 31, 0, 0, 0)],
        },
        "parametros": {
            "UZTWM": 19.127     ,
            "UZFWM": 149.905     ,
              "UZK": 0.359240      ,
            "ZPERC": 15.978     ,
             "REXP": 4.999091      ,
            "LZTWM": 16.426     ,
            "LZFSM": 185.334    ,
            "LZFPM": 999.809   ,
             "LZSK": 0.074162      ,
             "LZPK": 0.003482      ,
            "PFREE": 0.799960      ,
             "SIDE": 0.999267      ,
            "PCTIM": 0.000005      ,
            "ADIMP": 0.000006      ,
            "Kprop": 0.578690      ,
              "lag": 0.3
        } 
    },
    {
        "idSimul": "IG1-SAC-F2-SIPREC",
        "config": {
            "id": "IG1",
            "modelo": SACSMA,
            "fobj": "DesvResid",
            "chuva": "SIPREC",
            "periodo": [datetime(2011, 1, 1, 0, 0, 0), datetime(2015, 12, 31, 0, 0, 0)],
        },
        "parametros": {
            "UZTWM": 16.819    ,
            "UZFWM": 149.983   ,
              "UZK": 0.351805 ,
            "ZPERC": 11.608   ,
             "REXP": 4.999489 ,
            "LZTWM": 15.210   ,
            "LZFSM": 241.975  ,
            "LZFPM": 999.791  ,
             "LZSK": 0.073613 ,
             "LZPK": 0.003652 ,
            "PFREE": 0.799997 ,
             "SIDE": 0.999991 ,
            "PCTIM": 0.000004 ,
            "ADIMP": 0.000001 ,
            "Kprop": 0.576250  ,
              "lag": 0.2
        } 
    },  

    {
        "idSimul": "IG1-IPH-F1-SIPREC",
        "config": {
            "id": "IG1",
            "modelo": IPH2,
            "fobj": "NSE",
            "chuva": "SIPREC",
            "periodo": [datetime(2011, 1, 1, 0, 0, 0), datetime(2015, 12, 31, 0, 0, 0)],
        },
        "parametros": {
            "RMAX": 7.4126      , 
              "Io": 68.5537     ,
             "fIb": 0.004101437 ,
               "H": 0.051229    ,
            "alfa": 0.100026    ,
            "Ksup": 17.0428      , 
            "Ksub": 799.9173    ,
            "Aimp": 0.070447    ,
              "NH": 2.36          ,
           "Kprop": 0.999916    ,
             "lag": -0.0
        } 
    },
    {
        "idSimul": "IG1-IPH-F2-SIPREC",
        "config": {
            "id": "IG1",
            "modelo": IPH2,
            "fobj": "DesvResid",
            "chuva": "SIPREC",
            "periodo": [datetime(2011, 1, 1, 0, 0, 0), datetime(2015, 12, 31, 0, 0, 0)],
        },
        
        "parametros": {
            "RMAX": 8.7993       ,
              "Io": 67.9780     ,
             "fIb": 0.00487259 ,
               "H": 0.040767   ,
            "alfa": 0.100001   ,
            "Ksup": 17.3174    ,
            "Ksub": 799.9967   ,
            "Aimp": 0.093541    ,
              "NH": 2.01       ,
           "Kprop": 0.999918   ,
             "lag": -0.0
        }      

    },
# Parâmetros R1 --- pluviometro +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    {
        "idSimul": "R1-SAC-F1-PLU",
        "config": {
            "id": "R1",
            "modelo": SACSMA,
            "fobj": "NSE",
            "chuva": "pluviometros",
            "periodo": [datetime(2011, 1, 1, 0, 0, 0), datetime(2015, 12, 31, 0, 0, 0)],
        },
        "parametros": {
            "UZTWM": 62.306     ,
            "UZFWM": 10.542      ,
              "UZK": 0.749970      ,
            "ZPERC": 9.998       ,
             "REXP": 1.004080      ,
            "LZTWM": 499.656     ,
            "LZFSM": 71.270      ,
            "LZFPM": 999.392     ,
             "LZSK": 0.315721      ,
             "LZPK": 0.003427      ,
            "PFREE": 0.229428      ,
             "SIDE": 0.817615      ,
            "PCTIM": 0.017566      ,
            "ADIMP": 0.084657      ,
            "Kprop": 0.210205      ,
              "lag": 2.2
        } 
    },
    {
        "idSimul": "R1-SAC-F2-PLU",
        "config": {
            "id": "R1",
            "modelo": SACSMA,
            "fobj": "DesvResid",
            "chuva": "pluviometros",
            "periodo": [datetime(2011, 1, 1, 0, 0, 0), datetime(2015, 12, 31, 0, 0, 0)],
        },
        "parametros": {
            "UZTWM": 45.867   ,
            "UZFWM": 73.980   ,
              "UZK": 0.750000  ,
            "ZPERC": 62.681   ,
             "REXP": 1.000021  ,
            "LZTWM": 499.978  ,
            "LZFSM": 69.099   ,
            "LZFPM": 999.873  ,
             "LZSK": 0.279053  ,
             "LZPK": 0.002709  ,
            "PFREE": 0.278900  ,
             "SIDE": 0.812294  ,
            "PCTIM": 0.017458  ,
            "ADIMP": 0.037058  ,
            "Kprop": 0.246252   ,
              "lag": 1.8
        } 
    },  

    {
        "idSimul": "R1-IPH-F1-PLU",
        "config": {
            "id": "R1",
            "modelo": IPH2,
            "fobj": "NSE",
            "chuva": "pluviometros",
            "periodo": [datetime(2011, 1, 1, 0, 0, 0), datetime(2015, 12, 31, 0, 0, 0)],
        },
        "parametros": {
            "RMAX": 19.0916    , 
              "Io": 22.9095    ,
             "fIb": 0.16033934  ,
               "H": 0.000036   ,
            "alfa": 0.100000   ,
            "Ksup": 11.3928    , 
            "Ksub": 799.9988   ,
            "Aimp": 0.023954    ,
              "NH": 6.03
  
        } 
    },
    {
        "idSimul": "R1-IPH-F2-PLU",
        "config": {
            "id": "R1",
            "modelo": IPH2,
            "fobj": "DesvResid",
            "chuva": "pluviometros",
            "periodo": [datetime(2011, 1, 1, 0, 0, 0), datetime(2015, 12, 31, 0, 0, 0)],
        },
        
        "parametros": {
            "RMAX": 19.0921    ,
              "Io": 22.9095    ,
             "fIb": 0.16033894 ,
               "H": 0.000036   ,
            "alfa": 0.100001   ,
            "Ksup": 11.3859    ,
            "Ksub": 799.9953   ,
            "Aimp": 0.023622   ,
              "NH": 5.82        
         
        }      

    },
        
        
    # Parâmetros R1 --- siprec +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    
    {
        "idSimul": "R1-SAC-F1-SIPREC",
        "config": {
            "id": "R1",
            "modelo": SACSMA,
            "fobj": "NSE",
            "chuva": "SIPREC",
            "periodo": [datetime(2011, 1, 1, 0, 0, 0), datetime(2015, 12, 31, 0, 0, 0)],
        },
        "parametros": {
            "UZTWM": 10.000     ,
            "UZFWM": 16.481     ,
              "UZK": 0.100010       ,
            "ZPERC": 40.777     ,
             "REXP": 1.000021        ,
            "LZTWM": 499.998     ,
            "LZFSM": 7.742      ,
            "LZFPM": 999.992    ,
             "LZSK": 0.349923       ,
             "LZPK": 0.001788       ,
            "PFREE": 0.759667       ,
             "SIDE": 0.999999       ,
            "PCTIM": 0.047403       ,
            "ADIMP": 0.114819       ,
            "Kprop": 0.212307       ,
              "lag": 2.0
        } 
    },
    {
        "idSimul": "R1-SAC-F2-SIPREC",
        "config": {
            "id": "R1",
            "modelo": SACSMA,
            "fobj": "DesvResid",
            "chuva": "SIPREC",
            "periodo": [datetime(2011, 1, 1, 0, 0, 0), datetime(2015, 12, 31, 0, 0, 0)],
        },
        "parametros": {
            "UZTWM": 10.000   ,
            "UZFWM": 17.163   ,
              "UZK": 0.100017  ,
            "ZPERC": 38.014    ,
             "REXP": 1.000044  ,
            "LZTWM": 499.988   ,
            "LZFSM": 6.723     ,
            "LZFPM": 999.971   ,
             "LZSK": 0.349824  ,
             "LZPK": 0.002182  ,
            "PFREE": 0.736768  ,
             "SIDE": 0.999997  ,
            "PCTIM": 0.054571  ,
            "ADIMP": 0.086520  ,
            "Kprop": 0.212679  ,
              "lag": 1.6
        } 
    },  

    {
        "idSimul": "R1-IPH-F1-SIPREC",
        "config": {
            "id": "R1",
            "modelo": IPH2,
            "fobj": "NSE",
            "chuva": "SIPREC",
            "periodo": [datetime(2011, 1, 1, 0, 0, 0), datetime(2015, 12, 31, 0, 0, 0)],
        },
        "parametros": {
            "RMAX": 9.7699      , 
              "Io": 17.3827     ,
             "fIb": 0.19999992  ,
               "H": 0.148162   ,
            "alfa": 0.100000    ,
            "Ksup": 8.7735      , 
            "Ksub": 799.9994    ,
            "Aimp": 0.103317    ,
              "NH": 6.01      
           
        } 
    },
    {
        "idSimul": "R1-IPH-F2-SIPREC",
        "config": {
            "id": "R1",
            "modelo": IPH2,
            "fobj": "DesvResid",
            "chuva": "SIPREC",
            "periodo": [datetime(2011, 1, 1, 0, 0, 0), datetime(2015, 12, 31, 0, 0, 0)],
        },
        
        "parametros": {
            "RMAX": 9.6681    ,
              "Io": 17.3804   ,
             "fIb": 0.19999857,
               "H": 0.149296  ,
            "alfa": 0.100000  ,
            "Ksup": 8.7986    ,
            "Ksub": 799.9995  ,
            "Aimp": 0.104081  ,
              "NH": 6.22 
      
        }      

    },
    # Parâmetros IT1 --- pluviometro +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    {
        "idSimul": "IT1-SAC-F1-PLU",
        "config": {
            "id": "IT1",
            "modelo": SACSMA,
            "fobj": "NSE",
            "chuva": "pluviometros",
            "periodo": [datetime(2014, 2, 1, 0, 0, 0), datetime(2015, 12, 31, 0, 0, 0)],
        },
        "parametros": {
            "UZTWM": 12.995      ,
            "UZFWM": 9.044    ,
              "UZK": 0.741537    ,
            "ZPERC": 187.905    ,
             "REXP": 1.013657     ,
            "LZTWM": 80.473      ,
            "LZFSM": 35.473      ,
            "LZFPM": 999.989     ,
             "LZSK": 0.073032     ,
             "LZPK": 0.003138     ,
            "PFREE": 0.380427     ,
             "SIDE": 0.558538     ,
            "PCTIM": 0.011120     ,
            "ADIMP": 0.100720     ,
            "Kprop": 0.058930     ,
              "lag": 0.4
        } 
    },
    {
        "idSimul": "IT1-SAC-F2-PLU",
        "config": {
            "id": "IT1",
            "modelo": SACSMA,
            "fobj": "DesvResid",
            "chuva": "pluviometros",
            "periodo": [datetime(2014, 2, 1, 0, 0, 0), datetime(2015, 12, 31, 0, 0, 0)],
        },
        "parametros": {
            "UZTWM": 164.113   ,
            "UZFWM": 149.993   ,
              "UZK": 0.100022  ,
            "ZPERC": 349.948   ,
             "REXP": 1.000208  ,
            "LZTWM": 29.864    ,
            "LZFSM": 27.974    ,
            "LZFPM": 999.996   ,
             "LZSK": 0.083301  ,
             "LZPK": 0.002760  ,
            "PFREE": 0.698100  ,
             "SIDE": 0.592192  ,
            "PCTIM": 0.038068  ,
            "ADIMP": 0.052082  ,
            "Kprop": 0.059835   ,
              "lag": -0.3
        } 
    },  

    {
        "idSimul": "IT1-IPH-F1-PLU",
        "config": {
            "id": "IT1",
            "modelo": IPH2,
            "fobj": "NSE",
            "chuva": "pluviometros",
            "periodo": [datetime(2014, 2, 1, 0, 0, 0), datetime(2015, 12, 31, 0, 0, 0)],
        },
        "parametros": {
            "RMAX": 20.0000     , 
              "Io": 10.7066     ,
             "fIb": 0.15201674  ,
               "H": 0.738188    ,
            "alfa": 0.100000    ,
            "Ksup": 92.1302     , 
            "Ksub": 799.9999     ,
            "Aimp": 0.000100     ,
              "NH": 2.86
  
        } 
    },
    {
        "idSimul": "IT1-IPH-F2-PLU",
        "config": {
            "id": "IT1",
            "modelo": IPH2,
            "fobj": "DesvResid",
            "chuva": "pluviometros",
            "periodo": [datetime(2014, 2, 1, 0, 0, 0), datetime(2015, 12, 31, 0, 0, 0)],
        },
        
        "parametros": {
            "RMAX": 19.9999      ,
              "Io": 20.0300     ,
             "fIb": 0.19953534   ,
               "H": 0.032316    ,
            "alfa": 0.100001    ,
            "Ksup": 55.3586     ,
            "Ksub": 799.9992    ,
            "Aimp": 0.000100     ,
              "NH": 4.93   
        }      
    },
                
    # Parâmetros IT1 --- siprec +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    
    {
        "idSimul": "IT1-SAC-F1-SIPREC",
        "config": {
            "id": "IT1",
            "modelo": SACSMA,
            "fobj": "NSE",
            "chuva": "SIPREC",
            "periodo": [datetime(2014, 2, 1, 0, 0, 0), datetime(2015, 12, 31, 0, 0, 0)],
        },
        "parametros": {
            "UZTWM": 10.000      ,
            "UZFWM": 5.007      ,
              "UZK": 0.248001     ,
            "ZPERC": 278.419    ,
             "REXP": 1.138658     ,
            "LZTWM": 499.996    ,
            "LZFSM": 27.839     ,
            "LZFPM": 999.999    ,
             "LZSK": 0.050510     ,
             "LZPK": 0.001944     ,
            "PFREE": 0.726910     ,
             "SIDE": 0.999999     ,
            "PCTIM": 0.043269     ,
            "ADIMP": 0.296616     ,
            "Kprop": 0.042512     ,
              "lag": 0.0
        } 
    },
    {
        "idSimul": "IT1-SAC-F2-SIPREC",
        "config": {
            "id": "IT1",
            "modelo": SACSMA,
            "fobj": "DesvResid",
            "chuva": "SIPREC",
            "periodo": [datetime(2014, 2, 1, 0, 0, 0), datetime(2015, 12, 31, 0, 0, 0)],
        },
        "parametros": {
            "UZTWM": 18.329   ,
            "UZFWM": 46.262   ,
              "UZK": 0.104902  ,
            "ZPERC": 349.992   ,
             "REXP": 1.012174  ,
            "LZTWM": 10.000    ,
            "LZFSM": 6.889     ,
            "LZFPM": 572.617  ,
             "LZSK": 0.067964  ,
             "LZPK": 0.001582  ,
            "PFREE": 0.786400  ,
             "SIDE": 0.999989  ,
            "PCTIM": 0.063083  ,
            "ADIMP": 0.000001  ,
            "Kprop": 0.062518  ,
              "lag": -0.4
        } 
    },  

    {
        "idSimul": "IT1-IPH-F1-SIPREC",
        "config": {
            "id": "IT1",
            "modelo": IPH2,
            "fobj": "NSE",
            "chuva": "SIPREC",
            "periodo": [datetime(2014, 2, 1, 0, 0, 0), datetime(2015, 12, 31, 0, 0, 0)],
        },
        "parametros": {
            "RMAX": 13.5600     , 
              "Io": 19.3402     ,
             "fIb": 0.19690672  ,
               "H": 0.009697    ,
            "alfa": 0.100000    ,
            "Ksup": 52.1980     , 
            "Ksub": 800.0000    ,
            "Aimp": 0.043181    ,
              "NH": 8.96
           
        } 
    },
    {
        "idSimul": "IT1-IPH-F2-SIPREC",
        "config": {
            "id": "IT1",
            "modelo": IPH2,
            "fobj": "DesvResid",
            "chuva": "SIPREC",
            "periodo": [datetime(2014, 2, 1, 0, 0, 0), datetime(2015, 12, 31, 0, 0, 0)],
        },
        
        "parametros": {
            "RMAX": 14.5369    ,
              "Io": 19.3402    ,
             "fIb": 0.19690649 ,
               "H": 0.009697   ,
            "alfa": 0.100000   ,
            "Ksup": 52.0392    ,
            "Ksub": 799.9997   ,
            "Aimp": 0.043113   ,
              "NH": 8.89
      
        }      

    },
    
    # Parâmetros C1 --- pluviometro +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    {
        "idSimul": "C1-SAC-F1-PLU",
        "config": {
            "id": "C1",
            "modelo": SACSMA,
            "fobj": "NSE",
            "chuva": "pluviometros",
            "periodo": [datetime(2014, 5, 28, 0, 0, 0), datetime(2015, 12, 31, 0, 0, 0)],
        },
        "parametros": {
            "UZTWM": 11.504      ,
            "UZFWM": 16.920      ,
              "UZK": 0.667326    ,
            "ZPERC": 57.277      ,
             "REXP": 1.000017     ,
            "LZTWM": 74.233       ,
            "LZFSM": 34.399       ,
            "LZFPM": 223.570      ,
             "LZSK": 0.120981     ,
             "LZPK": 0.010609     ,
            "PFREE": 0.343661     ,
             "SIDE": 0.753445     ,
            "PCTIM": 0.000003     ,
            "ADIMP": 0.077525     ,
            "Kprop": 0.067598     ,
              "lag": -0.1
        } 
    },
    {
        "idSimul": "C1-SAC-F2-PLU",
        "config": {
            "id": "C1",
            "modelo": SACSMA,
            "fobj": "DesvResid",
            "chuva": "pluviometros",
            "periodo": [datetime(2014, 5, 28, 0, 0, 0), datetime(2015, 12, 31, 0, 0, 0)],
        },
        "parametros": {
            "UZTWM": 10.170    ,
            "UZFWM": 15.006    ,
              "UZK": 0.695673  ,
            "ZPERC": 168.553   ,
             "REXP": 1.479542  ,
            "LZTWM": 67.486    ,
            "LZFSM": 35.764    ,
            "LZFPM": 253.586   ,
             "LZSK": 0.114016  ,
             "LZPK": 0.010651  ,
            "PFREE": 0.339964  ,
             "SIDE": 0.728209  ,
            "PCTIM": 0.006704  ,
            "ADIMP": 0.148485  ,
            "Kprop": 0.064088   ,
              "lag": -0.3
        } 
    },  

    {
        "idSimul": "C1-IPH-F1-PLU",
        "config": {
            "id": "C1",
            "modelo": IPH2,
            "fobj": "NSE",
            "chuva": "pluviometros",
            "periodo": [datetime(2014, 5, 28, 0, 0, 0), datetime(2015, 12, 31, 0, 0, 0)],
        },
        "parametros": {
            "RMAX": 20.0000      , 
              "Io": 8.1901      ,
             "fIb": 0.19970084  ,
               "H": 0.637916    ,
            "alfa": 0.100001    ,
            "Ksup": 53.8960     , 
            "Ksub": 799.9777    ,
            "Aimp": 0.099218     ,
              "NH": 6.35
  
        } 
    },
    {
        "idSimul": "C1-IPH-F2-PLU",
        "config": {
            "id": "C1",
            "modelo": IPH2,
            "fobj": "DesvResid",
            "chuva": "pluviometros",
            "periodo": [datetime(2014, 5, 28, 0, 0, 0), datetime(2015, 12, 31, 0, 0, 0)],
        },
        
        "parametros": {
            "RMAX": 19.4551     ,
              "Io": 11.8165     ,
             "fIb": 0.18448541  ,
               "H": 0.000590    ,
            "alfa": 0.100001    ,
            "Ksup": 79.2921     ,
            "Ksub": 799.8664    ,
            "Aimp": 0.000100    ,
              "NH": 5.64         
        }      
    },
                
    # Parâmetros C1 --- siprec +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    
    {
        "idSimul": "C1-SAC-F1-SIPREC",
        "config": {
            "id": "C1",
            "modelo": SACSMA,
            "fobj": "NSE",
            "chuva": "SIPREC",
            "periodo": [datetime(2014, 5, 28, 0, 0, 0), datetime(2015, 12, 31, 0, 0, 0)],
        },
        "parametros": {
            "UZTWM": 43.857       ,
            "UZFWM": 5.001        ,
              "UZK": 0.253046      ,
            "ZPERC": 289.014     ,
             "REXP": 1.628038      ,
            "LZTWM": 500.000     ,
            "LZFSM": 60.727     ,
            "LZFPM": 999.998    ,
             "LZSK": 0.160204      ,
             "LZPK": 0.002100      ,
            "PFREE": 0.799998      ,
             "SIDE": 1.000000      ,
            "PCTIM": 0.100000      ,
            "ADIMP": 0.299999      ,
            "Kprop": 0.047990      ,
              "lag": -0.2
        } 
    },
    {
        "idSimul": "C1-SAC-F2-SIPREC",
        "config": {
            "id": "C1",
            "modelo": SACSMA,
            "fobj": "DesvResid",
            "chuva": "SIPREC",
            "periodo": [datetime(2014, 5, 28, 0, 0, 0), datetime(2015, 12, 31, 0, 0, 0)],
        },
        "parametros": {
            "UZTWM": 10.000   ,
            "UZFWM": 5.001     ,
              "UZK": 0.177539 ,
            "ZPERC": 231.790   ,
             "REXP": 1.243561 ,
            "LZTWM": 500.000  ,
            "LZFSM": 73.381   ,
            "LZFPM": 999.999  ,
             "LZSK": 0.157821 ,
             "LZPK": 0.001753 ,
            "PFREE": 0.781095 ,
             "SIDE": 0.999999 ,
            "PCTIM": 0.098543 ,
            "ADIMP": 0.172414 ,
            "Kprop": 0.052761 ,
              "lag": -0.4
        } 
    },  

    {
        "idSimul": "C1-IPH-F1-SIPREC",
        "config": {
            "id": "C1",
            "modelo": IPH2,
            "fobj": "NSE",
            "chuva": "SIPREC",
            "periodo": [datetime(2014, 5, 28, 0, 0, 0), datetime(2015, 12, 31, 0, 0, 0)],
        },
        "parametros": {
            "RMAX": 20.0000      , 
              "Io": 19.2461      ,
             "fIb": 0.16227457  ,
               "H": 0.174416    ,
            "alfa": 0.100001    ,
            "Ksup": 35.4468     , 
            "Ksub": 799.9975    ,
            "Aimp": 0.216682    ,
              "NH": 13.21
           
        } 
    },
    {
        "idSimul": "C1-IPH-F2-SIPREC",
        "config": {
            "id": "C1",
            "modelo": IPH2,
            "fobj": "DesvResid",
            "chuva": "SIPREC",
            "periodo": [datetime(2014, 5, 28, 0, 0, 0), datetime(2015, 12, 31, 0, 0, 0)],
        },
        
        "parametros": {
            "RMAX": 20.0000    ,
              "Io": 19.2461    ,
             "fIb": 0.16227344 ,
               "H": 0.174413   ,
            "alfa": 0.100000   ,
            "Ksup": 34.5744    ,
            "Ksub": 799.9945   ,
            "Aimp": 0.209954   ,
              "NH": 12.89
      
        }      

    },

# Parâmetros I1 --- pluviometro +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    {
        "idSimul": "I1-SAC-F1-PLU",
        "config": {
            "id": "I1",
            "modelo": SACSMA,
            "fobj": "NSE",
            "chuva": "pluviometros",
            "periodo": [datetime(2014, 2, 1, 0, 0, 0), datetime(2015, 12, 31, 0, 0, 0)],
        },
        "parametros": {
            "UZTWM": 67.146      ,
            "UZFWM": 5.001      ,
              "UZK": 0.748985    ,
            "ZPERC": 11.600    ,
             "REXP": 1.000039     ,
            "LZTWM": 79.585     ,
            "LZFSM": 126.011     ,
            "LZFPM": 249.259     ,
             "LZSK": 0.174484     ,
             "LZPK": 0.008934     ,
            "PFREE": 0.261374     ,
             "SIDE": 0.999705     ,
            "PCTIM": 0.000016     ,
            "ADIMP": 0.241978     ,
            "Kprop": 0.062982     ,
              "lag": 8.9
        } 
    },
    {
        "idSimul": "I1-SAC-F2-PLU",
        "config": {
            "id": "I1",
            "modelo": SACSMA,
            "fobj": "DesvResid",
            "chuva": "pluviometros",
            "periodo": [datetime(2014, 2, 1, 0, 0, 0), datetime(2015, 12, 31, 0, 0, 0)],
        },
        "parametros": {
            "UZTWM": 62.581    ,
            "UZFWM": 5.011     ,
              "UZK": 0.747446  ,
            "ZPERC": 11.248    ,
             "REXP": 1.000258  ,
            "LZTWM": 75.125    ,
            "LZFSM": 125.207   ,
            "LZFPM": 242.942   ,
             "LZSK": 0.177037  ,
             "LZPK": 0.009519  ,
            "PFREE": 0.285918  ,
             "SIDE": 0.999999  ,
            "PCTIM": 0.000000  ,
            "ADIMP": 0.237174  ,
            "Kprop": 0.063482   ,
              "lag": 8.8
        } 
    },  

    {
        "idSimul": "I1-IPH-F1-PLU",
        "config": {
            "id": "I1",
            "modelo": IPH2,
            "fobj": "NSE",
            "chuva": "pluviometros",
            "periodo": [datetime(2014, 2, 1, 0, 0, 0), datetime(2015, 12, 31, 0, 0, 0)],
        },
        "parametros": {
            "RMAX": 20.0000     , 
              "Io": 47.4034     ,
             "fIb": 0.00459023  ,
               "H": 0.178749    ,
            "alfa": 0.127498    ,
            "Ksup": 79.9909     , 
            "Ksub": 799.9949     ,
            "Aimp": 0.030489     ,
              "NH": 19.05
  
        } 
    },
    {
        "idSimul": "I1-IPH-F2-PLU",
        "config": {
            "id": "I1",
            "modelo": IPH2,
            "fobj": "DesvResid",
            "chuva": "pluviometros",
            "periodo": [datetime(2014, 2, 1, 0, 0, 0), datetime(2015, 12, 31, 0, 0, 0)],
        },
        
        "parametros": {
            "RMAX": 20.0000     ,
              "Io": 20.6680     ,
             "fIb": 0.01078561  ,
               "H": 0.508735    ,
            "alfa": 0.133537    ,
            "Ksup": 73.3435     ,
            "Ksub": 799.9978    ,
            "Aimp": 0.062027    ,
              "NH": 19.07
        }      
    },
                
    # Parâmetros I1 --- siprec +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    
    {
        "idSimul": "I1-SAC-F1-SIPREC",
        "config": {
            "id": "I1",
            "modelo": SACSMA,
            "fobj": "NSE",
            "chuva": "SIPREC",
            "periodo": [datetime(2014, 2, 1, 0, 0, 0), datetime(2015, 12, 31, 0, 0, 0)],
        },
        "parametros": {
            "UZTWM": 10.005       ,
            "UZFWM": 5.000    ,
              "UZK": 0.749888      ,
            "ZPERC": 12.520    ,
             "REXP": 1.000066      ,
            "LZTWM": 18.499    ,
            "LZFSM": 100.291     ,
            "LZFPM": 64.091    ,
             "LZSK": 0.166525      ,
             "LZPK": 0.016051      ,
            "PFREE": 0.799988      ,
             "SIDE": 1.000000      ,
            "PCTIM": 0.099988      ,
            "ADIMP": 0.222924      ,
            "Kprop": 0.050638      ,
              "lag": 8.2
        } 
    },
    {
        "idSimul": "I1-SAC-F2-SIPREC",
        "config": {
            "id": "I1",
            "modelo": SACSMA,
            "fobj": "DesvResid",
            "chuva": "SIPREC",
            "periodo": [datetime(2014, 2, 1, 0, 0, 0), datetime(2015, 12, 31, 0, 0, 0)],
        },
        "parametros": {
            "UZTWM": 10.000    ,
            "UZFWM": 25.766    ,
              "UZK": 0.749997  ,
            "ZPERC": 16.114    ,
             "REXP": 3.018896  ,
            "LZTWM": 10.000    ,
            "LZFSM": 113.956   ,
            "LZFPM": 46.668    ,
             "LZSK": 0.161743  ,
             "LZPK": 0.030340  ,
            "PFREE": 0.800000  ,
             "SIDE": 0.999999  ,
            "PCTIM": 0.099997  ,
            "ADIMP": 0.000001  ,
            "Kprop": 0.059612  ,
              "lag": 6.9
        } 
    },  

    {
        "idSimul": "I1-IPH-F1-SIPREC",
        "config": {
            "id": "I1",
            "modelo": IPH2,
            "fobj": "NSE",
            "chuva": "SIPREC",
            "periodo": [datetime(2014, 2, 1, 0, 0, 0), datetime(2015, 12, 31, 0, 0, 0)],
        },
        "parametros": {
            "RMAX": 6.9819    , 
              "Io": 97.2069   ,
             "fIb": 0.00174886  ,
               "H": 0.059387    ,
            "alfa": 0.170873    ,
            "Ksup": 69.2914   , 
            "Ksub": 799.9574   ,
            "Aimp": 0.354733    ,
              "NH": 26.76
           
        } 
    },
    {
        "idSimul": "I1-IPH-F2-SIPREC",
        "config": {
            "id": "I1",
            "modelo": IPH2,
            "fobj": "DesvResid",
            "chuva": "SIPREC",
            "periodo": [datetime(2014, 2, 1, 0, 0, 0), datetime(2015, 12, 31, 0, 0, 0)],
        },
        
        "parametros": {
            "RMAX": 3.0082     ,
              "Io": 123.0826   ,
             "fIb": 0.00111078 ,
               "H": 0.024253   ,
            "alfa": 0.406801   ,
            "Ksup": 73.1191    ,
            "Ksub": 799.9724   ,
            "Aimp": 0.228055   ,
              "NH": 26.84
      
        }      

    },

   # TBA: Parâmetros da simulação na bacia até Telêmaco Borba
   # Estes parâmetros serão usados para simular a vazão até Ribeirão das Antas (TBA), que posteriormente
   # será propagada para Cebolão e Jataizinho. 
   # OBS.: devido a falta de dados do siprec para calibrar, os parâmetros do siprec também foram calibrados com
   #       dados dos pluviômetros
   
    {
        "idSimul": "TBA-SAC-F1-PLU",
        "config": {
            "id": "TBA",
            "modelo": SACSMA,
            "fobj": "NSE",
            "chuva": "pluviometros",
            "periodo": [datetime(2013, 1, 1, 0, 0, 0), datetime(2017, 6, 25, 0, 0, 0)],
        },
        "parametros": {
            "UZTWM": 24.568    ,
            "UZFWM": 66.654    ,
              "UZK": 0.101793  ,
            "ZPERC": 349.889   ,
             "REXP": 1.015588  ,
            "LZTWM": 65.310    ,
            "LZFSM": 72.312    ,
            "LZFPM": 149.816   ,
             "LZSK": 0.076154  ,
             "LZPK": 0.006744  ,
            "PFREE": 0.589693  ,
             "SIDE": 1.000000  ,
            "PCTIM": 0.004214  ,
            "ADIMP": 0.048616  ,
            "Kprop": 0.089759  ,
              "lag": 3.4
        } 
    },
    {
        "idSimul": "TBA-SAC-F2-PLU",
        "config": {
            "id": "TBA",
            "modelo": SACSMA,
            "fobj": "DesvResid",
            "chuva": "pluviometros",
            "periodo": [datetime(2013, 1, 1, 0, 0, 0), datetime(2017, 6, 25, 0, 0, 0)],
        },
        "parametros": {
            "UZTWM": 24.318    ,
            "UZFWM": 66.729    ,
              "UZK": 0.102747  ,
            "ZPERC": 349.996   ,
             "REXP": 1.040742  ,
            "LZTWM": 57.832    ,
            "LZFSM": 70.944    ,
            "LZFPM": 147.297    ,
             "LZSK": 0.076539   ,
             "LZPK": 0.007379   ,
            "PFREE": 0.611928   ,
             "SIDE": 1.000000   ,
            "PCTIM": 0.005550   ,
            "ADIMP": 0.045018   ,
            "Kprop": 0.091071   ,
              "lag": 2.7
        } 
    },  

    {
        "idSimul": "TBA-IPH-F1-PLU",
        "config": {
            "id": "TBA",
            "modelo": IPH2,
            "fobj": "NSE",
            "chuva": "pluviometros",
            "periodo": [datetime(2013, 1, 1, 0, 0, 0), datetime(2017, 6, 25, 0, 0, 0)],
        },
        "parametros": {
            "RMAX": 19.9999    , 
              "Io": 32.0876    ,
             "fIb": 0.19999656 ,
               "H": 0.003817   ,
            "alfa": 0.100001   ,
            "Ksup": 43.8275    , 
            "Ksub": 528.9083   ,
            "Aimp": 0.049472    ,
              "NH": 29.66
    
  
        } 
    },
    {
        "idSimul": "TBA-IPH-F2-PLU",
        "config": {
            "id": "TBA", 
            "modelo": IPH2,
            "fobj": "DesvResid",
            "chuva": "pluviometros",
            "periodo": [datetime(2013, 1, 1, 0, 0, 0), datetime(2017, 6, 25, 0, 0, 0)],
        },
        
        "parametros": {
            "RMAX": 20.0000  ,
              "Io": 30.4705  ,
             "fIb": 0.19999988 ,
               "H": 0.005686  ,
            "alfa": 0.100000  ,
            "Ksup": 28.3341   ,
            "Ksub": 497.0249  ,
            "Aimp": 0.035386  ,
              "NH": 33.99
              
        }      
    },
        
    # TBA simulado pelo SIPREC ---------------------------------------------------------------------------------
    
    {
        "idSimul": "TBA-SAC-F1-SIPREC",
        "config": {
            "id": "TBA",
            "modelo": SACSMA,
            "fobj": "NSE",
            "chuva": "siprec",
            "periodo": [datetime(2013, 1, 1, 0, 0, 0), datetime(2017, 6, 25, 0, 0, 0)],
        },
        "parametros": {
            "UZTWM": 10.002   ,
            "UZFWM": 149.966   ,
              "UZK": 0.100617  ,
            "ZPERC": 349.732   ,
             "REXP": 1.005196  ,
            "LZTWM": 10.000   ,
            "LZFSM": 399.997   ,
            "LZFPM": 999.999   ,
             "LZSK": 0.100828  ,
             "LZPK": 0.002928  ,
            "PFREE": 0.799996  ,
             "SIDE": 0.999999  ,
            "PCTIM": 0.057756  ,
            "ADIMP": 0.038730  ,
            "Kprop": 0.035387  ,
              "lag": -0.0
        } 
    },
    {
        "idSimul": "TBA-SAC-F2-SIPREC",
        "config": {
            "id": "TBA",
            "modelo": SACSMA,
            "fobj": "DesvResid",
            "chuva": "siprec",
            "periodo": [datetime(2013, 1, 1, 0, 0, 0), datetime(2017, 6, 25, 0, 0, 0)],
        },
        "parametros": {
            "UZTWM": 10.000   ,
            "UZFWM": 149.986   ,
              "UZK": 0.100945   ,
            "ZPERC": 344.800   ,
             "REXP": 1.032250   ,
            "LZTWM": 10.000   ,
            "LZFSM": 399.995    ,
            "LZFPM": 999.974    ,
             "LZSK": 0.110719    ,
             "LZPK": 0.004195    ,
            "PFREE": 0.799995    ,
             "SIDE": 1.000000    ,
            "PCTIM": 0.100000    ,
            "ADIMP": 0.010802    ,
            "Kprop": 0.028731    ,
              "lag": 0.0
        } 
    },  

    {
        "idSimul": "TBA-IPH-F1-SIPREC",
        "config": {
            "id": "TBA",
            "modelo": IPH2,
            "fobj": "NSE",
            "chuva": "siprec",
            "periodo": [datetime(2013, 1, 1, 0, 0, 0), datetime(2017, 6, 25, 0, 0, 0)],
        },
        "parametros": {
            "RMAX": 3.2193    , 
              "Io": 16.7626   ,
             "fIb": 0.18791100 ,
               "H": 0.006346   ,
            "alfa": 0.100000  ,
            "Ksup": 199.9997  , 
            "Ksub": 433.9780  ,
            "Aimp": 0.000100    ,
              "NH": 21.18
    
  
        } 
    },
    {
        "idSimul": "TBA-IPH-F2-SIPREC",
        "config": {
            "id": "TBA", 
            "modelo": IPH2,
            "fobj": "DesvResid",
            "chuva": "siprec",
            "periodo": [datetime(2013, 1, 1, 0, 0, 0), datetime(2017, 6, 25, 0, 0, 0)],
        },
        
        "parametros": {
            "RMAX": 2.1645   ,
              "Io": 18.3369  ,
             "fIb": 0.19999593 ,
               "H": 0.022890   ,
            "alfa": 0.100003  ,
            "Ksup": 199.9831  ,
            "Ksub": 418.8836  ,
            "Aimp": 0.000100   ,
              "NH": 28.93
              
        }      
    },

   # T1: até cebolão serão usados os parâmetros calibrados entre ribeirão das antas e jataizinho.
   # Os mesmos parâmetros serão usados para simular a bacia T2, que será simulada como uma bacia de
   # 2. ordem. Será usada vazão de montande simulada até ribeirão das antas
   # 
   # OBS1.: devido a falta de dados do siprec para calibrar, os parâmetros do siprec também foram calibrados com
   #       dados dos pluviômetros
   # OBS2.: a curva-chave da estação cebolão está muito estranha, subestimando a vazão. Até ser devidamente corrigida,
   #       não confiar muito nestos dados
   # OBS3.: o parametro "lag" foi dimunuido em 3h visto que este é o tempo de propagação entre cebolão e jataizinho.
   
    {
        "idSimul": "T1-SAC-F1-PLU",
        "config": {
            "id": "T1",
            "modelo": SACSMA,
            "fobj": "NSE",
            "chuva": "pluviometros",
            "periodo": [datetime(2013, 1, 1, 0, 0, 0), datetime(2017, 6, 25, 0, 0, 0)],
        },
        "parametros": {
            "UZTWM": 10.001    ,
            "UZFWM": 16.008   ,
              "UZK": 0.749987   ,
            "ZPERC": 71.094   ,
             "REXP": 4.863409   ,
            "LZTWM": 53.921    ,
            "LZFSM": 37.841    ,
            "LZFPM": 352.143   ,
             "LZSK": 0.349995   ,
             "LZPK": 0.018230   ,
            "PFREE": 0.554135   ,
             "SIDE": 1.000000   ,
            "PCTIM": 0.000003   ,
            "ADIMP": 0.108307   ,
            "Kprop": 0.161081   ,
              "lag": 6.1
        } 
    },
    {
        "idSimul": "T1-SAC-F2-PLU",
        "config": {
            "id": "T1",
            "modelo": SACSMA,
            "fobj": "DesvResid",
            "chuva": "pluviometros",
            "periodo": [datetime(2013, 1, 1, 0, 0, 0), datetime(2017, 6, 25, 0, 0, 0)],
        },
        "parametros": {
            "UZTWM": 10.000   ,
            "UZFWM": 14.667 ,
              "UZK": 0.691021   ,
            "ZPERC": 45.701  ,
             "REXP": 4.016416    ,
            "LZTWM": 43.001    ,
            "LZFSM": 27.963  ,
            "LZFPM": 325.168  ,
             "LZSK": 0.349999   ,
             "LZPK": 0.018612   ,
            "PFREE": 0.578169   ,
             "SIDE": 0.999999   ,
            "PCTIM": 0.000037   ,
            "ADIMP": 0.082341   ,
            "Kprop": 0.160526      ,
              "lag": 6.5
        } 
    },  

    {
        "idSimul": "T1-IPH-F1-PLU",
        "config": {
            "id": "T1",
            "modelo": IPH2,
            "fobj": "NSE",
            "chuva": "pluviometros",
            "periodo": [datetime(2013, 1, 1, 0, 0, 0), datetime(2017, 6, 25, 0, 0, 0)],
        },
        "parametros": {
            "RMAX": 18.4941   , 
              "Io": 20.2170  ,
             "fIb": 0.15382408   ,
               "H": 0.000441    ,
            "alfa": 0.122012    ,
            "Ksup": 25.8266   , 
            "Ksub": 799.9674   ,
            "Aimp": 0.187252     ,
              "NH": 19.18   ,
           "Kprop": 0.208873    ,
             "lag": 7.2
    
  
        } 
    },
    {
        "idSimul": "T1-IPH-F2-PLU",
        "config": {
            "id": "T1",
            "modelo": IPH2,
            "fobj": "DesvResid",
            "chuva": "pluviometros",
            "periodo": [datetime(2013, 1, 1, 0, 0, 0), datetime(2017, 6, 25, 0, 0, 0)],
        },
        
        "parametros": {
            "RMAX": 18.6088   ,
              "Io": 19.9440  ,
             "fIb": 0.15258997   ,
               "H": 0.000601    ,
            "alfa": 0.100001    ,
            "Ksup": 24.7052    ,
            "Ksub": 799.9981  ,
            "Aimp": 0.183512    ,
              "NH": 19.71   ,
           "Kprop": 0.207449     ,   
             "lag": 7              
        }      
    },

   # Simulação com dados do siprec
   {
        "idSimul": "T1-SAC-F1-SIPREC",
        "config": {
            "id": "T1",
            "modelo": SACSMA,
            "fobj": "NSE",
            "chuva": "siprec",
            "periodo": [datetime(2013, 1, 1, 0, 0, 0), datetime(2017, 6, 25, 0, 0, 0)],
        },
        "parametros": {
            "UZTWM": 149.412    ,
            "UZFWM": 28.897  ,
              "UZK": 0.313446    ,
            "ZPERC": 45.897  ,
             "REXP": 1.296888    ,
            "LZTWM": 188.465    ,
            "LZFSM": 21.741    ,
            "LZFPM": 540.033   ,
             "LZSK": 0.225782    ,
             "LZPK": 0.003349    ,
            "PFREE": 0.758985    ,
             "SIDE": 0.999999    ,
            "PCTIM": 0.048151    ,
            "ADIMP": 0.000233    ,
            "Kprop": 0.207212    ,
              "lag": 7
        } 
    },
    {
        "idSimul": "T1-SAC-F2-SIPREC",
        "config": {
            "id": "T1",
            "modelo": SACSMA,
            "fobj": "DesvResid",
            "chuva": "siprec",
            "periodo": [datetime(2013, 1, 1, 0, 0, 0), datetime(2017, 6, 25, 0, 0, 0)],
        },
        "parametros": {
            "UZTWM": 176.203  ,
            "UZFWM": 149.926   ,
              "UZK": 0.223694    ,
            "ZPERC": 348.886   ,
             "REXP": 1.506777     ,
            "LZTWM": 307.849   ,
            "LZFSM": 238.799    ,
            "LZFPM": 999.998  ,
             "LZSK": 0.349997    ,
             "LZPK": 0.005511    ,
            "PFREE": 0.699780    ,
             "SIDE": 1.000000    ,
            "PCTIM": 0.064870    ,
            "ADIMP": 0.067059    ,
            "Kprop": 0.188101       ,
              "lag": 7
        } 
    },  

    {
        "idSimul": "T1-IPH-F1-SIPREC",
        "config": {
            "id": "T1",
            "modelo": IPH2,
            "fobj": "NSE",
            "chuva": "siprec",
            "periodo": [datetime(2013, 1, 1, 0, 0, 0), datetime(2017, 6, 25, 0, 0, 0)],
        },
        "parametros": {
            "RMAX": 18.6521    , 
              "Io": 17.5696   ,
             "fIb": 0.13603437   ,
               "H": 0.000057    ,
            "alfa": 0.102204    ,
            "Ksup": 43.2513    , 
            "Ksub": 799.9794   ,
            "Aimp": 0.096434     ,
              "NH": 15.10   ,
           "Kprop": 0.238967    ,
             "lag": 7
    
  
        } 
    },
    {
        "idSimul": "T1-IPH-F2-SIPREC",
        "config": {
            "id": "T1",
            "modelo": IPH2,
            "fobj": "DesvResid",
            "chuva": "siprec",
            "periodo": [datetime(2013, 1, 1, 0, 0, 0), datetime(2017, 6, 25, 0, 0, 0)],
        },
        
        "parametros": {
            "RMAX": 18.6521    ,
              "Io": 17.5688   ,
             "fIb": 0.13603710   ,
               "H": 0.000057    ,
            "alfa": 0.102196    ,
            "Ksup": 41.1013  ,
            "Ksub": 799.9973   ,
            "Aimp": 0.079406    ,
              "NH": 15.86   ,
           "Kprop": 0.240165     ,   
             "lag": 7       
        }      
    },

   # T2: até jataizinho serão usados os parâmetros calibrados entre ribeirão das antas e jataizinho.
   # Os mesmos parâmetros serão usados para simular a bacia T1, que será simulada como uma bacia de
   # 2. ordem. Será usada vazão de montante simulada até ribeirão das antas
   # 
   # OBS1.: devido a falta de dados do siprec para calibrar, os parâmetros do siprec também foram calibrados com
   #       dados dos pluviômetros

    {
        "idSimul": "T2-SAC-F1-PLU",
        "config": {
            "id": "T2",
            "modelo": SACSMA,
            "fobj": "NSE",
            "chuva": "pluviometros",
            "periodo": [datetime(2013, 1, 1, 0, 0, 0), datetime(2017, 6, 25, 0, 0, 0)],
        },
        "parametros": {
            "UZTWM": 10.001    ,
            "UZFWM": 16.008    ,
              "UZK": 0.749987  ,
            "ZPERC": 71.094    ,
             "REXP": 4.863409  ,
            "LZTWM": 53.921    ,
            "LZFSM": 37.841    ,
            "LZFPM": 352.143   ,
             "LZSK": 0.349995   ,
             "LZPK": 0.018230   ,
            "PFREE": 0.554135   ,
             "SIDE": 1.000000   ,
            "PCTIM": 0.000003   ,
            "ADIMP": 0.108307   ,
            "Kprop": 0.161081   ,
              "lag": 9.1
        } 
    },
    {
        "idSimul": "T2-SAC-F2-PLU",
        "config": {
            "id": "T2",
            "modelo": SACSMA,
            "fobj": "DesvResid",
            "chuva": "pluviometros",
            "periodo": [datetime(2013, 1, 1, 0, 0, 0), datetime(2017, 6, 25, 0, 0, 0)],
        },
        "parametros": {
            "UZTWM": 10.000   ,
            "UZFWM": 14.667 ,
              "UZK": 0.691021   ,
            "ZPERC": 45.701  ,
             "REXP": 4.016416    ,
            "LZTWM": 43.001    ,
            "LZFSM": 27.963  ,
            "LZFPM": 325.168  ,
             "LZSK": 0.349999   ,
             "LZPK": 0.018612   ,
            "PFREE": 0.578169   ,
             "SIDE": 0.999999   ,
            "PCTIM": 0.000037   ,
            "ADIMP": 0.082341   ,
            "Kprop": 0.160526      ,
              "lag": 9.5
        } 
    },  

    {
        "idSimul": "T2-IPH-F1-PLU",
        "config": {
            "id": "T2",
            "modelo": IPH2,
            "fobj": "NSE",
            "chuva": "pluviometros",
            "periodo": [datetime(2013, 1, 1, 0, 0, 0), datetime(2017, 6, 25, 0, 0, 0)],
        },
        "parametros": {
            "RMAX": 18.4941   , 
              "Io": 20.2170  ,
             "fIb": 0.15382408   ,
               "H": 0.000441    ,
            "alfa": 0.122012    ,
            "Ksup": 25.8266   , 
            "Ksub": 799.9674   ,
            "Aimp": 0.187252     ,
              "NH": 19.18   ,
           "Kprop": 0.208873    ,
             "lag": 10.2
    
  
        } 
    },
    {
        "idSimul": "T2-IPH-F2-PLU",
        "config": {
            "id": "T2",
            "modelo": IPH2,
            "fobj": "DesvResid",
            "chuva": "pluviometros",
            "periodo": [datetime(2013, 1, 1, 0, 0, 0), datetime(2017, 6, 25, 0, 0, 0)],
        },
        
        "parametros": {
            "RMAX": 18.6088   ,
              "Io": 19.9440  ,
             "fIb": 0.15258997   ,
               "H": 0.000601    ,
            "alfa": 0.100001    ,
            "Ksup": 24.7052    ,
            "Ksub": 799.9981  ,
            "Aimp": 0.183512    ,
              "NH": 19.71   ,
           "Kprop": 0.207449     ,   
             "lag": 9.7              
        }      
    },
    
    
    # Siprec
   {
        "idSimul": "T2-SAC-F1-SIPREC",
        "config": {
            "id": "T2",
            "modelo": SACSMA,
            "fobj": "NSE",
            "chuva": "siprec",
            "periodo": [datetime(2013, 1, 1, 0, 0, 0), datetime(2017, 6, 25, 0, 0, 0)],
        },
        "parametros": {
            "UZTWM": 149.412    ,
            "UZFWM": 28.897   ,
              "UZK": 0.313446    ,
            "ZPERC": 45.897   ,
             "REXP": 1.296888    ,
            "LZTWM": 188.465    ,
            "LZFSM": 21.741    ,
            "LZFPM": 540.033   ,
             "LZSK": 0.225782    ,
             "LZPK": 0.003349    ,
            "PFREE": 0.758985    ,
             "SIDE": 0.999999    ,
            "PCTIM": 0.048151    ,
            "ADIMP": 0.000233    ,
            "Kprop": 0.207212    ,
              "lag": 10.0
        } 
    },
    {
        "idSimul": "T2-SAC-F2-SIPREC",
        "config": {
            "id": "T2",
            "modelo": SACSMA,
            "fobj": "DesvResid",
            "chuva": "siprec",
            "periodo": [datetime(2013, 1, 1, 0, 0, 0), datetime(2017, 6, 25, 0, 0, 0)],
        },
        "parametros": {
            "UZTWM": 176.203  ,
            "UZFWM": 149.926   ,
              "UZK": 0.223694  ,
            "ZPERC": 348.886   ,
             "REXP": 1.506777   ,
            "LZTWM": 307.849  ,
            "LZFSM": 238.799  , 
            "LZFPM": 999.998  ,
             "LZSK": 0.349997  ,
             "LZPK": 0.005511  ,
            "PFREE": 0.699780  ,
             "SIDE": 1.000000  ,
            "PCTIM": 0.064870  ,
            "ADIMP": 0.067059  ,
            "Kprop": 0.188101     ,
              "lag": 10.4
        } 
    },  

    {
        "idSimul": "T2-IPH-F1-SIPREC",
        "config": {
            "id": "T2",
            "modelo": IPH2,
            "fobj": "NSE",
            "chuva": "siprec",
            "periodo": [datetime(2013, 1, 1, 0, 0, 0), datetime(2017, 6, 25, 0, 0, 0)],
        },
        "parametros": {
            "RMAX": 18.6521    , 
              "Io": 17.5696   ,
             "fIb": 0.13603437   ,
               "H": 0.000057    ,
            "alfa": 0.102204    ,
            "Ksup": 43.2513   , 
            "Ksub": 799.9794  ,
            "Aimp": 0.096434     ,
              "NH": 15.10  ,
           "Kprop": 0.238967    ,
             "lag": 9.9
    
  
        } 
    },
    {
        "idSimul": "T2-IPH-F2-SIPREC",
        "config": {
            "id": "T2",
            "modelo": IPH2,
            "fobj": "DesvResid",
            "chuva": "siprec",
            "periodo": [datetime(2013, 1, 1, 0, 0, 0), datetime(2017, 6, 25, 0, 0, 0)],
        },
        
        "parametros": {
            "RMAX": 18.6521    ,
              "Io": 17.5688   ,
             "fIb": 0.13603710   ,
               "H": 0.000057    ,
            "alfa": 0.102196    ,
            "Ksup": 41.1013  ,
            "Ksub": 799.9973    ,
            "Aimp": 0.079406    ,
              "NH": 15.86   ,
           "Kprop": 0.240165     ,   
             "lag": 10.2       
        }      
    }


]