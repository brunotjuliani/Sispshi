import pandas as pd
import numpy as np

grade = pd.read_csv('../Dados/lista_10k.csv')
grade = grade.sort_values(by=['Nr_Bacia', 'y', 'x'])
grade = grade[['x', 'y', 'Nr_Bacia']]
grade.columns = ['x', 'y', 'bacia']
grade.index = np.arange(1,len(grade)+1)
grade.to_csv('../Dados/grade_def.csv', index_label='idGrade')

grade = pd.read_csv('../Dados/grade_def.csv')
max(grade['x'])
min(grade['x'])

max(grade['y'])
min(grade['y'])
