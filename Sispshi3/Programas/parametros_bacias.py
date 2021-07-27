import pandas as pd
import numpy as np
#Definicao das sub-bacias
bacias_def = pd.read_csv('../Dados/bacias_def.csv', dtype={'b_montante':list})

params1 = pd.read_csv('../../calibracao_sacramento/param_macs/param_macs_01_Rio_Negro.csv', index_col='Parametros')
params1 = params1['Par_MACS'].rename('par_01')
params = params1

params2 = pd.read_csv('../../calibracao_sacramento/param_macs/param_macs_02_Porto_Amazonas.csv', index_col='Parametros')
params2 = params2['Par_MACS'].rename('par_02')
params = pd.merge(params, params2, left_index=True, right_index=True)

params3 = pd.read_csv('../../calibracao_sacramento/param_macs/param_macs_03_Sao_Bento.csv', index_col='Parametros')
params3 = params3['Par_MACS'].rename('par_03')
params = pd.merge(params, params3, left_index=True, right_index=True)

params4 = pd.read_csv('../../calibracao_sacramento/param_macs/param_macs_04_Pontilhao.csv', index_col='Parametros')
params4 = params4['Par_MACS'].rename('par_04')
params = pd.merge(params, params4, left_index=True, right_index=True)

params5 = pd.read_csv('../../calibracao_sacramento/param_macs/param_macs_05_Santa_Cruz_Timbo.csv', index_col='Parametros')
params5 = params5['Par_MACS'].rename('par_05')
params = pd.merge(params, params5, left_index=True, right_index=True)

params10 = pd.read_csv('../../calibracao_sacramento/param_macs/param_macs_10_Madereira_Gavazzoni.csv', index_col='Parametros')
params10 = params10['Par_MACS'].rename('par_10')
params = pd.merge(params, params10, left_index=True, right_index=True)

params11 = pd.read_csv('../../calibracao_sacramento/param_macs/param_macs_11_Jangada.csv', index_col='Parametros')
params11 = params11['Par_MACS'].rename('par_11')
params = pd.merge(params, params11, left_index=True, right_index=True)

params13 = pd.read_csv('../../calibracao_sacramento/param_macs/param_macs_13_Solais_Novo.csv', index_col='Parametros')
params13 = params13['Par_MACS'].rename('par_13')
params = pd.merge(params, params13, left_index=True, right_index=True)

params14 = pd.read_csv('../../calibracao_sacramento/param_macs/param_macs_14_Porto_Santo_Antonio.csv', index_col='Parametros')
params14 = params14['Par_MACS'].rename('par_14')
params = pd.merge(params, params14, left_index=True, right_index=True)

params15 = pd.read_csv('../../calibracao_sacramento/param_macs/param_macs_15_Aguas_do_Vere.csv', index_col='Parametros')
params15 = params15['Par_MACS'].rename('par_15')
params = pd.merge(params, params15, left_index=True, right_index=True)

params.to_csv('../Dados/param_dt6.csv')