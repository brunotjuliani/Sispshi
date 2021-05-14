# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from operator import itemgetter
from os import path as os_path
from time import localtime
from sys import path as sys_path; sys_path.append('/simepar/hidro/COPEL/SISPSHI2/Bibliotecas')
from admin import *

""" Módulo moniguacu.py
    Reúne informações sobre pluviometros, postos fluviométricos (cota e vazão), sub-bacias do SISPSHI2 e métodos para estimar CMB."""




# +---------------------------------------------------------------------------------------------------------------------------------+
# |          DADOS/INFORMAÇÕES GERAIS                                                                                               |
# +-=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---+
base         = '/simepar/hidro/COPEL/SISPSHI2'
dir_curdesc  = '/simepar/hidro/COPEL/SISPSHI2/Curvas_Descarga/'
arq_malha    = '/simepar/hidro/COPEL/SISPSHI2/Dados_Bacias/malha_iguacu_4km.txt'
distmax_padrao = 55000 #55 km

mtz_pluvs_sispshi = [
#[ Código, Nome                         ,  Latitude, Longitude,  X UTM,   Y UTM, Alti, Grupos]
[25494905, u'Vossoroca'                 , -25.81660, -49.08330, 692138, 7143226,  851, [1]], #01
[25254905, u'Pinhais'                   , -25.41670, -49.13330, 687749, 7187597,  898, [1]], #02
[25264916, u'Curitiba'                  , -25.44817, -49.23033, 677945, 7184241,  922, [1]], #03
[26094923, u'Fragosos'                  , -26.15000, -49.38330, 661603, 7106699,  824, [1]], #04
[25474946, u'Lapa'                      , -25.78330, -49.76660, 623667, 7147735,  879, [2]], #05
[25564947, u'São Bento'                 , -25.93330, -49.78330, 621839, 7131137,  800, [2]], #06
[26064948, u'Rio Negro'                 , -26.10000, -49.80000, 619997, 7112689,  798, [2]], #07
[25334953, u'Porto Amazonas'            , -25.55000, -49.88330, 612184, 7173678,  789, [2]], #08
[25135001, u'Ponta Grossa'              , -25.01329, -50.15198, 585575, 7233422,  848, [2]], #09
[26055019, u'Divisa'                    , -26.08330, -50.31660, 568346, 7114912,  762, [3]], #10
[25525023, u'São Mateus do Sul'         , -25.86660, -50.38330, 561788, 7138944,  783, [3]], #11
[25555031, u'Pontilhão'                 , -25.91660, -50.51660, 548412, 7133463,  765, [3]], #12
[26025035, u'Fluviópolis'               , -26.03330, -50.58330, 541691, 7120562,  764, [3]], #13
[25275035, u'Fernandes Pinheiro'        , -25.45000, -50.58330, 541895, 7185157,  880, [3]], #14
[26355045, u'Foz do Cachoeira'          , -26.58330, -50.75000, 524895, 7059692,  902, [4]], #15
[26105047, u'Foz do Timbó'              , -26.29452, -50.89522, 510462, 7091697,  747, [4]], #16
[26125049, u'Santa Cruz do Timbó'       , -26.38330, -50.86660, 513307, 7081860,  750, [4]], #17
[26145104, u'União da Vitória Hid.'     , -26.23330, -51.06660, 493348, 7098478,  748, [4, 5]], #18
[26145103, u'União da Vitória Met.'     , -26.23330, -51.06660, 493348, 7098478,  748, [4, 5]], #19
[26025109, u'Palmital do Meio'          , -26.03330, -51.15000, 484993, 7120620,  909, [5]], #20
[26105114, u'Porto Vitória'             , -26.16660, -51.23330, 476685, 7105845,  856, [5]], #21
[26225115, u'Jangada'                   , -26.36660, -51.25000, 475059, 7083692, 1020, [5]], #22
[25485116, u'Madeireira Gavazzoni'      , -25.80000, -51.26660, 473274, 7146438,  838, [6]], #23
[25335129, u'Entre Rios'                , -25.55000, -51.48330, 451449, 7174061, 1116, [6]], #24
[25215130, u'Guarapuava'                , -25.35000, -51.50000, 449689, 7196202, 1066, [6]], #25
[26005139, u'Foz do Areia Hid.'         , -26.00000, -51.65000, 434949, 7124154,  720, [6]], #26
[26055139, u'Foz do Areia Met.'         , -26.08330, -51.65000, 434995, 7114929, 1031, [6]], #27
[26055155, u'Solais Novo'               , -26.08330, -51.91660, 408331, 7114769,  786, [7]], #28
[25385157, u'Pinhão'                    , -25.64940, -51.96250, 403388, 7162791,  841, [7]], #29
[26285158, u'Palmas'                    , -26.46670, -51.96670, 403638, 7072268, 1039, [7]], #30
[25475206, u'Segredo'                   , -25.78000, -52.10000, 389706, 7148219,  706, [7]], #31
[26015237, u'Porto Palmeirinha'         , -26.02910, -52.62830, 337070, 7120077,  509, [8]], #32
[26075241, u'Pato Branco'               , -26.11660, -52.68330, 331691, 7110315,  705, [8]], #33
[25465256, u'Águas do Verê'             , -25.76660, -52.93330, 306116, 7148741,  466, [8, 9]], #34
[25315301, u'Salto Osório'              , -25.51670, -53.01670, 297328, 7176300,  398, [9]], #35
[25235306, u'Porto Santo Antônio'       , -25.38330, -53.10000, 288722, 7190949,  379, [9]], #36
[25345306, u'Foz do Chopim'             , -25.57130, -53.11350, 287694, 7170100,  357, [9]], #37
[25345816, u'Balsa Jaracatiá'           , -25.58320, -53.26680, 272312, 7168527,  328, [10]], #38
[25315329, u'Salto Caxias Met.'         , -25.51660, -53.48330, 250419, 7175517,  348, [10]], #39
[25325330, u'Salto Caxias Hid.'         , -25.53330, -53.50000, 248775, 7173635,  338, ['off']], #40
[25345331, u'Nova Prata do Iguaçu'      , -25.56660, -53.51660, 247176, 7169914,  355, ['off']], #41
[24535333, u'Cascavel'                  , -24.88330, -53.55000, 242382, 7245561,  665, [11]], #42
[25345435, u'Porto Capanema'            , -25.56660, -53.79230, 217686, 7169322,  236, [11]], #43
[25115408, u'São Miguel do Iguaçu'      , -25.35280, -54.25460, 172411, 7191999,  283, [11]], #44
[25415426, u'Salto Cataratas'           , -25.68330, -54.43330, 155358, 7154909,  233, ['off']], #45
[25245437, u'Foz do Iguaçu'             , -25.40000, -54.61670, 136076, 7185829,  222, ['off']], #46 #ms: grupo 11, desligando
[25325329, u'Reservatório Salto Caxias' , -25.53330, -53.48330, 250454, 7173667,  326, [10]], #47
[25315021, u'Boa Vista da Aparecida'    , -25.52250, -53.35580, 263250, 7175097,  368, [10]], #48
[26055305, u'Francisco Beltrão'         , -26.05930, -53.05080, 294837, 7116136,  552, [8]], #49
[25825217, u'Coronel Domingos Soares'   , -25.82750, -52.17061, 382672, 7142897,  608, [7]], #50
[25755210, u'Derivação do Rio Jordão'   , -25.75922, -52.10889, 388795, 7150513,  682, [7]], #51
[26065150, u'Bituruna'                  , -26.06390, -51.50830, 449158, 7117141,  720, [6]]  #52
]

