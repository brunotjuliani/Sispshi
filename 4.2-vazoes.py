#!/usr/bin/python
# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from sys import path, stdout; path.append('/simepar/hidro/COPEL/SISPSHI2/Bibliotecas/')
from admin import dataexec, N2F, Preenchimento
from iguacu import BaciaSISPSHI
from simuhidro import EntradaPadrao, SimulacaoPadrao


""" 2-vazoes.py: Faz a gestão das séries longas de vazão nas sub-bacias simuladas pelo SISPSHI2
    Este programa serve para atualizar os arquivos que contém as séries longas de vazão e, eventualmente, reconstituir períodos
com falhas. O tamanho da série longa é determinado pelo intervalo entre as datas gravadas no arquivo ~/SISPSHI2/data.txt corres-
pondente aos tags "datainiciohistorico" e "datareferencia".
    A atualização dos históricos é feita adicionando-se as séries curtas de dados gerados em ~/SISPSHI2/Dados_Estacoes/Vazao_01H/.
Nos períodos de redundância entre as série, onde há dados tanto na série longa quanto na curta, serão aplicadas as seguintes
regras:
    - Se o dado da série curta for válido (i.e., valor que não o código de falha) ele é colocado no lugar do mesmo dado presente
      na série longa;
    - Se o dado da série curta for inválido (= código de falha) o dado correspondente da série longa não é alterado.
    Uma vez reconstruida a série longa de vazão o programa procurará por períodos sem dados e os preencherá com interpolação ou
vazão modelada. Todavia, nos arquivos das séries longas serão gravadas duas colunas de dados, uma com a série horária consistida
sem preenchimento e outra com preenchimento. A primeira deve ser utilizada para efetuar cálculos de parâmetros estatísticos e a
segunda como dado de entrada dos modelos hidrológicos (i.e. vazão de montante para o modelo conceitual, e vazão observada para
modelos de inteligência artificial ou estocásticos). """
print '\n ~/SISPSHI2/Dados_Bacias/2-vazoes.py'


# Listando sub-bacias do SISPSHI2, incluindo suas informações espaciais,
Lbacs = BaciaSISPSHI()
Nbacs = len(Lbacs)

# Inicializando matriz de dados
dtref, dthist = dataexec(['datareferencia','datainiciohistorico'])
mtz1 = {}    #matriz onde serão armazenadas as séries longas de vazão, sem preenchimento
datas = []

dt = dthist
while dt <= dtref:
    mtz1[dt] = [[None,None] for x in range(Nbacs)]
    datas.append(dt)
    dt += timedelta(hours = 1)


# Códigos das simulações aplicadas ao preenchimento de falhas
codsim = [ None, 102, 202, 302, 402, 502, 602, 702, 802, 902, 1002, 1102, 1201, 1302, 1402, 1502, 1600, 1700,
           1800, 1900, 2000, 2102]


# Mudando código do posto da exutória para sigla do arquivo de dados nas bacias de UHEs
for iB in range(Nbacs):
    if Lbacs[iB].numero == 12:      # Foz do Areia (Governador Bento Munhoz)
        Lbacs[iB].codigo = 'GBM'
    if Lbacs[iB].numero == 16:      # Segredo
        Lbacs[iB].codigo = 'SGD'
    if Lbacs[iB].numero == 17:      # Foz do Chopim
        Lbacs[iB].codigo = 'FCH'
    if Lbacs[iB].numero == 18:      # Santa Clara
        Lbacs[iB].codigo = 'SCL'
    if Lbacs[iB].numero == 19:      # Salto Caxias
        Lbacs[iB].codigo = 'SCX'








for iB, Bac in enumerate(Lbacs):

    # PARTE 1: Atualizando séries longas
    #-------------------------------------------------------------------------------------------------------------------------------
    print '\n     - B%2.2i %s: Atualizando série longa' % (Bac.numero, Bac.nome)

    # Adicionando série longa
    try:
        arq = open(str('vazao_%2.2i.txt' % Bac.numero), 'r')
        for L in arq.readlines():
            L = L.split()
            dt = datetime(int(L[0]), int(L[1]), int(L[2]), int(L[3]), 0, 0)
            v1, v2 = float(L[4]), float(L[5])
            if v1 < -999: v1 = None
            try:
                mtz1[dt][iB] = [v1, v1]    # Aqui é o momento em que apenas dados entre dthist e dtref são armazenados
            except KeyError:
                pass
        arq.close()
        print '          > Armazenou série longa'

    except IOError:
        print '          > Não há série longa de vazão'
        pass

    
    # Adicionando série curta
    """ Nas sub-bacias cuja exutória é a seção do rio monitorada por um posto fluviométrico a série curta de vazão é procedente dos
    arquivos gerados em ~/SISPSHI2/Dados_Estacoes/Vazao_01H/. Entretanto, nas sub-bacias delimitadas por UHEs é preciso pegar os
    dados estimados de vazão afluente para o reservatório (sugestão do Anderson da COPEL). Estes dados são gerados pela COPEL e disponibilizados hora a hora no diretório '/simepar/copelger/sispshi/'.
    Atualizacao 2020-09-11: diretorio para dados das usinas modificado para '/simepar/hidro/COPEL/SISPSHI2/Dados_Usinas/'."""
    if type(Bac.codigo).__name__ == 'int':    # Sub-bacia de seção normal
        arq = open(str('/simepar/hidro/COPEL/SISPSHI2/Dados_Estacoes/Vazao_01H/vaz01H_%8i.txt' % Bac.codigo), 'r')
        for L in arq.readlines():
            dt = datetime(int(L[0:4]), int(L[5:7]), int(L[8:10]), int(L[11:13]), 0, 0)
            v3 = float(L[14:22])
            if v3 < -999:    # Não incluir falhas da série curta na série longa (não é preciso)
                pass
            else:
                mtz1[dt][iB][0] = v3
                mtz1[dt][iB][1] = v3
        arq.close()

    ## -- Alteracao importacao dados UHEs / Atualizado por Bruno em 2020-09-11
    else:    # Sub-bacia de UHE
        arq = open(str('/simepar/hidro/COPEL/SISPSHI2/Dados_Usinas/%3s.txt' % Bac.codigo), 'r')
        for L in arq.readlines()[-720:]: #30 dias retroativo
            dt = datetime(int(L[0:4]), int(L[5:7]), int(L[8:10]), int(L[11:13]), 0, 0)
            try:
                v3 = float(L[14:22])
                if v3 < 0.0:    # Não incluir valores negativos da série curta na série longa (não é preciso)
                    v3 = None
                else:
                    mtz1[dt][iB][0] = v3
                    mtz1[dt][iB][1] = v3
            except ValueError:
                pass
        arq.close()

