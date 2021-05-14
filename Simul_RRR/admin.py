# -*- coding: utf-8 -*-
from datetime import datetime, timedelta

""" Biblioteca com funções para: manipulação de data; leitura e gravação de arquivos; demais processos de controle."""




def dataexec(datatags,arqnome='/simepar/hidro/COPEL/SISPSHI2/data.txt'):
    """ Consulta no arquivo /simepar/hidro/COPEL/SISPSHI2/data.txt as datahoras que tem as mesmos tags fornecidas na lista datatags. Retorna lista com as datahoras no formato datetime seguindo a sequência da tags na lista de entrada."""
    arq = open(arqnome, 'r')
    datas = {}
    
    # Verificando consistência das strings que compõem as tags
    """ A lista de tags utilizada na sintaxe do primeiro 'if' abaixo deve ser idêntica à utilizada no programa ~/SISPSSHI2/1-datahora.py """
    for tag in datatags:
        if tag not in ['datareferencia', 'datainiciobanco', 'datafinalprevisao', 'datainiciohistorico']:
            print '\n     ERRO: ~/SISPSHI2/Bibliotecas/admin.py --- dataexec()'
            print '     %s não é uma tag válida para obter uma das datahoras utilizadas na execução do sistema.\n' % repr(tag)
            exit()
    
    # Armazenando datahoras da execução
    for linha in arq.readlines():
        linha = linha.split()
        datas[linha[-1]] = datetime(int(linha[0]), int(linha[1]), int(linha[2]), int(linha[3]), 0, 0)
    arq.close()
    
    # Retornando lista com as datahoras solicitadas
    if len(datatags) == 1:
        return datas[datatags[0]]
    else:
        return [datas[tag] for tag in datatags]




def Ldatas(dt0, dtN):
    """ Gera lista horária de datetimes entre dt0 e dtN. """
    lista = []
    while dt0 <= dtN:
        lista.append(dt0)
        dt0 += timedelta(hours = 1)
    return lista




def N2F(valor1,valor2):
    """ Transformar variável None em um float ou inteiro que represente dado com falha ou ausente. """
    if valor1 == None:
        return valor2
    else:
        return valor1




def str2datetime(s):
    """ Retorna a data/hora de um string com formato "aaaa-mm-dd HH:MM:SS" em uma variável da classe datetime. """
    s = s.strip()
    return datetime(int(s[0:4]), int(s[5:7]), int(s[8:10]), int(s[11:13]), int(s[14:16]), int(s[17:19]))




def multisplit(lin, seps=[' ','\t','\n','/','-',';',':','|']):
    """ Função para separar a string de entrada utilizando todos os separadores da lista 'seps'. Após separados os elementos, os mesmos serão convertidos em variáveis do tipo inteiro ou real, se possível. """
    palavras = []
    elemento = ''

    # Separando a string de entrada utilizando os caracteres na lista 'seps' como separadores
    for i, letra in enumerate(lin):

        # Procedendo frente a um separador
        if letra in seps:
            # É preciso ter cuidado com o caractere '-', pois ele pode ser o sinal negativo de uma variável
            if letra == '-':
                if i >=1 and lin[i-1] in seps:
                    elemento = '-'
                    continue
                else:
                    palavras.append(elemento)
                    elemento = ''
                    continue
            else:
                if elemento != '': palavras.append(elemento)
                elemento = ''
                continue

        # Procedendo caso tenha atingindo o fim da string de entrada
        if i == len(lin)-1:
            elemento += letra
            palavras.append(elemento)
            continue

        # Caso a letra seja parte de uma palavra
        elemento += letra

    # Tentando converter palavras em números, se for possível
    for i, elemento in enumerate(palavras):
        try:
            palavras[i] = int(elemento)
        except ValueError:
            try:
                palavras[i] = float(elemento)
            except ValueError:
                pass

    return palavras




