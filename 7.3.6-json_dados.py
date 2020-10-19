# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from sys import path, stdout
path.append('/simepar/hidro/COPEL/SISPSHI2/Bibliotecas/')
from admin import serie_horaria, dataexec, Ldatas
from simuhidro import listaprev2 as listaprev
from iguacu import base, curva_descarga, BaciaSISPSHI

print ' ~/SISPSHI2/Site_Update/6-json_dados.py'



dirSite = '/simepar/hidro/webdocs/sispshi2/dados/'
bac_antes = 0
bacias_com_curva = [ 1, 2, 3, 4, 6, 7, 8, 9, 10, 11, 13, 14, 15, 20, 21]

dref, dfinal = dataexec(['datareferencia', 'datafinalprevisao'])
datasPrev = Ldatas(dref, dfinal)
d0 = dref - timedelta(days = 10)

""" Máxima Precipitação Acumulada, MPA.
    Para garantir que em todas as bacias a escala de chuva acumulada acumula será a mesma devo localizar o maior volume de chuva
nas séries que serão exibidas nos gráficos do site do SISPSHI2. Isto pode ocorrer na chuva observada acumulada entre dref - 5 dias
e dref, ou entre a chuva prevista acumulada entre dref + 1 hora e dfinal. """
datasObs = Ldatas(dref - timedelta(days = 5), dref)
MPA = 4.0




def toJSON(nome, dados):
    """ Função para gravar em formato JSON dados em um dicionário indexado por datetime. """
    
    arq = open(nome, 'w')
    arq.write('[')
    x = sorted(dados.keys())
    nx = len(x)
    
    for i in range(nx):
        
        arq.write('["%s",' % x[i])
        if dados[x[i]] == None:
            arq.write('null]')
        else:
            arq.write('%.3f]' % dados[x[i]])
        
        if i < nx - 1:
            arq.write(',\n')
        else:
            arq.write(']')
    
    arq.close()




# Preparando arquivos JSON para cada bacia e código de simulação.
for codigo in listaprev:
    
    bac   = BaciaSISPSHI(int(codigo/100.))
    if bac.numero in bacias_com_curva:
        curva = curva_descarga(bac.codigo)
    
    """ Só grava dados da bacia se for o primeiro código de simulação da bacia em questão. Se for código de 
    uma bacia já processada grava apenas resultados das previsões. """
    if bac.numero != bac_antes:
        
        #vazao observada
        vazao = serie_horaria([[base + str('/Dados_Bacias/vazao_%2.2i.txt' % bac.numero), 5]], [d0, dref])
        for d, aux in vazao.items():
            if aux < 0: vazao[d] = 0.0
        toJSON( dirSite + str('vaz%2.2i.json' % bac.numero), vazao )
        
        #cota revertida pela curva de descarga
        if bac.numero in bacias_com_curva:
            cotas = {}
            for d, aux in vazao.items():
                cotas[d] = curva.nivel(aux)
            toJSON( dirSite + str('cota%2.2i.json' % bac.numero), cotas )
        
        #chuva média na bacia observada (PM_D2 para visualização)
        cmb = serie_horaria([[base + str('/Dados_Bacias/cmb_%2.2i.txt' % bac.numero), 7]], [d0, dref])
        toJSON( dirSite + str('cmb%2.2i.json' % bac.numero), cmb )
        
        #chuva média prevista na bacia
        cmb2 = serie_horaria([[base + str('/Previsao_CMB/prevcmb_%2.2i.txt' % bac.numero), 4]], [dref, dfinal])
        cmb2[dref] = 0.0    #incluindo registro nulo em dref para apresentar no gráfico
        toJSON( dirSite + str('prevcmb%2.2i.json' % bac.numero), cmb2 )
        
        #analisando MPA na bacia
        acmCMB = sum([cmb[t] for t in datasObs])
        if acmCMB > MPA: MPA = acmCMB
        acmCMB = sum([cmb2[t] for t in datasPrev])
        if acmCMB > MPA: MPA = acmCMB
        
        print '\n > Bacia %2.2i: ' % bac.numero,
        stdout.flush()
        
        #atualizando variável bac_antes para evitar processamento em códigos de simulação da mesma bacia
        bac_antes = bac.numero

    #vazão prevista (entre d0 e dref a vazão prevista é a vazão observada)
    vazao2 = serie_horaria([[base + str('/Conceitual/Resultados/%4.4i.txt' % codigo), 6]], [d0, dfinal])
    for d, aux in vazao2.items():
        if aux < 0: vazao2[d] = 0.0
    toJSON( dirSite + str('prevaz%4.4i.json' % codigo), vazao2 )
    
    #cota prevista revertida pela curva de descarga
    if bac.numero in bacias_com_curva:
        cotas = {}
        for d, aux in vazao2.items():
            cotas[d] = curva.nivel(aux)
        toJSON( dirSite + str('precota%4.4i.json' % codigo), cotas )

    #vazão simulada
    simul = serie_horaria([[base + str('/Conceitual/Resultados/%4.4i.txt' % codigo), 7]], [d0, dfinal])
    toJSON( dirSite + str('simul%4.4i.json' % codigo), simul )
    
    print '%4i, ' % codigo,
    stdout.flush()

print '\n > MPA =', round(MPA,0)+1


# Computando coeficiente da área incremental de Segredo
aux = [ [base + '/Dados_Usinas/SGD.txt', 4], [base + '/Dados_Usinas/GBM.txt', 5], [base + '/Dados_Bacias/vazao_13.txt', 5] ]
dados = serie_horaria(aux, [dref, dref])
""" fator = (Qaflu Segredo - Qdeflu Foz do Areia) / (Qobs Solais Novo) """
try:
    fator = (dados[dref][0] - dados[dref][1]) / dados[dref][2]
    if fator < 1: fator = 1.0
except TypeError:
    fator = 1.0

print ' > Fator Inc. Segredo = %.3f' % fator


# Gravando datas, MPA e fator em arquivo para uso no site
arq = open(dirSite + 'info.json', 'w')
arq.write('{ "dref":"%s", "dfinal":"%s", "lmtPrec":%i, "fator":%.3f }' % (dref, dfinal, (round(MPA,0)+1), fator) )
arq.close()

