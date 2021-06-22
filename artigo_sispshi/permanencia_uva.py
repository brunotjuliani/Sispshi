import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import scipy.stats as st

df = pd.read_excel(f'./UVA_vazoes.xlsx', skiprows = 0, header = 0,
                   parse_dates=True, index_col='dia')
df['vazao'] = pd.to_numeric(df['vazao'], errors='coerce')
df['vazao'] = df['vazao'].interpolate(method='spline', order=3)
df['vazao'].isna().sum()
df = df.loc['1931':'2020']
df['q7'] = df['vazao'].rolling(window=7, min_periods=1).mean()


grouped = df.groupby(df.index.year)
minimos = grouped.min().reset_index()
minimos.index = minimos['dia']
#minimos['logq7'] = np.log10(minimos['q7'])
max_value = max(minimos['q7'])
min_value = min(minimos['q7'])
x = np.linspace(min_value,max_value,100)
x



param_p3 = st.pearson3.fit(minimos['q7'])
# fitted distribution
fd_p3 = st.pearson3(*param_p3[:-2], loc=param_p3[-2], scale=param_p3[-1])
pdf_fitted_p3 = fd_p3.pdf(x)
plt.plot(x,pdf_fitted_p3,'r-', color='red', label='Pearson3')#,x,pdf,'b--')
minimos['Prob_P3'] = minimos.apply(lambda x: fd_p3.cdf(x['q7']), axis=1)

# param_lp = st.pearson3.fit(np.log10(minimos['q7']))
# # fitted distribution
# fd_lp = st.pearson3(*param_lp[:-2], loc=param_lp[-2], scale=param_lp[-1])
# pdf_fitted_lp = fd_lp.pdf(x)
# plt.plot(x,pdf_fitted_lp,'r-', color='purple', label='LP3')#,x,pdf,'b--')
# minimos['Prob_LP'] = minimos.apply(lambda x: fd_lp.cdf(np.log10(x['q7'])), axis=1)


param_gr = st.gumbel_r.fit(minimos['q7'])
# fitted distribution
fd_gr = st.gumbel_r(loc=param_gr[-2], scale=param_gr[-1])
pdf_fitted_gr = fd_gr.pdf(x)
plt.plot(x,pdf_fitted_gr,'r-',color='blue', label='Gumbel')#,x,pdf,'b--')
minimos['Prob_GR'] = minimos.apply(lambda x: fd_gr.cdf(x['q7']), axis=1)


param_ln = st.lognorm.fit(minimos['q7'], floc=0)
# fitted distribution
fd_ln = st.lognorm(*param_ln[:-2], loc=param_ln[-2], scale=param_ln[-1])
pdf_fitted_ln = fd_ln.pdf(x)
plt.plot(x,pdf_fitted_ln,'r-',color='green', label='LN2')#,x,pdf,'b--')
minimos['Prob_LN'] = minimos.apply(lambda x: fd_ln.cdf(x['q7']), axis=1)


param_gm = st.gamma.fit(minimos['q7'])
# fitted distribution
fd_gm = st.gamma(*param_gm[:-2], loc=param_gm[-2], scale=param_gm[-1])
pdf_fitted_gm = fd_gm.pdf(x)
plt.plot(x,pdf_fitted_gm,'r-',color='orange', label='Gamma')#,x,pdf,'b--')
minimos['Prob_GM'] = minimos.apply(lambda x: fd_gm.cdf(x['q7']), axis=1)

dump=plt.hist(minimos['q7'],density=True,alpha=.3)
plt.title(f'União da Vitória')
plt.legend()

minimos.loc['2000':]