def interpola_linear(mtz):
    """ Deve-se fornecer a matriz 'mtz' contendo, entre as posições [1] e [-2], os pares ordenados do período de falhas e, nas posições [0]
e [-1] os dados consistentes anterior e posterior ao período, respectivamente. """
    A = (mtz[-1][1] - mtz[0][1]) / float((mtz[-1][0] - mtz[0][0]))
    B = mtz[0][1] - A*mtz[0][0]
    for i in range(1,len(mtz)-1):
        mtz[i][1] = A*mtz[i][0] + B
    return mtz


def ilhor(t1,t2,y1,y2):
    # Função para interpolar linearmente dados horários entre t1 e t2. Retorna pares X,Y em uma lista.
    x, i, t0 = [], 0, t1
    while t0 <= t2:
        x.append(i)
        i += 1
        t0 += timedelta(hours =1)

    a = (y2-y1)/(x[-1]-x[0])
    b = y1 - a*x[0]
    xy, t0 = [], t1
    for i in x:
       xy.append([t0, a*i+b])
       t0 += timedelta(hours = 1)

    return xy




def obter_linear(Xref,mtz):
    """ Funciona seguindo o exemplo:
    mtz = [ [0.0,0.0], [1.0,10.0], [10.0,1000.0] ]; Xref = 5.0
    1 - Procura os pares de coordenadas em mtz cujo valor de X seja imediatamente inferior e superior ao de Xref.
        No caso, dado Xref = 5.0 o par imediatamente inferior é [1.0,10.0] e o imediatamente inferior é [10.0,1000.0];
    2 - Utilizando os dados dos pares de coordenadas adjacentes calcula o valor de Y para Xref por interpolação linear;
        Y(Xref) = f(5.0, [1.0,10.0], [10.0,1000.0]) = 450.0"""
    for i in range(len(mtz)-1):
        if mtz[i][0] <= Xref <= mtz[i+1][0]:
            A = (mtz[i+1][1] - mtz[i][1]) / (mtz[i+1][0] - mtz[i][0])
            B = mtz[i][1] - A*mtz[i][0]
            return A*Xref + B
    #Se chegou aqui é porque não encontrou o par de coordenadas com valor de X inferior ou superior ao Xref
    print '\n\n'
    for x, y in mtz:
        print x, y
    print 'X de referencia:', Xref, '\n'
    raise ValueError("Não há par de coordenadas que englobe Xref")




def rec_linear(mtz):
    """ Reconstituir séries de dados com interpolação linear
    Dada a lista de dados sequenciais em 'mtz', contendo N valores entre dados bons e falhas (-999.99 ou None), emprega a interpolação \
linear para substituir as falhas e retornar a mesma lista devidamente preenchida. """
    if mtz[0] == None or int(mtz[0]*100) == -99999 or mtz[-1] == None or int(mtz[-1]*100) == -99999:
        raise ValueError('\n     Valor inicial e final NÃO podem ser falhas!\n')

    XY = []
    for i in range(len(mtz)):

        if mtz[i] == None or int(mtz[i]*100) == -99999:
            XY.append([i,mtz[i]])

        else:
            XY.append([i,mtz[i]])

            if len(XY) > 2:
                XY = interpola_linear(XY)
                for j, val in XY:
                    mtz[j] = val

            XY = [ [i,mtz[i]] ]

    return mtz