mtz_pfluvs_sispshi = [
#[codigo, nome, Hmed, Hdp, Hmax, Hmin, DH15M, DH60M, NDautcor, Qmed, Qdp, Qmax, Q20%, Q80%, Qmin, DQ15M, DQ60M]
[26064948, 'Rio Negro',           1.84, 1.46, 13.10, 0.15, 0.27, 0.34, 25,  76.1,  70.9,  712.0, 106.9,  32.2, 11.2,  10.0,  15.2],
[25334953, 'Porto Amazonas',      1.72, 0.79,  6.91, 0.86, 0.58, 1.57, 15,  80.4,  64.9,  635.5, 112.0,  31.5,  8.6,  42.8, 112.8],
[25564947, 'São Bento',           1.46, 0.91,  5.15, 0.08, 0.10, 0.18, 35,  34.7,  24.9,  202.0,  50.7,  15.7,  4.9,   4.8,  10.1],
[25555031, 'Pontilhão',           2.43, 1.80,  8.76, 0.10, 0.09, 0.16, 40,  51.8,  46.2,  235.8,  93.4,  14.0,  3.0,   1.6,   4.0],
[26125049, 'Santa Cruz do Timbó', 3.08, 1.53,  9.30, 0.91, 0.20, 0.48, 29,  79.1,  85.0,  903.4, 119.3,  19.5,  5.9,  73.6,  77.2],
[26105047, 'Foz do Timbó',        2.80, 1.46,  9.00, 0.68, 0.08, 0.16, 71,  None,  None,   None,  None,  None, None,  None,  None],
[25525023, 'São Mateus do Sul',   1.58, 1.16,  6.58, 0.15, 0.10, 0.14, 46, 109.9, 113.0, 1324.8, 157.7,  37.3, 16.5,  15.3,  37.2],
[26055019, 'Divisa',              2.39, 1.59,  8.19, 0.28, 0.06, 0.12, 48, 165.4, 142.7, 1104.5, 235.8,  64.6, 21.9,  17.9,  17.9],
[26025035, 'Fluviopolis',         1.73, 1.09,  6.74, 0.33, 0.05, 0.08, 57, 407.9, 334.0, 2082.8, 622.3, 159.2, 44.0,  15.7,  24.4],
[26145104, 'União da Vitória',    2.80, 1.13,  8.00, 1.31, 0.09, 0.10, 67, 542.1, 456.0, 2737.9, 814.8, 205.7, 49.9,  52.1,  54.1],
[26105114, 'Porto Vitória',       1.59, 0.62,  4.00, 0.12, 0.06, 0.07, 53,  None,  None,   None,  None,  None, None,  None,  None],
[25485116, 'Mad. Gavazzoni',      1.42, 0.37,  8.30, 0.90, 0.25, 0.43,  9,  28.4,  38.5,  811.8, 38.77,  9.18,  2.2,  35.9, 101.3],
[26225115, 'Jangada',             0.84, 0.33,  2.92, 0.32, 0.19, 0.49, 10,  34.6,  47.2,  465.6, 40.20,  8.00,  0.5,  30.2,  76.4],
[26055155, 'Solais Novo',         0.67, 0.40,  4.70, 0.11, 0.46, 0.79, 11,  46.4,  52.6,  492.7, 64.45, 14.78,  1.7,  67.4, 113.0],
[25235306, 'Porto Santo Antônio', 0.70, 0.51,  9.30, 0.05, 0.32, 0.81, 21,  27.5,  50.0,  728.4, 48.25,  4.70,  0.1,  44.8, 147.5],
[25465256, 'Águas do Verê',       1.21, 0.50,  4.63, 0.59, 0.18, 0.23, 17, 214.8, 253.5, 2850.8, 291.8, 62.14, 16.7, 182.4, 186.2],
[25345435, 'Porto Capanema',      2.78, 1.04, 14.80, 0.86, 0.69, 0.73,  7, 1837., 1514., 18236., 2332., 831.5, 116., 424.8, 1505.],
[25685442, 'Hotel Cataratas',     None, None,  8.00, 0.50, 0.22, 0.64, 11,  None,  None, 30193., 5000., 897.0, 209.8, 960.0, 3800.]
]

mtz_bacias_sispshi = [
#[número, nome, área incremental, área total, sub-bacias a montante, X UTM, Y UTM, código posto da exutória]
[ 1, 'Rio Negro'                               , 3379.0,  3379.0,        [], 646419, 7093745, 26064948],
[ 2, 'Porto Amazonas'                          , 3662.0,  3662.0,        [], 662548, 7173249, 25334953],
[ 3, 'São Bento'                               , 2012.0,  2012.0,        [], 653238, 7135720, 25564947],
[ 4, 'Pontilhão'                               , 2190.0,  2190.0,        [], 528613, 7156793, 25555031],
[ 5, 'Santa Cruz do Timbó'                     , 2698.0,  2698.0,        [], 528095, 7058765, 26125049],
[ 6, 'São Mateus do Sul'                       , 2403.0,  6065.0,       [2], 589071, 7155202, 25525023],
[ 7, 'Divisa'                                  , 2579.0,  7970.0,     [1,3], 598743, 7109682, 26055019],
[ 8, 'Fluviópolis'                             , 2075.0, 18300.0,   [4,6,7], 563935, 7089779, 26025035],
[ 9, 'União da Vitória'                        , 2995.0, 23993.0,     [5,8], 523553, 7102915, 26145104],
[10, 'Madereira Gavazzoni'                     ,  911.0,   911.0,        [], 487219, 7158370, 25485116],
[11, 'Jangada'                                 , 1100.0,  1100.0,        [], 470156, 7063417, 26225115],
[12, 'Foz do Areia'                            , 3969.0, 29973.0, [9,10,11], 469188, 7117789, None],
[13, 'Solais Novo'                             , 1616.0,  1616.0,        [], 429462, 7090059, 26055155],
[14, 'Porto Santo Antônio'                     , 1086.0,  1086.0,        [], 308457, 7206903, 25235306],
[15, 'Águas do Verê'                           , 6696.0,  6696.0,        [], 343511, 7099866, 25465256],
[16, 'Incremental Foz do Areia - Segredo'      , 2573.0,  4189.0,      [13], 401018, 7123441, None],
[17, 'Foz do Chopim'                           ,  777.0,  7473.0,      [15], 296842, 7150092, None],
[18, 'Santa Clara'                             , 3912.0,  3912.0,        [], 442416, 7181201, None],
[19, 'Incremental Salto Osório - Salto Caxias' , 3642.0,  3642.0,        [], 271938, 7168999, None],
[20, 'Porto Capanema'                          , 4521.0, 62519.0,      [19], 245856, 7163960, 25345435],
[21, 'Hotel Cataratas'                         , 4610.0, 67129.0,      [20], 199649, 7166598, 25685442]
]

