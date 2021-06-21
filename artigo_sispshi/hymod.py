import pandas as pd
import numpy as np
from  time import time

X = (
        ('cmax', 1, 2000),
        ('bexp', 0, 2),
        ('alpha', 0.1, 0.99),
        ('ks', 1e-6, 0.5),
        ('kq', 0.1, 1.2))
Xnomes = [i[0] for i in X]
Xmin = [i[1] for i in X]
Xmax = [i[2] for i in X]

def power(X,Y):
    X=abs(X) # Needed to capture invalid overflow with netgative values
    return X**Y

def HYMOD_CAL(precip, potential_evap, params,initFlow=True):
    'Calcula o Hydromod'
    if type(params) is np.ndarray:
        params = dict(zip(Xnomes, params))
    cmax = params['cmax']#parâmetros de calibração do modelo
    bexp = params['bexp']
    alpha = params['alpha']
    ks = params['ks']
    kq=params['kq']

    lt_to_m = 0.001

    # HYMOD PROGRAM IS SIMPLE RAINFALL RUNOFF MODEL
    x_loss = 0.0
    # Initialize slow tank state
    # value of 0 init flow works ok if calibration data starts with low discharge
    if initFlow:
        x_slow = 2.3503 / (ks * 22.5)
    else:
        x_slow= 0
    # Initialize state(s) of quick tank(s)
    x_quick = np.zeros(3)
    t = 0

    output=[]

    for Pval,PETval in zip(precip,potential_evap):
        # Compute excess precipitation and evaporation
        #ER1, ER2, x_loss = excess(x_loss, cmax, bexp, Pval, PETval)
        xn_prev = x_loss
        ct_prev = cmax * (1 - power((1 - ((bexp + 1) * (xn_prev) / cmax)), (1 / (bexp + 1))))
        # Calculate Effective rainfall 1
        ER1 = max((Pval - cmax + ct_prev), 0.0)
        Pval = Pval - ER1
        dummy = min(((ct_prev + Pval) / cmax), 1)
        xn = (cmax / (bexp + 1)) * (1 - power((1 - dummy), (bexp + 1)))

        # Calculate Effective rainfall 2
        ER2 = max(Pval - (xn - xn_prev), 0)

        # Alternative approach
        evap = (1 - (((cmax / (bexp + 1)) - xn) / (cmax / (bexp + 1)))) * PETval  # actual ET is linearly related to the soil moisture state
        xn = max(xn - evap, 0)  # update state

        # Calculate total effective rainfall
        ET = ER1 + ER2
        #  Now partition ER between quick and slow flow reservoirs
        UQ = alpha * ET
        US = (1 - alpha) * ET
        # Route slow flow component with single linear reservoir
        x_slow=(1 - ks) * x_slow + (1 - ks) * US
        QS=(ks / (1 - ks)) * x_slow

        inflow = UQ

        for i in range(3):
            # Linear reservoir
            x_quick[i]=(1 - kq) * x_quick[i] + (1 - kq) * inflow
            outflow=(kq / (1 - kq)) * x_quick[i]
            inflow = outflow

        # Compute total flow for timestep
        output.append(((QS + outflow)/lt_to_m))

    return output

def NSE_cal(dados_calculados,dados_observados):
    'Calcula 1-NSE'
    Qmedia=dados_observados.mean()
    soma_cima = ((dados_observados-dados_calculados)**2).sum()
    soma_baixo = ((dados_observados-Qmedia)**2).sum()
    return soma_cima/soma_baixo