def rec_spline(mtz):
    """ Reconstituir séries de dados com interpolação spline cúbica.
    Dada a lista de dados sequenciais em 'mtz', contendo N valores entre dados bons e falhas (-999.99 ou None), emprega a interpolação \
por spline cúbica para substituir as falhas e retornar a mesma lista devidamente preenchida.
    Esta função pode ser usada para aumentar a frequência de dados, tal como de dados bí-diários (7 e 17 horas) para dados horários. \
Basta que 'mtz' corresponda à série horária completa, contendo os dados observados nas posições equivalente da série horária, e que as \
demais horas do dia sejam representadas por valores de falha (-999.99 ou None). """
    if mtz[0] == None or int(mtz[0]*100) == -99999 or mtz[-1] == None or int(mtz[-1]*100) == -99999:
        raise ValueError('\n     Valor inicial e final NÃO podem ser falhas!\n')

    # Preparando série de derivada de segunda ordem para interpolação spline cúbica
    x, y, idx, j = [], [], {}, 0
    for i in range(len(mtz)):
        if mtz[i] == None or int(mtz[i]*100) == -99999: continue

        x.append(i)
        y.append(mtz[i])
        idx[j] = i
        j += 1

    yp1, ypn = 0.0, 0.0    #Estou chutando que a derivada de primeira ordem no início e no final da série são nulas
    y2 = [ -0.5 ]
    u  = [ (3.0/(x[1]-x[0])) * ((y[1]-y[0])/(x[1]-x[0]) - yp1) ]

    for i in range(1,len(x)-1):
        sig = (x[i] - x[i-1]) / float(x[i+1] - x[i-1])
        p   = sig * y2[i-1] + 2.0

        aux = (sig-1.0)/p
        y2.append(aux)

        aux = (6.0 * ( (y[i+1]-y[i])/(x[i+1]-x[i]) - (y[i]-y[i-1])/(x[i]-x[i-1]) ) / (x[i+1]-x[i-1]) - sig * u[i-1]) / p
        u.append(aux)

    qn = 0.5
    un = (3./(x[-1]-x[-2])) * (ypn - (y[-1]-y[-2])/(x[-1]-x[-2]))
    aux = (un - qn*u[-1]) / (qn*y2[-1] + 1.0)
    y2.append(aux)

    for k in range(len(x)-2,0,-1):
        y2[k] = y2[k] * y2[k+1] + u[k]


    # Construindo nova lista de dados
    mtz2, j = [mtz[0]], 0
    for i in range(1,len(mtz)):
        if i == idx[j+1]:
            mtz2.append(mtz[i])
            j += 1
        else:
        
            # Interpolando dados ausentes com spline cúbica
            h = float( x[j+1] - x[j] )
            A = (x[j+1] - i) / h
            B = (i - x[j]) / h
            yi = A*y[j] + B*y[j+1] + ( (A**3 - A)*y2[j] + (B**3 - B)*y2[j+1] ) * (h**2) / 6.0
            mtz2.append(yi)

    del mtz, x, y, y2, u
    return mtz2