# +-=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---+








# +---------------------------------------------------------------------------------------------------------------------------------+
# |          CLASSES DE VARIÁVEIS                                                                                                   |
# +-=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---+

class pluviometro(object):
    """ Classe para agregar na mesma variável as informações do pluviometro.
    var = pluviometro()
    var.codigo      |int|: Código SIMEPAR (8 dígitos);
    var.nome     |string|: Nome do posto pluviométrico;
    var.latitude  |float|: Latitude em coordenadas geográficas;
    var.longitude |float|: Longitude em coordenadas geográficas;
    var.Xutm        |int|: Latitude em UTM;
    var.Yutm        |int|: Longitude em UTM."""
    def __init__(self,info=None):
        if type(info).__name__ == 'list':
            self.codigo = info[0]
            self.nome   = info[1]
            self.latitude  = info[2]
            self.longitude = info[3]
            self.Xutm   = info[4]
            self.Yutm   = info[5]
            self.Alt    = info[6]
            try:
                self.Grupos = info[7]
            except IndexError:
                self.Grupos = None
        else:
            self.codigo = None
            self.nome   = None
            self.latitude  = None
            self.longitude = None
            self.Xutm = None
            self.Yutm = None
            self.Alt = None
            self.Grupos = None




class posto_fluvio(object):
    """ Classe para agregar na mesma variável as informações do posto de monitoramento fluviométrico.
    var = posto_fluvio()
    var.codigo    |int|: Código SIMEPAR (8 dígitos);
    var.nome   |string|: Nome do posto fluviométrico;
    var.Hmed, var.Hdp, var.Hmax, var.Hmin |float|: Média, desvio-padrão, máximo, mínimo da série de cota da régua (H[m]);
    var.Qmed, var.Qdp, var.Qmax, var.Qmin |float|: Média, desvio-padrão, máximo, mínimo da série de vazão (Q[m³/s]);
    var.DH15, var.DQ15 |float|: Maior Delta possível em 15 minutos para cota de régua (H) e vazão (Q);
    var.DH60, var.DQ60 |float|: Maior Delta possível em 60 minutos para cota de régua (H) e vazão (Q);
    var.NDAC      |int|: Número de Dados na série de 15 minutos com Auto-Correlação superior a 0,995;
    var.Qalta   |float|: Valor a partir do qual se considera em vazão alta. Atualmente utiliza a vazão de 20% da curva de permanência;
    var.Qbaixa  |float|: Valor abaixo do qual se considerada em vazão baixa. Atualmente utiliza a vazão de 80% da curva de permanência."""
    def __init__(self,info=None):
        if type(info).__name__ == 'list':
            self.codigo = info[0]
            self.nome   = info[1]
            self.Hmed   = info[2]
            self.Hdp    = info[3]
            self.Hmax   = info[4]
            self.Hmin   = info[5]
            self.DH15   = info[6]
            self.DH60   = info[7]
            self.NDAC   = info[8]
            self.Qmed   = info[9]
            self.Qdp    = info[10]
            self.Qmax   = info[11]
            self.Qalta  = info[12]
            self.Qbaixa = info[13]
            self.Qmin   = info[14]
            self.DQ15   = info[15]
            self.DQ60   = info[16]
        else:
            self.codigo = None
            self.nome   = None




class ponto_de_malha(object):
    """ Classe para agregar na mesma variável as coordenadas do ponto de malha, em UTM, e o número da sub-bacia.
    var = ponto_de_malha()
    var.lin            |int|: Linha da posição do ponto na matriz da malha regular;
    var.col            |int|: Coluna da posição do ponto na matriz da malha regular;
    var.Xutm           |int|: Coordenada UTM da longitude do ponto;
    var.Yutm           |int|: Coordenada UTM da latitude do ponto;
    var.Alt            |int|: Altitude do ponto (SRTM);
    var.bacia          |int|: Número da bacia na qual o ponto está inserido."""
    def __init__(self, info = None):
        if type(info).__name__ == 'list':
            self.lin  = info[0]
            self.col  = info[1]
            self.Xutm = info[2]
            self.Yutm = info[3]
            self.Alt  = info[4]
            self.bacia = info[5]
        else:
            self.lin  = None
            self.col  = None
            self.Xutm = None
            self.Yutm = None
            self.Alt  = None
            self.bacia = None




