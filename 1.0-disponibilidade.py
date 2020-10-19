#!/usr/bin/python
from datetime import datetime
from sys import argv
d = datetime.now()
arq = open('livro_ponto.txt', 'a')
arq.write('%s %s\n' % (d.strftime('%Y %m %d %H %M %S'), argv[1]))
arq.close()