def ler_arquivo(nome,chave=None):
    """ Lê todos os dados de um arquivo, ignorando linhas começando com '#', utilizando a função multisplit() para separar os dados. A variável de entrada 'nome' deve conter o string com o caminho para acessar o arquivo de dados. A variável 'chave' exerce as funções abaixo descritas:
    chave = None
        Retorna um lista contendo os dados lidos em sub-listas para cada linha do arquivo.
    chave = int
        Retorna um dicionário indexado pela variável na coluna cuja posição corresponde ao valor do inteiro fornecido.
    chave = ['date',int,int,int]
        Retorna um dicionário indexado por variáveis do tipo 'date' sendo que a posição das colunas de ano, mês e dia devem ser fornecidas, exatamente nesta ordem.
    chave = ['datetime',int,int,int,int,<int>,<int>]
        Retorna um dicionário indexado por variáveis do tipo 'datetime' sendo que a posição das colunas de ano, mês, dia, hora, minuto e segundo devem ser fornecidos, nesta ordem, em sequência da lista 'chave'. Os campos de minuto e segundo são opcionais. Se não forem fornecidos na lista 'chave' utilizará o valor 0 para os mesmos.

    Atenção! Nas situações em que 'chave' for diferente de None, a função irá SUBSTITUIR o conteúdo no dicionário quando houver recorrência da variável indexadora do dicionário. Por exemplo, em arquivos com séries de dados de vários postos, se o campo de datahora for utilizado como indexador, ao reencontrar duas ou mais linhas com o mesmo valor da datahora, apenas o conteúdo da última linha lida será armazenado no dicionário que esta função retornará.
"""
    arq = open(nome,'r')

    # Retornar matriz com elementos da linha em uma lista
    if chave == None:
        mtz = []
        for L in arq.readlines():
            if len(L) <= 1 or L[0] == '#': continue
            L = multisplit(L)
            mtz.append(L)

        arq.close()
        return mtz


    # Situações onde será retornado um dicionário
    if chave != None:
        mtz = {}


    # Retornar dicionário indexado pelos elementos da coluna de nº 'chave' (1ª coluna = 0).
    #Os demais elementos são agrupados em uma lista.
    if type(chave).__name__ == 'int':
        mtz = {}
        for L in arq.readlines():
            if len(L) <= 1 or L[0] == '#': continue
            L = multisplit(L)
            aux1 = L[chave]
            L.pop(chave)
            mtz[aux1] = L

        arq.close()
        return mtz


    # Situações onde será utilizada a data para indexar o dicionário
    if type(chave).__name__ == 'list':
        
        # Controle do conteúdo
        if chave[0] not in ['date','datetime']:
            raise IndexError('Primeiro elemento da lista "chave" deve ser "date" ou "datetime"')

        # Lista em ordem decrescente das colunas das variáveis de tempo
        ordem = sorted(chave[1:], reverse = True)

        # Retornar dicionário indexado por campo 'date'
        if chave[0] == 'date':
            for L in arq.readlines():
                if len(L) <= 1 or L[0] == '#': continue
                L = multisplit(L)
                dt = date(L[chave[1]], L[chave[2]], L[chave[3]])
                for i in ordem:
                    L.pop(i)
                mtz[dt] = L

        # Retornar dicionário indexado por campo 'datetime' sem campo de minuto e de segundo
        if chave[0] == 'datetime' and len(chave) == 5:
            for L in arq.readlines():
                if len(L) <= 1 or L[0] == '#': continue
                L = multisplit(L)
                dt = datetime(L[chave[1]], L[chave[2]], L[chave[3]], L[chave[4]], 0, 0)
                for i in ordem:
                    L.pop(i)
                mtz[dt] = L

        # Retornar dicionário indexado por campo 'datetime' sem campo de segundo
        if chave[0] == 'datetime' and len(chave) == 6:
            for L in arq.readlines():
                if len(L) <= 1 or L[0] == '#': continue
                L = multisplit(L)
                dt = datetime(L[chave[1]], L[chave[2]], L[chave[3]], L[chave[4]], L[chave[5]], 0)
                for i in ordem:
                    L.pop(i)
                mtz[dt] = L

        # Retornar dicionário indexado por campo 'datetime' com todos os elementos da datahora
        if chave[0] == 'datetime' and len(chave) == 7:
            for L in arq.readlines():
                if len(L) <= 1 or L[0] == '#': continue
                L = multisplit(L)
                dt = datetime(L[chave[1]], L[chave[2]], L[chave[3]], L[chave[4]], L[chave[5]], L[chave[6]])
                for i in ordem:
                    L.pop(i)
                mtz[dt] = L

        # Encerrando arquivo e retornado dicionário
        arq.close()
        return mtz


    # Se a lista 'chave' tiver um conteúdo diferente do especificado no caput da função retorna erro
    raise ValueError('Conteúdo inválido para indexar lista de elementos lido em cada linha.')