class bacia(object):
    """ Classe para agregar na mesma variável as informações da bacia hidrográfica.
    var = bacia()
    var.numero          |int|: Número da bacia no sistema de previsão;
    var.nome         |string|: Nome da bacia no sistema de previsão;
    var.areainc       |float|: Área incremental de contribuição da bacia (km2);
    var.areatot       |float|: Área total de contribuição da bacia (km2);
    var.montante       |list|: Lista com o número das bacias contribuintes imediatamente a montante."""
    def __init__(self,info=None):
        """ Inicializar atributos básicos da classe. """
        if type(info).__name__ == 'list':
            self.numero   = info[0]
            self.nome     = info[1]
            self.areainc  = info[2]
            self.areatot  = info[3]
            self.montante = info[4]
            self.Xutm     = info[5]
            self.Yutm     = info[6]
            self.codigo   = info[7]
        else:
            self.numero   = None
            self.nome     = None
            self.areainc  = None
            self.areatot  = None
            self.montante = None
            self.Xutm     = None
            self.Yutm     = None
            self.codigo   = None

    def informacoes_espaciais(self, distmax = distmax_padrao):
        """ Incluir atributos de informações espaciais, sendo:
        self.malha     |list|: Lista de variáveis ponto_de_malha() para os pontos da malha obtidos no arquivo 'arq_malha' que pertencem à
                               bacia;
        self.pluvsprox |list|: Lista com pares [codigo, distancia] para os pluviometros da 'mtz_pluvs_sispshi' que estão próximos à bacia."""
        self.malha = []
        self.pluvsprox = []
        aux = []

        arq = open(arq_malha, 'r')
        for linha in arq.readlines():
            linha = map(int, linha.split())

            #Processa o ponto de malha se for pertencente à bacia em questão
            if linha[-1] == self.numero:
                pto = ponto_de_malha(linha)         #Utilizando classe ponto_de_malha() para agregar as informações na variável 'pto'
                pto.pluvsprox = []                  #Geração de atributo dinâmica. No caso, adicionando o atributo 'pluvsprox' para a
                                                    #variável 'pto'.
                #Localizando pluviometros próximos ao ponto de malha.
                for itens in mtz_pluvs_sispshi:
                    pluv = pluviometro(itens)           #Agregando informações na variável 'pluv' que é da classe pluviometro().

                    dist = ( (pto.Xutm - pluv.Xutm)**2 + (pto.Yutm - pluv.Yutm)**2 )**0.5
                    if dist <= distmax:
                        pto.pluvsprox.append([pluv.codigo, dist])

                        #Adicionando pluviometro como próximo à bacia.
                        if pluv.codigo not in aux:
                            dist = ( (self.Xutm - pluv.Xutm)**2 + (self.Yutm - pluv.Yutm)**2 )**0.5
                            self.pluvsprox.append([pluv.codigo, dist])
                            aux.append(pluv.codigo)

                #Ordenando lista de pluviometros em ordem crescente da distância antes de adicioná-lo à malha.
                pto.pluvsprox = sorted(pto.pluvsprox, key = itemgetter(1))
                self.malha.append(pto)

        #Ordenando a lista de pluviometros da bacia e fechando o arquivo de malha.
        self.pluvsprox = sorted(self.pluvsprox, key = itemgetter(1))
        arq.close()
        
    """ COMENTÁRIO: Tanto para a variável da classe bacia() e da classe ponto_de_malha() foi criado o atributo "self.pluvsprox" que é uma lista dos pluviometros mais próximos. 
Entretanto, no atributo de ponto_de_malha() os pluviometros próximos são os que estão em um raio de 'distmax' metros do ponto da malha em si. Para bacia() a lista é construida 
adicionando-se todos os pluviometros identificados como próximos ao conjunto dos pontos de malha internos à bacia. Analogamente é o mesmo que a criar uma lista dos pluviometros que 
estão a até 'distmax' metros do contorno da bacia. Todavia o valor de distância armazenado no par [codigo, distancia] é a distância do pluviometro ao centro da bacia. """
   

    def postos_montante(self):
        """ Função para gerar uma lista com o código dos postos hidrológicos que representam a exutória das sub-bacias que compõem a
        contribuição de montante. """
        if len(self.montante) == 0: return []
        
        aux = []
        for bac in self.montante:
            for itens in mtz_bacias_sispshi:
                if bac == itens[0]:
                    aux.append(itens[7])
                    break

        return aux




