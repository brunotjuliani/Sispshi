import pandas as pd
import numpy as np
import datetime as dt
import xarray as xr
import time

print(dt.datetime.now(), 'Inicializando')
start1 = time.time()

with xr.open_dataset('../teste_ECMWF_3meses.grib2', engine='cfgrib') as ds:
    grbs = ds.to_dataframe()

grbs = grbs.iloc[:,-1].rename('chuva_acum').reset_index(level=['latitude','longitude'])
grbs['chuva_acum'] = grbs['chuva_acum']*1000 #m para mm
grbs['x'] = grbs['longitude'].apply(lambda x: round(x,1))
grbs['y'] = grbs['latitude'].apply(lambda x: round(x,1))
grbs = grbs.drop(['latitude', 'longitude'], axis=1)

#Lista membro ensemble
membros = grbs.index.unique('number')
#Lista passos de tempo
steps = grbs.index.unique('step')

grbs