def serie_horaria(Lseries,intervalo=None,operacao='apendar',rejeito=-99):
    """ Versão otimizada de 'ler_arquivo' para armazenar dados de séries horárias.

    Variáveis de entrada:
> Lseries = Lista com sub-listas do tipo ['diretório/arquivo', col1, col2, ...], onde 'diretório/arquivo' é o caminho exato do arquivo
            de onde deseja-se ler a(s) série(s) horária(s). A posição da coluna onde estão os dados desejados, ou das colunas desejadas,
            devem ser expressadas por inteiros logo após o nome do arquivo. Veja os exemplos de uso mais abaixo.
> intevalo = Lista com dois elementos do tipo datetime para indicar a data/hora inicial e final, respectivamente, do período de dados
             desejado. Se não fornecido a função armazena toda a série presente no arquivo.
> operacao = 'apendar' para armazenar todas as séries lidas, 'somar' para retornar a série da soma das séries lidas ou 'media' para
             retornar a série da média dos dados de cada hora;
> rejeito  = valor limite, cujo dados menores que ele serão substituidos por None.

    Pré-supostos e configurações fixas:
> Os arquivos de dados horários seguem rigorosamente o formato: 'yyyy mm dd hh float float float ...', onde yyyy é o ano, mm é o mês,
  dd é o dia, hh é a hora (0 a 23) e float representa o dado da coluna;
> As colunas estão separadas por espaços, portanto garante-se que a operação .split() separará o conteúdo da linha no número correto de
  colunas do arquivo;
> Linhas contendo menos de 15 caracteres ou iniciadas com '#' não são linhas de dados;
> Registros ausentes nas séries horárias entre intervalo[0] e intervalo[1] serão substituídos por None, assim como os com valores menores
  que o valor de 'rejeito';
> Operações de soma e média não são executadas se uma ou mais variáveis tiverem o valor None. O respectivo valor da operação para a
  data/hora em questão será também None.

    Exemplos de uso:
1 - Armazenar a série de vazão observada (s/ preenchimento) na bacia 9 entre 2013-04-10 04:00:00 e 2013-07-14 04:00:00
    Lseries = [ ['/simepar/hidro/COPEL/SISPSHI2/Dados_Bacia/vazao_09.txt', 4] ]
    intervalo = [datetime(2013,4,10,4,0,0), datetime(2013,7,14,4,0,0)]

2 - Ler a média das cinco séries de chuva média observada na sub-bacia 21
    Lseries = [ ['/simepar/hidro/COPEL/SISPSHI2/Dados_Bacia/cmb_21.txt', 4, 5, 6, 7, 8] ]
    operacao = 'media'
    *OBS: Se a variável 'operacao' não fosse fornecida ou se fosse utilizado 'apendar', seria retornado um dicionário com os dados das
    cinco séries a cada hora.

3 - Gerar série de vazão montante em B07-Divisa (soma B01-Rio Negro e B03-São Bento) para o mesmo período do ex. 1
    Lseries = [ ['/simepar/hidro/COPEL/SISPSHI2/Dados_Bacia/vazao_01.txt', 5],
                ['/simepar/hidro/COPEL/SISPSHI2/Dados_Bacia/vazao_03.txt', 5] ]
    operacao = 'soma'
    *OBS2: Caso um dos dados envolvidos na soma seja None, então a soma será None.
"""
    # Contabilizando número de colunas que serão lidas e criando uma tag para cada série de dados
    ncol = 0
    tags = []    # Esta lista servirá para indexar a posição das séries de dados no dicionário
    for aux in Lseries:
        if type(aux).__name__ != 'list':
            erro = '\n     Lista de séries e coluna de dados está com indexação errada!'
            erro += '\n     Exemplo de indexação correta: Lseries = [ [arquivo, col, col, ...], [arquivo, col, col, ...] ]\n'
            raise IndexError(erro)
        for i in aux[1:]:
            tags.append( aux[0] + repr(i) )
            ncol += 1

    # Dicionário de dados
    mtz = {}

    # Leitura otimizada das séries se um intervalo de dados não foi especificado
    if intervalo == None:
        for aux in Lseries:

            # Arquivo de dados
            arq = open(aux[0], 'r')

            # Posição das colunas a serem lidas no dicionário de dados
            sub = []
            for i in aux[1:]:
                tag = aux[0] + repr(i)
                sub.append( tags.index(tag) )

            # Lendo série(s) de dado(s)
            for L in arq.readlines():
                if len(L) < 15 or L[0] == '#': continue
                L = L.split()
                dt = datetime(int(L[0]), int(L[1]), int(L[2]), int(L[3]), 0, 0)
                
                for j in range(1,len(aux)):
                    valor = float(L[aux[j]])
                    if valor < rejeito: valor = None

                    try:
                        mtz[dt][ sub[j-1] ] = valor
                    except KeyError:
                        mtz[dt] = [None for k in range(ncol)]
                        mtz[dt][ sub[j-1] ] = valor

            arq.close()

    # Leitura com restrição de intervalo
    else:
        for aux in Lseries:

            # Arquivo de dados
            arq = open(aux[0], 'r')

            # Posição das colunas a serem lidas no dicionário de dados
            sub = []
            for i in aux[1:]:
                tag = aux[0] + repr(i)
                sub.append( tags.index(tag) )

            # Lendo série(s) de dado(s)
            for L in arq.readlines():
                if len(L) < 15 or L[0] == '#': continue
                L = L.split()
                dt = datetime(int(L[0]), int(L[1]), int(L[2]), int(L[3]), 0, 0)
                
                # Armazenando dados ser atender à restrição de intervalo
                if intervalo[0] <= dt <= intervalo[1]:
                    for j in range(1,len(aux)):
                        valor = float(L[aux[j]])
                        if valor < rejeito: valor = None

                        try:
                            mtz[dt][ sub[j-1] ] = valor
                        except KeyError:
                            mtz[dt] = [None for k in range(ncol)]
                            mtz[dt][ sub[j-1] ] = valor

            arq.close()

    # Retornando dicionário de multiplas séries de dados
    if ncol > 1 and operacao == 'apendar':
        return mtz

    # Simplificando dicionário de dados se apenas 1 série de dados foi lida (acessar o dado por mtz[dt] ao invés de mtz[dt][0])
    if ncol == 1:
        mtz2 = {}
        for aux in mtz.items():
            mtz2[aux[0]] = aux[1][0]
        del mtz
        return mtz2

    # Realizando operação de soma ou média dos dados
    if operacao == 'somar' or operacao == 'media':
        mtz2 = {}

        # Calculando acumulado
        for aux in mtz.items():
            acm = 0.0
            for val in aux[1]:
                if val == None:
                    acm = None
                    break
                else:
                    acm += val
            mtz2[aux[0]] = acm
        del mtz

        if operacao == 'somar':
            return mtz2

        # Calculando média
        else:
            NCOL = float(ncol)
            for chave, valor in mtz2.items():
                if valor != None:
                    mtz2[chave] = valor/NCOL
            return mtz2

    # Se chegar aqui é porque algo deu errado
    erro  = '\n > Lseries   =' + repr(Lseries) + '\n'
    erro += ' > intervalo =' + repr(intervalo) + '\n'
    erro += ' > operacao  =' + repr(operacao) + '\n'
    erro += '\n     Verifique os argumentos de entrada e tente denovo!\n'
    raise IOError(erro)