class curva_descarga(object):
    """ Classe para agregar na mesma variável os registros de curvas de descarga para um posto hidrológico.
    var = curdesc(XXXXXXXX), onde XXXXXXXX é o código simepar (8 dígitos) do posto.
    var.periodos       |list|: Lista com pares datetime do início e final da validade de cada curva de descarga
    var.curvas         |list|: Lista das listas contendo os pares nivel/vazão de cada curva de descarga."""
    def __init__(self,cod):
        """ Armazena os registros das curvas de descarga presentes no arquivo 'curdesc_XXXXXXXX.txt nos atributos da classe. """
        self.codigo   = cod
        self.periodos = []
        self.curvas   = []

        #Abrindo arquivo com registros da(s) curva(s) de descarga, se houver CD para o posto fluviométrico
        try:
            arq = open(dir_curdesc + str('curdesc_%8i.txt' % cod), 'r')
        except IOError:
            F = FluvSISPSHI(cod)
            raise IOError(str('Não há curva de descarga para %s (%i)' % (F.nome, F.codigo)))

        # Lendo conteúdo da CD
        for lin in arq.readlines():
                
            #Ignorando linhas sem dados
            if len(lin) < 10: continue
            
            #Identificando variáveis da linha lida
            lin = lin.split('|')
            dt0 = datetime(int(lin[0][1:5]), int(lin[0][6:8]), int(lin[0][9:11]), int(lin[0][12:14]), int(lin[0][15:17]), int(lin[0][18:20]))
            dtN = datetime(int(lin[1][1:5]), int(lin[1][6:8]), int(lin[1][9:11]), int(lin[1][12:14]), int(lin[1][15:17]), int(lin[1][18:20]))
            niv = float(lin[-2])
            vaz = float(lin[-1])

            #Acrescentando nova curva de descarga se encontrar um novo período de validade '[dt0,dtN]'
            if [dt0, dtN] not in self.periodos:
                self.periodos.append([dt0, dtN])
                self.curvas.append([])

            #Indexador de posição da curva de descarga na lista 'self.curvas' deve estar relacionado à posição do período de validade
            #'[dt0, dtN]' na lista 'self.periodos'
            nc = self.periodos.index([dt0, dtN])
            self.curvas[nc].append([niv,vaz])
            
        arq.close()
        
        # Séries de dados adicionais para postos com remanso
        if cod == 26125049:
            self.relacao1 = []
            arq = open(dir_curdesc + 'dadosinterp.txt', 'r')
            for lin in arq.readlines():
                self.relacao1.append(map(float,lin.split()))

        if cod == 26145104:
            self.relacao1 = []
            arq = open(dir_curdesc + 'spuvpv1.txt','r')         # No código fonte em Pascal para cálculo da vazão em UVA, embora o
            for lin in arq.readlines():                         #arquivo _spuvpv1.bin (equivalente ao spuvpv1.txt) seja lido, seus
                self.relacao1.append(map(float,lin.split()))    #dados não são aplicados em nenhum lugar do programa.

            self.relacao2 = []
            arq = open(dir_curdesc + 'spuvpv2.txt','r')
            for lin in arq.readlines():
                self.relacao2.append(map(float,lin.split()))

            self.relacao3 = []
            arq = open(dir_curdesc + 'mquvpvx.txt','r')
            for lin in arq.readlines():                        # Inverto a ordem da primeira com a segunda coluna do arquivo para
                aux = map(float,lin.split())                   #que o nível em Porto Vitória seja o primeiro elemento da sub-lista
                self.relacao3.append([aux[1], aux[0], aux[2]]) #tal como na sequencia dos dados lidos de 'spuvpv2.txt'.
            
            #Usando curva revista em 2012
            self.periodos = [[datetime(1931,1,1,0,0,0), datetime(2199,12,31,23,59,59)]]
            self.curvas = [[]]
            arq = open(dir_curdesc + 'curva65310000_2012.txt', 'r')
            for lin in arq:
                self.curvas[0].append(map(float,lin.split()))
            arq.close()
            

    def index_curva(self, dt):
        """ Indentifica o indexador da curva de descarga, no período de validade que contenha a datahora 'dt', para acessar a lista correta de pares nivel/vazão."""
        if dt == None:
            dt = datetime.now()
        nc = -1
        for d0, dN in self.periodos:
            if d0 <= dt <= dN:
                nc = self.periodos.index([d0,dN])
        if nc == -1:
            raise ValueError(str("Não há curva de descarga válida para %s." % dt))
        else:
            return nc

    def vazao(self, niv, dt=None):
        """ Retorna o valor de vazão para o nível 'niv' informado, de acordo com a curva de descarga válida no momento 'dt'. Se 'dt' não for fornecido será utilizada a curva de descarga válida atualmente."""
        # Vazão com remanso em Santa Cruz do Timbó
        if self.codigo == 26125049:
            if type(niv).__name__ != 'list':
                raise TypeError ("Vazão em Santa Cruz do Timbó precisa de LISTA com nivel em Foz do Timbó e em Santa Cruz")
            elif len(niv) != 2:
                raise IndexError ("Vazão em Santa Cruz do Timbó precisa de lista com nivel EM Foz do Timbó E EM Santa Cruz.")

            nc    = self.index_curva(dt)
            curva = self.curvas[nc]
            Hft, Hsc  = niv[0], niv[1]
            
            # Testando limite aceitável de nível em Santa Cruz do Timbó
            if Hsc < curva[0][0] or Hsc > curva[-1][0]:
                return None

            # Testando nivel em Foz do Timbó: Utiliza limites de SCT para teste pois aparentam utilizar a mesma referência altimétrica
            if Hft < curva[0][0] or Hft > curva[-1][0]:
                return None

            # Calculando vazão com remanso
            # Passo 1: Obter a diferença de nivel entre estações e aplicando fatores de ajuste
            Dref = (Hsc - Hft + 0.25) * 2.0
            if Dref <= 0.001: return None
            # Passo 2: Obter fator de correção da vazão
            try:
                fator = obter_linear(Dref,self.relacao1)
            except ValueError:
                return None
            # Passo 3: Obter vazão em SCT pela curva de descarga do posto
            Vsct = obter_linear(Hsc,curva)
            # Passo 4: Retornando vazão com ajuste de remanso
            return Vsct*fator

        # Vazão com remanso (ou não) em União da Vitória
        if self.codigo == 26145104:
            if type(niv).__name__ != 'list':
                raise TypeError ("Vazão em União da Vitória precisa de LISTA com nivel em Porto Vitória e em União da Vitória")
            elif len(niv) != 2:
                raise IndexError ("Vazão em União da Vitória precisa de lista com nivel EM Porto Vitória E EM União da Vitória.")

            nc = self.index_curva(dt)
            curva = self.curvas[nc]
            Hpv, Huv = niv[0], niv[1]

            # Testando limite aceitável de nível em União da Vitória
            if Huv < curva[0][0] or Huv > curva[-1][0]:
                return None

            # Testando nivel em Porto Vitória: Utiliza limites com base no histórico do monitoramento de nível em Porto Vitória
            if Hpv < -1.0 or Hpv > 5.24:
                return None

            # Situações sem remanso
            if Hpv < 1.0:
                return obter_linear(round(Huv,2),curva)

            # Situações com remanso
            else:
                Hpv = round(Hpv*100,0)
                Huv = round(Huv*100,0)
                Huvc = splcaly(self.relacao2, Hpv)
                
                if Huv > Huvc:
                    Hpvc = splcalx(self.relacao2, Huv)
                    return multqua(self.relacao3, Hpvc, Huv)

                else:
                    return multqua(self.relacao3, Hpv, Huv)

        # Vazão por curva de descarga nos demais postos
        else:
            nc    = self.index_curva(dt)
            curva = self.curvas[nc]

            if niv < curva[0][0] or niv > curva[-1][0]:
                return None

            return obter_linear(niv,curva)


    def nivel(self, vaz, dt=None):
      
        """ Retorna o valor de nível para a vazão 'vaz' informada, de acordo com a curva de descarga válida no momento 'dt'. Se 'dt' não for fornecido será utilizada a curva de descarga válida atualmente."""
        nc    = self.index_curva(dt)
        curva = self.curvas[nc]

        
        ### INTERVENCAO AS, maio-2020 ###
        #if vaz < curva[0][1] or vaz > curva[-1][1]:
	#  return None
        if vaz < curva[0][1]:
	  return curva[0][0]
	
	elif vaz > curva[-1][1]:
	  return curva[-1][0]
        ### INTERVENCAO AS, maio-2020 ###

        
        for i in range(len(curva)-1):
            if curva[i][1] <= vaz <= curva[i+1][1]:
                A = (curva[i+1][0] - curva[i][0]) / (curva[i+1][1] - curva[i][1])
                B = curva[i][0] - A*curva[i][1]
                return A*vaz + B
        raise IndexError("Não deveria ter chegado aqui! Rever curva de descarga.")
	return 0
      
    def limites(self, dt=None):
        """ Retorna os pares nivel/vazao do limite inferior e superior da curva de descarga válida no momento 'dt'. Se 'dt' não for fornecido será utilizada a curva de descarga válida atualmente."""
        nc    = self.index_curva(dt)
        curva = self.curvas[nc]
        return [curva[0][0], curva[0][1]], [curva[-1][0], curva[-1][1]]

# +-=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---+








# +---------------------------------------------------------------------------------------------------------------------------------+
# |          FUNÇÕES PARA CALCULO DE VAZÃO COM REMANSO EM UNIÃO DA VITÓRIA                                                          |
# +-=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---+

def splcaly(dados,xc):

    j, n = 0, len(dados)
    while xc > dados[j][0] and j < n:
        j += 1

    j -= 1

    h = dados[j+1][0] - dados[j][0]

    k = dados[j+1][0] - xc
    c = dados[j][2]*(k/h)*(k/6.0)*k

    k = xc - dados[j][0]
    d = dados[j+1][2]*(k/h)*(k/6.0)*k

    a = (dados[j+1][1] - dados[j][1])/h - h*(dados[j+1][2] - dados[j][2])/6.0
    a = a*k
    b = dados[j][1] - dados[j][2]*h*h/6.0

    yc = a + b + c + d
    return yc


