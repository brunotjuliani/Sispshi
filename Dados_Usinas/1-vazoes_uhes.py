import pandas as pd
import datetime as dt
import numpy as np
import psycopg2, psycopg2.extras


listaUHES = [
	      ['DRJ', 'Derivação Rio Jordão', '30'],
	      ['FCH', 'Foz do Chopim', '6'],
	      ['GBM', 'Gov. Bento Munhoz (Foz do Areia)', '1'],
	      ['SCL', 'Santa Clara', '31'],
	      ['SCX', 'Gov. José Richa (Salto Caxias)', '20'],
	      ['SGD', 'Gov. Ney Braga (Segredo)', '24'],
	      ['SOS', 'Salto Osório', '53']
	    ]

ponto = '1'
t_ini = dt.datetime(1997, 1, 1,  0,  0)


tini = t_ini.strftime('%Y-%m-%d %H:%M')

texto_psql = "select mondatahora, \
	  monvalues->>'vazaoAfluente', \
	  monvalues->>'vazaoDefluente' \
	  from copel.monhid \
	  where mondatahora > '{}' and \
	  monponto = {}".format(tini, ponto)
conn = psycopg2.connect(dbname='clim', user='reader', password='r&ead3r', host='tornado', port='5432')
consulta = conn.cursor(cursor_factory = psycopg2.extras.DictCursor)
consulta.execute(texto_psql)
consulta = consulta.fetchall()

df3 = pd.DataFrame(consulta)
df = pd.DataFrame(consulta, columns=['mondatahora','Qaflu','Qdeflu'])

df