def Preenchimento(dados):
    """ Função para preencher falhas de um intervalo utilizando dados de outra série, com ancoragem variando linearmente entre os
dados consistentes nas pontas do intervalo.

    Variável de entrada: lista 'dados'
 > dados[:]    = [idx, serie1[idx], serie2[idx]]
    > idx é o indexador das séries de dados. Tanto faz se é um datetime, inteiro ou qualquer outra coisa. Contudo, a função assume
    que o intervalo entre dados consecutivos é constante. Em outras palavras:
               dx(dados[1][0]-dados[0][0]) == dx(dados[2][0]-dados[1][0]) ... == dx(dados[-1][0]-dados[-2][0])
    > serie1[idx] é o valor do dado da série 1 no momento idx. Nesta série deve conter valores do tipo None para serem substituidos.
    > serie2[idx] é o valor do dado da série 2 no momento idx. Os valores dessa série serão ancorados aos da série 1 para preencher
    suas falhas.

    Descrição do método:
    Suponha que os dados fornecidos sejam:
        dados = [ [datetime(2013,2,25,15,0,0), 320.0, 310.0],
                  [datetime(2013,2,25,16,0,0),  None, 350.0],
                  [datetime(2013,2,25,17,0,0),  None, 375.0],
                  [datetime(2013,2,25,18,0,0),  None, 400.0],
                  [datetime(2013,2,25,19,0,0), 400.0, 420.0] ]
    Esta função irá substituir os valores None da série 1 ancorando os dados da série 2 aos dados consistentes da série 1 e aplicando
uma regressão linear entre a diferença no primeiro dado e no último dado. Matematicamente preciso resolver um sistema de equações
lineares:
        { A*0 + B = +10.0
        { A*4 + B = -20.0    (solução: A = 10, B = +10)
    Basta agora aplicar a equação linear de ANCORAGEM aos dados em x = 1, 2 e 3. Os valores a serem adicionados aos dados da série 2
para obter o respectivo da série 1 serão:
        x = 1, dy = 10*1 - 60 = -50 -> serie1(x=1) = serie2(x=1) + dy = 340.0
        x = 2, dy = 10*2 - 60 = -40 -> serie1(x=2) = serie2(x=2) + dy = 360.0
        x = 3, dy = 10*3 - 60 = -30 -> serie1(x=3) = serie2(x=3) + dy = 380.0
    Pronto!
    Observação: É possível que os dados de serie1 começem, ou terminem (mas nunca ambos), com None. Nestes casos utilizar-se-á um
valor de ancoragem constante, igual à diferença entre o dado consistente de serie1 e o respectivo de serie2

    Variável de saída: lista 'revisao'
 > revisao[:] = [idx, serie1[idx]], sendo que os valores None da série 1 já foram preenchidos. """
    if dados[0][1] == None and dados[-1][1] == None:
        erro = '\n    Para o preenchimento é preciso de um dado consistente em pelo menos uma das pontas do intervalo.\n'
        raise ValueError(erro)

    drev, ND = [], len(dados)

    # Dado consistente está na ponta final do intervalo
    if dados[0][1] == None:
        dq = dados[-1][1] - dados[-1][2]
        for i in range(ND):
            drev.append( [dados[i][0], dados[i][2]+dq] )
        return drev

    # Dado consistente está na ponta inicial do intervalo
    if dados[-1][1] == None:
        dq = dados[0][1] - dados[0][2]
        for i in range(ND):
            drev.append( [dados[i][0], dados[i][2]+dq] )
        return drev

    # Há dados consistentes nas duas pontas do intervalo -> ancoragem variando linearmente
    b = (dados[0][1] - dados[0][2])    # = dq(x=0)
    a = ((dados[-1][1] - dados[-1][2]) - b) / float(ND)
    for i in range(ND):
        dq = a*i + b
        drev.append( [dados[i][0], dados[i][2]+dq] )
    return drev