def splcalx(dados,yc):

    j, n = 0, len(dados)
    while yc > dados[j][1] and j < n:
        j += 1

    j -= 1

    h = dados[j+1][0] - dados[j][0]

    a = (dados[j+1][1] - dados[j][1])/h - h*(dados[j+1][2] - dados[j][2])/6.0
    b = dados[j][1] - dados[j][2]*h*h/6.0

    xcn, xc = dados[j][0], dados[j][0] + 100.0 # Inicializa 'xc' em condição que atenda o statement do ciclo 'while' abaixo
    niter = 0
    while abs(xcn - xc) >= 1.0e-3 and niter < 100:

        niter += 1
        xc = xcn

        k1 = dados[j+1][0] - xc
        c  = dados[j][2]*(k1/h)*k1

        k2 = xc - dados[j][0]
        d  = dados[j+1][2]*(k2/h)*k2

        f  = a*k2 + b + (c*k1/6.0) + (d*k2/6.0) - yc
        fl = a - (c/2.0) + (d/2.0)

        xcn = xc - f/fl

    return xcn


def multqua(dados,xc,yc):

    zc = 0.0

    for i in range(len(dados)):
        a = dados[i][0] - xc
        b = dados[i][1] - yc
        zc += dados[i][2] * (a*a + b*b)**0.5

    return zc

# +-=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---+








# +---------------------------------------------------------------------------------------------------------------------------------+
# |          FUNÇÕES COM CLASSES DESTE MÓDULO E OPERAÇÕES CRUZADAS                                                                  |
# +-=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---+

def PluvSISPSHI(busca = None):
    """ Retorna variável da classe pluviometro() contendo as informações do pluviometro cujo código corresponde ao argumento de entrada
'busca'. Se nenhum argumento for fornecido, retorna lista com todos os pluviometros do SISPSHI."""
    if busca == None:
        aux = []
        for itens in mtz_pluvs_sispshi:
            aux.append(pluviometro(itens))
        return aux

    #Se 'busca' é uma variável do tipo INTEIRO, então procura o código na lista 'mtz_pluvs_sispshi'.
    if type(busca).__name__ == 'int':
        for itens in mtz_pluvs_sispshi:
            if itens[0] == busca:
                return pluviometro(itens)

        #Se não encontrou o pluviometro no loop acima, retorna erro.
        raise ValueError(str('Pluviometro %i não pertence à lista de pluviometros do SISPSHI.' % busca))

    #Mas se 'busca' não for um INTEIRO então informa erro.
    else:
        raise TypeError('Código de busca deve ser um inteiro.')




def GrupoPluvs(numGrupo):
    """ Retorna lista de variáveis da classe pluviometro que pertencem ao grupo 'numGrupo'. """
    lista = []
    
    for itens in mtz_pluvs_sispshi:
        if numGrupo in itens[7]:
            lista.append(pluviometro(itens))
        
    return lista




def FluvSISPSHI(busca = None):
    """ Retorna variável da classe posto_fluvio() contendo as informações do posto fluviométro cujo código corresponde ao argumento
de entrada 'busca'. Se nenhum argumento for fornecido, retorna lista com todos os postos fluviométricos do SISPSHI."""
    if busca == None:
        aux = []
        for itens in mtz_pfluvs_sispshi:
            aux.append(posto_fluvio(itens))
        return aux

    #Se 'busca' é uma variável do tipo INTEIRO, então procura o código na lista 'mtz_pfluvs_sispshi'.
    if type(busca).__name__ == 'int':
        for itens in mtz_pfluvs_sispshi:
            if itens[0] == busca:
                return posto_fluvio(itens)

        #Se não encontrou o posto no loop acima, retorna erro.
        print '\n'
        raise ValueError(str('Posto %i não pertence à lista de postos fluviométricos do SISPSHI.\n' % busca))

    #Mas se 'busca' não for um INTEIRO então informa erro.
    else:
        print '\n'
        raise TypeError('\n  Código de busca deve ser um inteiro.\n')




def BaciaSISPSHI(busca = None):
    """ Retorna variável da classe bacia() contendo as informações da bacia cujo número corresponde ao argumento de entrada 'busca'. Se
nenhum argumento for fornecido, retorna lista com todas as bacias do SISPSHI."""
    if busca == None:
        aux = []
        for itens in mtz_bacias_sispshi:
            aux.append(bacia(itens))
        return aux

    #Se 'busca' é uma variável do tipo INTEIRO, então procura o número na lista 'mtz_bacias_sispshi'.
    if type(busca).__name__ == 'int':
        for itens in mtz_bacias_sispshi:
            if itens[0] == busca:
                return bacia(itens)

        #Se não encontrou a bacia no loop acima, retorna erro.
        raise ValueError(str('Bacia %i não pertence à lista de bacias do SISPSHI.' % busca))

    #Mas se 'busca' não for um INTEIRO então informa erro.
    else:
        raise TypeError('Número de busca deve ser um inteiro.')




def PluvsProximos(Xlocal, Ylocal, distmax=distmax_padrao):
    """ Retorna lista com pares [codigo, distancia(m)] para os pluviometros do SISPSHI que estão a um raio de até 'distmax' metros do ponto
de coordenadas (Xlocal, Ylocal). As coordenadas devem estar em UTM. """
    # Verificando consistência dos valores das coordenadas UTM (em relação à bacia do rio Iguaçu)
    if Xlocal < 100000 or Xlocal > 900000:
        raise ValueError('Longitude em UTM inválida:' + str(Xlocal))
    if Ylocal < 6500000 or Ylocal > 8000000:
        raise ValueError('Latitude em UTM inválida:' + str(Ylocal))

    # Inicializando lista dos pluviometros próximos.
    pluvsproximos = []

    for itens in mtz_pluvs_sispshi:
        pluv = pluviometro(itens)
        dist = ((Xlocal - pluv.Xutm)**2 + (Ylocal - pluv.Yutm)**2)**0.5

        # Adicionando pluviometros a uma distância inferior a 'distmax' metros.
        if dist <= distmax:
            pluvsproximos.append([pluv.codigo,dist])

    # Ordenando lista por ordem crescente da distância.
    pluvsproximos = sorted(pluvsproximos, key = itemgetter(1))
    return pluvsproximos