### -- SCRIPT ANTERIOR PARA VAZOES DE UHE -- ###
#    else:    # Sub-bacia de UHE
#        arq = open(str('/simepar/copelger/sispshi/%3s.txt' % Bac.codigo), 'r')
#        for L in arq.readlines()[1:]:
#            L = L.split(';')
#
#            dia, mes, ano, hor = int(L[0][0:2]), int(L[0][3:5]), int(L[0][6:10]), int(L[0][11:13])
#            if hor == 24:
#                dt = datetime(ano,mes,dia,23,0,0) + timedelta(hours = 1)
#            else:
#                dt = datetime(ano,mes,dia,hor,0,0)
#            if dt > dtref:
#                continue
#
#            try:
#                v3 = float(L[1].replace(',','.'))    # Se não houver dado no arquivo o try/except irá desviar o erro.
#                if v3 < 0.0: v3 = None
#                mtz1[dt][iB][0] = v3
#                mtz1[dt][iB][1] = v3
#            except ValueError:
#                pass
#        arq.close()
    print '          > Armazenou série curta'


    # Contabilizando ausências de dados na série longa
    nd = 0
    for dt in datas:
        if mtz1[dt][iB][0] == None:
            nd += 1
    if nd == 0:
        print '          > Nova série longa está completa.'




    # PARTE 2: Preenchendo falhas
    #-------------------------------------------------------------------------------------------------------------------------------
    else:
        print '          > Faltam %i dados, %6.2f%% da nova série longa.' % (nd, nd*100./float(len(datas)))

       # Obtendo dados de entrada e rodando o modelo
        M = EntradaPadrao(Bac, dthist, dtref, codsim[Bac.numero])
        """ A função EntradaPadrao lê os dados de entrada do modelo a partir dos arquivos presentes no diretório atual. Entretanto
        neste momento, os arquivos começam um pouco antes de dthist e terminam um pouco antes de dtref, de modo que a série de vazão
        não sincroniza com os demais dados de entrada. Por isso é preciso trocar os dados lidos pelos que já estão armazenados em
        mtz1. """
        M.qobs = {}
        for dt in datas:
            M.qobs[dt] = mtz1[dt][iB][0]
        Qmod = SimulacaoPadrao(M)    # Qmod é um dicionário de dados modelados, indexado por datahora

        # ALGORITMO DE SUBSTITUIÇÃO AUTOMÁTICA DE DADOS
        intervalo = [ [datas[0], mtz1[datas[0]][iB][0], Qmod[datas[0]]] ]
        for dt in datas[1:]:
            intervalo.append( [dt, mtz1[dt][iB][0], Qmod[dt]] )
            
            if mtz1[dt][iB][0] != None:    # Encontrou um dado consistente. Pode ser um intervalo com falhas ou não!
                if len(intervalo) == 2:    # Não é um intervalo com falhas ...
                    intervalo.pop(0)       # ... então retira o dado da hora anterior e segue o 'for'.

                else:                      # Sim! Há dados no meio do intervalo que são falhas. Vamos substituir!
                    Qsub = Preenchimento(intervalo)
                    for dt2, valor in Qsub:
                        mtz1[dt2][iB][1] = max(valor, 0.0)    # Operação max() para evitar vazão negativa
                    intervalo = [ intervalo[-1][:] ]

            else:    # É um dado com falhas (valor == None), já adicionado no intervalo.
                pass

        if len(intervalo) > 1:    # Ops, o final da série não está completa. Substituir.
            Qsub = Preenchimento(intervalo)
            for dt2, valor in Qsub:
                mtz1[dt2][iB][1] = max(valor, 0.0)    # Operação max() para evitar vazão negativa

        print '          > Preencheu falhas com vazão modelada.'
    #===============================================================================================================================




    # PARTE 3: Regravando séries longas de vazão na exutória
    #-------------------------------------------------------------------------------------------------------------------------------
    arq = open(str('vazao_%2.2i.txt' % Bac.numero), 'w')
    for dt in datas:
        arq.write('%s %8.1f %8.1f\n' % (dt.strftime('%Y %m %d %H'), N2F(mtz1[dt][iB][0],-99999.9), N2F(mtz1[dt][iB][1],-99999.9)))
    arq.close()
    print '          > Atualizou séries na B%2.2i' % Bac.numero
    #===============================================================================================================================

    #===============================================================================================================================