def grava_JSON(arquivo,mtz):
    """ Função para gravar séries de dados em formato JSON.
    
    Variáveis de entrada:
 > arquivo: string com o caminho/nome do arquivo onde serão gravados os dados em formato JSON;
 > mtz:     dicionário com a(s) série(s) de dados, indexado por variáveis datetime.
     > mtz.keys() = lista das variáveis que indexam o dicionário;
     > mtz.values() = lista com os dados das séries armazenadas em mtz.

    Esta função não retorna qualquer valor.
    """
    # Lista dos indexadores em ordem crescente
    datas = sorted(mtz.keys())
    ND = len(datas)
    
    # Contando número de séries de dados em mtz
    NS = len(mtz[datas[0]])
    if NS != len(mtz[datas[-1]]):
        erro = '\n     O dicionário de dados começa com %i séries mas termina com %i.\n' % (NS, len(mtz[datas[-1]]))
        raise IOError(erro)
    
    # Inicializando arquivo
    arq = open(arquivo,'w')
    arq.write('[')

    # Gravando série a série
    for j in range(NS):
        
        #Abrindo lista para a j-ésima série
        if j == 0:
            arq.write('[')
        else:
            arq.write('\n [')
        
        # Gravando os pares data/valor
        for i in range(ND):
            dt, valor = datas[i], mtz[datas[i]][j]
            
            """ O processo de escrita busca reproduzir um sistema de identação no arquivo p/ o site, facilitando a identificação
            de cada uma das séries de dados. """
            if i == 0:
                arq.write('[')
            else:
                arq.write('  [')

            if valor != None:
                arq.write('"%s",%9.3f]' % (dt, valor))
            else:
                arq.write('"%s",     null]' % datas[i])

            if i < ND-1:
                arq.write(',\n')

        if j == NS-1:
            arq.write(']\n')
        else:
            arq.write('],\n')

    # Encerrando arquivo de dados em formato JSON
    arq.write(']')
    arq.close()