def MalhaIguacu(num_bac=None):
    """ Dada a bacia 'num_bac' do SISPSHI, gera a lista de variáveis ponto_de_malha() para os pontos internos à bacia. A malha de pontos
consultada está no arquivo especificado na string 'arq_malha' (início deste módulo). Se 'num_bac' não for fornecido, irá retornar toda a
malha de pontos."""
    arq = open(arq_malha, 'r')
    aux = []
    
    if num_bac == None:
        for lin in arq.readlines():
            lin = map(int,lin.split())
            aux.append(ponto_de_malha(lin))

    elif type(num_bac).__name__ == 'int':
        for lin in arq.readlines():
            lin = map(int,lin.split())
            if lin[-1] == num_bac:
                aux.append(ponto_de_malha(lin))

    else:
        raise TypeError('Identificação da bacia inválido. Fornecer um inteiro correspondente ao número da bacia.')

    arq.close()
    return aux

# +-=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---+








# +---------------------------------------------------------------------------------------------------------------------------------+
# |          FUNÇÕES PARA CALCULO DE CHUVA MEDIA NA BACIA                                                                           |
# +-=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---+

def MediaPonderada(dados, Norma):
    """ Estima a média utilizando o fator '1.0/dist^Norma' para ponderar o peso de cada dado.
    'dados' = lista dos pares (chuva, distância). "chuva" é o valor do dado e "distância" é a distância entre o pluviômetro e local da estimativa (centro da bacia ou ponto de 
              malha);
    'Norma' = valor da potência à qual a distância será elevada no momento da ponderação.
    
    ATENÇÃO: Esta função NÃO verifica se os dados são consistentes. Utiliza toda a lista 'dados' sem distinção."""
    
    num, dem = 0.0, 0.0
    for i in range(len(dados)):
        num += dados[i][0] / dados[i][1]**Norma
        dem += 1.0 / dados[i][1]**Norma

    return num/dem




def MediaMalha(dic_dados, malha, Norma):
    """ Calcula o valor médio da chuva interpolada para os pontos de malha. Esta interpolação é feita pela função MediaPonderada.
    'dic_dados' = dicionário de dados de chuva indexado pelos códigos dos pluviometros;
    'malha'     = lista de variáveis ponto_de_malha(), sendo que cada uma deve conter o atributo 'self.pluvsprox';
    'Norma'     = valor da potência à qual a distância será elevada no momento da ponderação."""

    media, nptos = 0.0, 0
    for ponto in malha:

        dados = []
        for codigo, dist in ponto.pluvsprox:
            try:
                dados.append([dic_dados[codigo],dist])
            except KeyError:
                pass

        if len(dados) > 0:
            media += MediaPonderada(dados, Norma)
            nptos += 1

    return media/nptos




def Thiessen(dic_dados, malha):
    """ Calcula a chuva média ponderando os dados conforme a fração dos pontos da malha representada por cada pluviometro.
    'dic_dados' = dicionário de dados de chuva indexado pelos códigos dos pluviometros;
    'malha'     = lista de variáveis ponto_de_malha(), sendo que cada uma deve conter o atributo 'self.pluvsprox'.
    
    ATENÇÃO: Esta função presume que o atributo 'self.pluvsprox' dos pontos de malha já estão ordenados em ordem crescente da distância."""
    media, nptos = 0.0, 0
    for ponto in malha:

        for codigo, dist in ponto.pluvsprox:
            try:
                media += dic_dados[codigo]
                nptos += 1
                break
            except KeyError:
                pass

    return media/nptos

# +-=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---+








# +---------------------------------------------------------------------------------------------------------------------------------+
# |          OPERAÇÃO COM METEOGRAMAS E SÉRIES DE CHUVA PREVISTA                                                                    |
# +-=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---+

def AMMR(tref,nh_atras=96):
    """ AMMR = Arquivo de Meteograma Mais Recente. Esta função busca o(s) arquivo(s) de meteograma gerado(s) mais recentemente.
    'tref'     = variável datetime (em horário BRT) a partir da qual inicia-se a busca retrocronologica dos últimos arquivos de meteogramas
                 disponibilizados;
    'nh_atras' = quantidade de horas anterior a 'tref', a partir da qual deseja-se listar os arquivos de meteogramas. É montada uma
                 lista com o nome dos arquivos em ordem cronológica, do mais antigo para o mais novo.
    OBS: Os meteogramas trabalham com data em UTC, assim como a data que compoem seus nomes. """
    taux = tref + timedelta(hours = 3)
    
    # Buscando lista de meteogramas nas 'nh_atras' horas anteriores a 'tref'
    arquivos = []
    for nh in range(nh_atras,-1,-1):    # Indo de 'taux - nh_atras' até 'taux', hora a hora

        dt = taux - timedelta(hours = nh)
        nome_meteo = str('/simepar/hidro/WRF/sispshi/sispshi_%s.txt' % dt.strftime('%d_%m_%Y_%H'))

        if os_path.exists(nome_meteo):    # Incluindo nomes de arquivos existentes
            arquivos.append(nome_meteo)

    #check = open('/simepar/hidro/COPEL/SISPSHI2/Testes/MeteoDaRodada/meteograma.txt', 'a')
    #check.write('%s | %s\n' % (datetime.now(), arquivos[-1]))
    #check.close()
    return arquivos




def PrevPluvios1_WRF(lista,dt0,dtN):
    """ Função para obter séries de chuva prevista pelo WRF em pluviometros no período desejado.
    IMPORTANTE: Esta função utiliza a função AMMR para obter a lista de meteogramas a serem lidos.
    
    Variáveis de entrada:
 > lista = lista de códigos do pluviômetros onde se deseja obter as previsões de chuva;
 > dt0   = data de referência. O período de previsão começa em dt0 + 1 hora;
 > dtN   = data final do período de previsão.
 
     Variável de saída:
 > Dicionário 'mtz' com indexação mtz[codigo][datahora][valor], sendo 'codigo' o código SIMEPAR do posto pluviométrico (onde deseja-se
 a previsão do meteograma), 'datahora' a data e hora do momento para a qual aquela chuva está prevista, 'valor' é o montante horário de
 chuva previsto. """

    # Lista em ordem cronológica dos meteogramas quatro dias anteriores a dt0        
    arquivos = AMMR(dt0)
    
    # Inicializando dicionário de dados indexado pelo código dos pluviometros
    mtz = dict( [(pluv,{}) for pluv in lista] )
    
    # Ciclo dos meteogramas
    for nome_meteo in arquivos:
        fmet = open(nome_meteo, 'r')    # Arquivo do meteograma

        # Lendo e armazenando previsões de chuva horária entre 'dt0 + 1h' e 'dtN' para os pluviômetros em 'lista'
        for linha in fmet:
            linha = linha.split()
            
            # Contigência para quando o arquivo do WRF não está completo
            try:
                cod, dtaux, valor = int(linha[0]), linha[3], float(linha[4])
            except IndexError:
                continue

            dt = datetime(int(dtaux[0:4]), int(dtaux[5:7]), int(dtaux[8:10]), int(dtaux[11:13]), 0, 0)
            dt -= timedelta(hours = 3)    # Horário local
            
            # Dado do período de previsão
            if dt0 < dt <= dtN:
                """ Usando decisor 'try, except' para processar apenas dados de pluviometros da 'lista', pois 'mtz[cod]' já foi
                definido na inicialização do dicionário de dados. Como mtz[cod] = {}, se dt não fizer parte do dicionário ele
                será incluido, mas se já for parte (inserido na leitura de um meteograma anterior) então o dado será sobreposto
                pelo de um meteograma mais recente (previsão com menos tempo de antecedência), visto que a sucessão dos meteogramas
                é cronológica. """
                try:
                    mtz[cod][dt] = valor
                except KeyError:
                    pass

        # Fechando arquivo
        fmet.close()

    return mtz




