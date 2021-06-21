import numpy as np
import matplotlib.pyplot as plt
from time import time
import pandas as pd
import hidrologia




def hbv_calc(prec,dpem,air_temp,month,params ):
    '''Calcula o HBV dados Preciptação, evapotranspiração potencial , temperatura do ar e meses'''
    #prec - preciptação em mm
    #dpem - evapotranspiração potencial
    #air_temp - temperatura do ar
    #month - mes do dado
    
    #temperatura média de cada mês
    aux=pd.DataFrame({'mes':month,'temp':air_temp})
    monthly=np.insert(aux.groupby('mes').mean()['temp'].values,0,0,axis=0)
    Tsnow_thresh = 0.0
    ca = 410.

    #Initialize arrays for the simiulation

    snow      = np.zeros(air_temp.size)  #
    liq_water = np.zeros(air_temp.size)  #
    pe        = np.zeros(air_temp.size)  #
    soil      = np.zeros(air_temp.size)  #
    ea        = np.zeros(air_temp.size)  #
    dq        = np.zeros(air_temp.size)  #
    s1        = np.zeros(air_temp.size)  #
    s2        = np.zeros(air_temp.size)  #
    q         = np.zeros(air_temp.size)  #
    qm        = np.zeros(air_temp.size)  #

    #Set parameters
    d    = params['d']  #
    fc   = params['fc']  #
    beta = params['beta'] #
    c    = params['c']  #
    k0   = params['k0']  #
    l    = params['l'] #
    k1   = params['k1'] #
    k2   = params['k2']  #
    kp   = params['kp']  #
    pwp  = params['pwp']  #
    n_days=len(air_temp)
    for i_day in range(1,n_days):

	#print i_day
        if air_temp[i_day] < Tsnow_thresh:

	    #Precip adds to the snow pack
            snow[i_day] = snow[i_day-1] + prec[i_day]

	    #Too cold, no liquid water
            liq_water[i_day] = 0.0

	    #Adjust potential ET base on difference between mean daily temp
	    #and long-term mean monthly temp
            pe[i_day]        = (1.+ c*(air_temp[i_day]-monthly[int(month[i_day])]))*dpem[i_day]

            #Check soil moisture and calculate actual evapotranspiration
            if soil[i_day-1] > pwp:
                ea[i_day] = pe[i_day]
            else:
                #Reduced ET_actual by fraction of permanent wilting point
                ea[i_day] = pe[i_day]*(soil[i_day-1]/pwp)

            #See comments below
            dq[i_day]   = liq_water[i_day]*(soil[i_day-1]/fc)**beta
            soil[i_day] = soil[i_day-1]+liq_water[i_day]-dq[i_day]-ea[i_day]
            if soil[i_day]<0:
                soil[i_day]=0
            s1[i_day]   = s1[i_day-1]  + dq[i_day] - max(0,s1[i_day-1]-l)*k0 -(s1[i_day]*k1)-(s1[i_day-1]*kp)
            s2[i_day]   = s2[i_day-1]  + s1[i_day-1]*kp - s2[i_day]*k2
            q[i_day]    = max(0,s1[i_day]-l)*k0+(s1[i_day]*k1)+(s2[i_day]*k2)
            qm[i_day]   = (q[i_day]*ca*1000.)/(24.*3600.)
            
           
        else:
	    #Air temp over threshold: precip falls as rain
            
           
            snow[i_day]      = max(snow[i_day-1]-d*air_temp[i_day]-Tsnow_thresh,0.)

            liq_water[i_day] = prec[i_day]+min(snow[i_day],d*air_temp[i_day]-Tsnow_thresh,0.)

            #PET adjustment
            pe[i_day]        = (1.+c*(air_temp[i_day]-monthly[int(month[i_day])]))*dpem[i_day]

            if soil[i_day-1] > pwp:
            	ea[i_day] = pe[i_day]
            else:
                ea[i_day] = pe[i_day]*soil[i_day]/pwp

            #Effective precip (portion that contributes to runoff)
            dq[i_day]   = liq_water[i_day]*((soil[i_day-1]/fc))**beta
            
                
	    #Soil moisture = previous days SM + liquid water - Direct Runoff - Actual ET
            soil[i_day] = soil[i_day-1] + liq_water[i_day]-dq[i_day]-ea[i_day]
            if soil[i_day]<0:
                soil[i_day]=0
            #Upper reservoir water levels
            s1[i_day]   = s1[i_day-1]   + dq[i_day]-max(0,s1[i_day-1]-l)*k0 - (s1[i_day]*k1)-(s1[i_day-1]*kp)
            #Lower reservoir water levels
            s2[i_day]   = s2[i_day-1]   + dq[i_day-1]*kp -s2[i_day-1]*k2

            #Run-off is total from upper (fast/slow) and lower reservoirs
            q[i_day]    = max(0,s1[i_day]-l)*k0+s1[i_day]*k1+(s2[i_day]*k2)
	#Resulting Q
        qm[i_day]   = (q[i_day]*ca*1000.)/(24.*3600.)
        #qm[i_day]   = s2[i_day]
        #qm[i_day]=10
    #End of simulation
    return qm

def hbv_calc_rapido(prec,dpem,air_temp,month,params ):
    '''Calcula o HBV pelo Fortran'''
    #temperatura média de cada mês
    aux=pd.DataFrame({'mes':month,'temp':air_temp})
    monthly=np.insert(aux.groupby('mes').mean()['temp'].values,0,0,axis=0)
    #Set parameters
    d    = params['d']  #
    fc   = params['fc']  #
    beta = params['beta'] #
    c    = params['c']  #
    k0   = params['k0']  #
    l    = params['l'] #
    k1   = params['k1'] #
    k2   = params['k2']  #
    kp   = params['kp']  #
    pwp  = params['pwp']  #
    n_days=len(air_temp)
    qm=hidrologia.hbv_sub(prec,dpem,air_temp,month,d,fc,beta,c,k0,l,k1,k2,kp,pwp,monthly,n_days)
    return qm
def NSE(dados_calculados,dados_observados):
    Qmedia=dados_observados.mean()
    soma_cima = ((dados_observados-dados_calculados)**2).sum()
    soma_baixo = ((dados_observados-Qmedia)**2).sum()
    return 1-soma_cima/soma_baixo
def NSE_cal_rapido(dados_calculados,dados_observados):
    return hidrologia.nse(dados_calculados,dados_observados,len(dados_calculados))

def NSE_cal(dados_calculados,dados_observados):
    Qmedia=dados_observados.mean()
    soma_cima = ((dados_observados-dados_calculados)**2).sum()
    soma_baixo = ((dados_observados-Qmedia)**2).sum()
    return soma_cima/soma_baixo
