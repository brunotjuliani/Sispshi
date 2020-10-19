#!/usr/bin/python
# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from os import system
from sys import path, stdout; path.append('/simepar/hidro/COPEL/SISPSHI2/Bibliotecas/')
from admin import dataexec, ler_arquivo
from iguacu import base, PluvSISPSHI, GrupoPluvs, FluvSISPSHI




""" 1-json_observados.py: Gerar arquivos no formato JSON com os dados hidrológicos do período de consulta. """
print '\n ~/SISPSHI2/Site_Update/1-json_observados.py'

# Data inicial e final do período de consulta
d0, dN = dataexec(['datainiciobanco','datareferencia'])

# Lista de datahora a cada 15 minutos entre d0 e dN
datas, dt = [], d0
while dt <= dN:
    datas.append(dt)
    dt += timedelta(minutes = 15)
ND = len(datas)

# Local onde serão gravados os dados das estações
dirSite = '/simepar/hidro/webdocs/sispshi2/dados/'




# PLUVIOMETROS
#-----------------------------------------------------------------------------------------------------------------------
""" Inicializando arquivo JSON com dados de 15 minutos dos pluviometros """
json = open(dirSite + 'chuva.json', 'w')
json.write('{ "datas" : [')

for dt in datas:
    
    if dt == datas[0]:
        json.write('[%i,%i,%i,%i,%i]' % (dt.year, dt.month, dt.day, dt.hour, dt.minute))
        
    else:
        json.write(',[%i,%i,%i,%i,%i]' % (dt.year, dt.month, dt.day, dt.hour, dt.minute))
        
json.write('],\n')


""" Processando dados de cada pluviometro e regravando registro do período de dados no arquivo JSON """
lista = PluvSISPSHI()
precMax = 0.0

for P in lista:
    
    if P.Grupos[0] == 'off':
        continue
    
    #Arquivo com os dados de 15 em 15 minutos do pluviômetro
    try:
        arq = open(base + str('/Dados_Estacoes/Chuva_15M/chv15M_%8i.txt' % P.codigo), 'r')
    except IOError:
        continue
    
    #Lendo dados
    dados = {}
    
    for l in arq:
        
        l = l.split()
        dt = datetime(int(l[0]), int(l[1]), int(l[2]), int(l[3]), int(l[4]), 0)
        nota = int(l[-1])
        
        if nota == 0:
            dados[dt] = float(l[5])
            
    arq.close()
    
    #Gravando no JSON
    acm = 0.0
    json.write('"%i" : [' % P.codigo)
    
    for dt in datas:
        
        if dt != datas[0]:
            json.write(',')
        
        try:
            acm += dados[dt]
            json.write('%.1f' % acm)
            
        except KeyError:
            json.write('null')
        
    json.write('],\n')
    if acm > precMax: precMax = acm
    

#Precipitação Máxima (para uniformizar escala do eixo Y nos gráficos do site)
json.write('"precMax" : %.1f,\n' % precMax)


#Criando lista dos grupos
for ig in range(1,12):
    
    G = GrupoPluvs(ig)    
    json.write('"grupo%2.2i" : [' % ig)
    
    for P in G:
        
        if P != G[0]:
            json.write(',')
            
        json.write('[%i,"%s"]' % (P.codigo, P.nome.encode('utf-8')))
    
    json.write('],\n')
    

#Fechando arquivo JSON
json.write('"numGrupos" : 11\n}')
#=======================================================================================================================




# NÍVEL E VAZÃO
#-----------------------------------------------------------------------------------------------------------------------
""" Inicializando arquivos JSON com dados de 15 minutos """
jsonH = open(dirSite + 'nivel.json', 'w')
jsonQ = open(dirSite + 'vazao.json', 'w')

jsonH.write('{ "datas" : [')
jsonQ.write('{ "datas" : [')