def PrevCMB(sbac,tipocmb,dt0,dtN,metodo=1):
    """ Função para gerar série de previsão de chuva média na bacia para o período desejado
    'sbac'    = variável bacia() para sub-bacia do SISPSHI na qual deseja-se obter a previsão de chuva. Também aceita o número da bacia;
    'tipocmb' = método de cálculo da CMB. Opções: 'MEDIA', 'PC_D2', 'PC_D4', 'PM_D2', 'THSEN';
    'dt0'     = data de referência. O período de previsão começa em dt0 + 1 hora;
    'dtN'     = data final do período de previsão;
    'metodo'  = inteiro que representa qual será a fonte dos dados de previsão nos pluviômetro, conforme:
                1 = PrevPluvios1_WRF, para meteogramas txt em /simepar/hidro/WRF/sispshi/;
                2 = PrevPluvios2_WRF, para meteogramas netcdf em X. """

    # Listando pluviometros próximos da sub-bacia
    if type(sbac).__name__ == 'bacia':
        if not hasattr(sbac, 'pluvsprox'):
            sbac.informacoes_espaciais()
    elif type(sbac).__name__ == 'int':
        sbac = BaciaSISPSHI(sbac)
        sbac.informacoes_espaciais()
    else:
        erro = str('\n     Variável "sbac" deve ser do tipo "bacia", mas é um "%s".\n' % type(sbac).__name__)
        raise ValueError(erro)
    pluvios = [item[0] for item in sbac.pluvsprox]

    # Origem dos dados de chuva prevista
    if metodo == 1:
        # Obtendo série prevista de chuva nos pluviometros
        chuva = PrevPluvios1_WRF(pluvios,dt0,dtN)
    
    elif metodo == 2:
        # Obtendo série prevista de chuva em arquivos na pasta ~/SISPSHI2/Previsao_CMB
        nome_arq = base + str('/Previsao_CMB/prevcmb_%2.2i.txt' % sbac.numero)
        chuva = serie_horaria([[nome_arq, 4]])

    else:
        raise ValueError('\n     Este método de extração de dados dos meteogramas não existe.\n')


    # Computando chuva média prevista para a bacia
    cmb, dt, nfal = {}, dt0+timedelta(hours = 1), 0
    
    # Cálculo da CMB por média aritmética simples ou ponderações pela distância ao ponto central da bacia
    if tipocmb in ['MEDIA', 'PC_D2', 'PC_D4']:
        
        # Norma da ponderação por distância: MEDIA = 0; PC_D2 = 2; PC_D4 = 4.
        norma = 0
        if tipocmb[0:2] == 'PC': norma = int(tipocmb[-1:])

        # Ciclo horário
        while dt <= dtN:

            # Organizando dados de chuva prevista em lista [valor, distancia]
            dados = []
            for codigo, distancia in sbac.pluvsprox:
                try:
                    dados.append([chuva[codigo][dt], distancia])
                except KeyError:
                    pass

            # Calculando média ou atribuindo valor nulo se não há dados
            if len(dados) == 0:
                nfal += 1
                cmb[dt] = 0.0
            else:
                cmb[dt] = MediaPonderada(dados, norma)
            dt += timedelta(hours = 1)

    # Cálculo da CMB por ponderação pela distância entre os pluviômetros e o ponto central da bacia
    elif tipocmb == 'PM_D2':
        while dt <= dtN:

            # Orgarnizando dados de chuva em dicionário {codigo: valor}
            dados = {}
            for codigo, distancia in sbac.pluvsprox:
                try:
                    dados[codigo] = chuva[codigo][dt]
                except KeyError:
                    pass

            # Calculando CMB ou atribuindo valor nulo se não há dados
            if len(dados) == 0:
                nfal += 1
                cmb[dt] = 0.0
            else:
                cmb[dt] = MediaMalha(dados, sbac.malha, 2)
            dt += timedelta(hours = 1)

    # Cálculo da CMB pelo método de Thiessen
    elif tipocmb == 'THSEN':
        while dt <= dtN:

            # Orgarnizando dados de chuva em dicionário {codigo: valor}
            dados = {}
            for codigo, distancia in sbac.pluvsprox:
                try:
                    dados[codigo] = chuva[codigo][dt]
                except KeyError:
                    pass

            # Calculando CMB ou atribuindo valor nulo se não há dados
            if len(dados) == 0:
                nfal += 1
                cmb[dt] = 0.0
            else:
                cmb[dt] = Thiessen(dados, sbac.malha)
            dt += timedelta(hours = 1)

    # Chuva gerada em etapa separada, armazenada em arquivo no diretório ~/SISPSHI2/Previsao_CMB
    elif tipocmb == 'ENSWRFMED':
        
        # Copiando dados do arquivo para o período de previsão
        while dt <= dtN:
            
            try:
                cmb[dt] = chuva[dt]
            except KeyError:
                cmb[dt] = 0.0
                nfal += 1

            dt += timedelta(hours = 1)

    # Método de cálculo da CMB desconhecido
    else:
        erro = str('\n Método para cálculo da CMB, %s, não existe!' % tipocmb)
        erro += '\n As opções válidas são "MEDIA", "PC_D2", "PC_D4", "PM_D2", "THSEN".\n'
        raise ValueError(erro)

    # Alertando ausência dados de chuva prevista
    if nfal == len(cmb):
        print str('\n     ATENÇÃO! Não há dados para calcular CMB prevista de B%2.2i.' % sbac.numero)

    return cmb

# +-=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---+