for dt in datas:
    
    if dt == datas[0]:
        jsonH.write('[%i,%i,%i,%i,%i]' % (dt.year, dt.month, dt.day, dt.hour, dt.minute))
        jsonQ.write('[%i,%i,%i,%i,%i]' % (dt.year, dt.month, dt.day, dt.hour, dt.minute))
        
    else:
        jsonH.write(',[%i,%i,%i,%i,%i]' % (dt.year, dt.month, dt.day, dt.hour, dt.minute))
        jsonQ.write(',[%i,%i,%i,%i,%i]' % (dt.year, dt.month, dt.day, dt.hour, dt.minute))
        
jsonH.write('],\n')
jsonQ.write('],\n')


""" Processando dados de cada posto hidrológico e regravando registro do período de dados nos arquivos JSON """
lista = FluvSISPSHI()

for F in lista:
    
    #Arquivo com os dados de 15 em 15 minutos de nível e vazão
    try:
        arq = open(base + str('/Dados_Estacoes/CotaVazao_15M/cot15M_%8i.txt' % F.codigo), 'r')
    except IOError:
        continue
    
    #Lendo dados
    dados = {}
    
    for l in arq:
        
        l = l.split()
        dt = datetime(int(l[0]), int(l[1]), int(l[2]), int(l[3]), int(l[4]), 0)
        nota = int(l[-2])
        
        if nota in [0, 8]:
            dados[dt] = [float(l[-3]), float(l[-1])]
            
    arq.close()
    
    #Gravando dados de Nível no JSON
    jsonH.write('"%i" : [' % F.codigo)
    
    for dt in datas:
        
        if dt != datas[0]:
            jsonH.write(',')
        
        try:
            jsonH.write('%.2f' % dados[dt][0])
            
        except KeyError:
            jsonH.write('null')
        
    jsonH.write('],\n')

    #Foz do Timbó e Porto Vitória não tem cálculo de vazão.
    if F.codigo in [26105047, 26105114]:
        continue
        
    #Gravando dados de Vazão no JSON
    jsonQ.write('"%i" : [' % F.codigo)
    
    for dt in datas:
        
        if dt != datas[0]:
            jsonQ.write(',')
        
        try:
            jsonQ.write('%.2f' % dados[dt][1])
            
        except KeyError:
            jsonQ.write('null')
        
    jsonQ.write('],\n')

#Agrupamento dos postos para Nível
jsonH.write('"grupo01" : [[26064948, "Rio Negro"], [25334953, "Porto Amazonas"], [25564947, "São Bento"], [25555031, "Pontilhão"],')
jsonH.write(' [25525023, "São Mateus do Sul"], [26055019, "Divisa"]],\n')
jsonH.write('"grupo02" : [[26125049, "Santa Cruz do Timbó"], [26105047, "Foz do Timbó"], [26025035, "Fluviopolis"], [26145104, "União da Vitória"],')
jsonH.write(' [26105114, "Porto Vitória"], [25485116, "Mad. Gavazzoni"], [26225115, "Jangada"]],\n')
jsonH.write('"grupo03" : [[26055155, "Solais Novo"], [25235306, "Porto Santo Antônio"], [25465256, "Águas do Verê"], [25345435, "Porto Capanema"],')
jsonH.write(' [25685442, "Hotel Cataratas"]],\n')

#Agrupamento dos postos para Vazão
jsonQ.write('"grupo01" : [[26064948, "Rio Negro"], [25334953, "Porto Amazonas"], [25564947, "São Bento"], [25555031, "Pontilhão"],')
jsonQ.write(' [25525023, "São Mateus do Sul"], [26055019, "Divisa"]],\n')
jsonQ.write('"grupo02" : [[26125049, "Santa Cruz do Timbó"], [26025035, "Fluviopolis"], [26145104, "União da Vitória"],')
jsonQ.write(' [25485116, "Mad. Gavazzoni"], [26225115, "Jangada"]],\n')
jsonQ.write('"grupo03" : [[26055155, "Solais Novo"], [25235306, "Porto Santo Antônio"], [25465256, "Águas do Verê"], [25345435, "Porto Capanema"],')
jsonQ.write(' [25685442, "Hotel Cataratas"]],\n')

#Fechando arquivos
jsonH.write('"numGrupos" : 3}')
jsonQ.write('"numGrupos" : 3}')
#=======================================================================================================================




print ' > gravou arquivos json de chuva, nível e vazão\n'