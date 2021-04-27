# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from os.path import exists
from iguacu import BaciaSISPSHI, FluvSISPSHI, PrevCMB, base
from admin import serie_horaria, dataexec
from prm_modhid import ParamRRR, ParamSACSIMPLES



# +---------------------------------------------------------------------------------------------------------------------------------+
# |          INFORMAÇÕES ESTÁTICAS                                                                                                  |
# +-=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---+
# Dicionário Tipo CMB x coluna no arquivo de CMB observada
TipoCMB = {'MEDIA':4, 'PC_D2':5, 'PC_D4':6, 'PM_D2':7, 'THSEN':8}

# Dicionário com configurações pré-programadas para rodadas automáticas de simulação/previsão
bdsimuls = {
    # Simulações B01
    100:{'BACIA':1, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2'},
    101:{'BACIA':1, 'MODELO':'SACSIMPLES', 'PARAM':'4', 'CMBOBS':'MEDIA'},
    102:{'BACIA':1, 'MODELO':'SACFRACAO', 'PARAM':'1,2,3', 'CMBOBS':'MEDIA'},
    # Previsões B01
    110:{'BACIA':1, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2', 'CMBPREV':'0', 'QMONTPREV':'0'},
    111:{'BACIA':1, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2', 'CMBPREV':'PC_D2', 'QMONTPREV':'0'},
    112:{'BACIA':1, 'MODELO':'SACFRACAO', 'PARAM':'1,2,3', 'CMBOBS':'PC_D2', 'CMBPREV':'0', 'QMONTPREV':'0'},
    113:{'BACIA':1, 'MODELO':'SACFRACAO', 'PARAM':'5,6,7', 'CMBOBS':'MEDIA', 'CMBPREV':'MEDIA', 'QMONTPREV':'0'},
    114:{'BACIA':1, 'MODELO':'RRR', 'PARAM':'2013,2', 'CMBOBS':'MEDIA', 'CMBPREV':'0', 'QMONTPREV':'0'},
    115:{'BACIA':1, 'MODELO':'RRR', 'PARAM':'2013,2', 'CMBOBS':'MEDIA', 'CMBPREV':'MEDIA', 'QMONTPREV':'0'},
    116:{'BACIA':1, 'MODELO':'SACFRACAO', 'PARAM':'5,6,7', 'CMBOBS':'MEDIA', 'CMBPREV':'ENSWRFMED', 'QMONTPREV':'0'},
    117:{'BACIA':1, 'MODELO':'RRR', 'PARAM':'2013,2', 'CMBOBS':'MEDIA', 'CMBPREV':'ENSWRFMED', 'QMONTPREV':'0'},
    131:{'BACIA':1, 'MODELO':'FK', 'REFER':111},

    # Simulações B02
    200:{'BACIA':2, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2'},
    201:{'BACIA':2, 'MODELO':'SACSIMPLES', 'PARAM':'4', 'CMBOBS':'PM_D2'},
    202:{'BACIA':2, 'MODELO':'SACFRACAO', 'PARAM':'1,2,3', 'CMBOBS':'MEDIA'},
    # Previsões B02
    210:{'BACIA':2, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2', 'CMBPREV':'0', 'QMONTPREV':'0'},
    211:{'BACIA':2, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2', 'CMBPREV':'PC_D2', 'QMONTPREV':'0'},
    212:{'BACIA':2, 'MODELO':'SACFRACAO', 'PARAM':'1,2,3', 'CMBOBS':'PC_D2', 'CMBPREV':'0', 'QMONTPREV':'0'},
    213:{'BACIA':2, 'MODELO':'SACFRACAO', 'PARAM':'5,6,7', 'CMBOBS':'MEDIA', 'CMBPREV':'MEDIA', 'QMONTPREV':'0'},
    214:{'BACIA':2, 'MODELO':'RRR', 'PARAM':'2013,3', 'CMBOBS':'PC_D2', 'CMBPREV':'0', 'QMONTPREV':'0'},
    215:{'BACIA':2, 'MODELO':'RRR', 'PARAM':'2013,1', 'CMBOBS':'PM_D2', 'CMBPREV':'PM_D2', 'QMONTPREV':'0'},
    216:{'BACIA':2, 'MODELO':'SACFRACAO', 'PARAM':'5,6,7', 'CMBOBS':'MEDIA', 'CMBPREV':'ENSWRFMED', 'QMONTPREV':'0'},
    217:{'BACIA':2, 'MODELO':'RRR', 'PARAM':'2013,1', 'CMBOBS':'PM_D2', 'CMBPREV':'ENSWRFMED', 'QMONTPREV':'0'},
    231:{'BACIA':2, 'MODELO':'FK', 'REFER':211},

    # Simulações B03
    300:{'BACIA':3, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2'},
    301:{'BACIA':3, 'MODELO':'SACSIMPLES', 'PARAM':'4', 'CMBOBS':'MEDIA'},
    302:{'BACIA':3, 'MODELO':'SACFRACAO', 'PARAM':'1,2,3', 'CMBOBS':'MEDIA'},
    # Previsões B03
    310:{'BACIA':3, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2', 'CMBPREV':'0', 'QMONTPREV':'0'},
    311:{'BACIA':3, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2', 'CMBPREV':'PC_D2', 'QMONTPREV':'0'},
    312:{'BACIA':3, 'MODELO':'SACFRACAO', 'PARAM':'5,6,7', 'CMBOBS':'PC_D2', 'CMBPREV':'0', 'QMONTPREV':'0'},
    313:{'BACIA':3, 'MODELO':'SACFRACAO', 'PARAM':'5,6,7', 'CMBOBS':'PC_D2', 'CMBPREV':'PC_D2', 'QMONTPREV':'0'},
    314:{'BACIA':3, 'MODELO':'RRR', 'PARAM':'2013,2', 'CMBOBS':'MEDIA', 'CMBPREV':'0', 'QMONTPREV':'0'},
    315:{'BACIA':3, 'MODELO':'RRR', 'PARAM':'2013,1', 'CMBOBS':'THSEN', 'CMBPREV':'THSEN', 'QMONTPREV':'0'},
    316:{'BACIA':3, 'MODELO':'SACFRACAO', 'PARAM':'5,6,7', 'CMBOBS':'PC_D2', 'CMBPREV':'ENSWRFMED', 'QMONTPREV':'0'},
    317:{'BACIA':3, 'MODELO':'RRR', 'PARAM':'2013,1', 'CMBOBS':'THSEN', 'CMBPREV':'ENSWRFMED', 'QMONTPREV':'0'},
    331:{'BACIA':3, 'MODELO':'FK', 'REFER':311},

    # Simulações B04
    400:{'BACIA':4, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2'},
    401:{'BACIA':4, 'MODELO':'SACSIMPLES', 'PARAM':'4', 'CMBOBS':'PC_D4'},
    402:{'BACIA':4, 'MODELO':'SACFRACAO', 'PARAM':'1,2,3', 'CMBOBS':'PM_D2'},
    # Previsões B04
    410:{'BACIA':4, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2', 'CMBPREV':'0', 'QMONTPREV':'0'},
    411:{'BACIA':4, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2', 'CMBPREV':'PC_D2', 'QMONTPREV':'0'},
    412:{'BACIA':4, 'MODELO':'SACFRACAO', 'PARAM':'5,6,7', 'CMBOBS':'PC_D2', 'CMBPREV':'0', 'QMONTPREV':'0'},
    413:{'BACIA':4, 'MODELO':'SACSIMPLES', 'PARAM':'5,6,7', 'CMBOBS':'PM_D2', 'CMBPREV':'PM_D2', 'QMONTPREV':'0'},
    414:{'BACIA':4, 'MODELO':'RRR', 'PARAM':'2013,2', 'CMBOBS':'MEDIA', 'CMBPREV':'0', 'QMONTPREV':'0'},
    415:{'BACIA':4, 'MODELO':'RRR', 'PARAM':'2013,3', 'CMBOBS':'PC_D4', 'CMBPREV':'PC_D4', 'QMONTPREV':'0'},
    416:{'BACIA':4, 'MODELO':'SACSIMPLES', 'PARAM':'5,6,7', 'CMBOBS':'PM_D2', 'CMBPREV':'ENSWRFMED', 'QMONTPREV':'0'},
    417:{'BACIA':4, 'MODELO':'RRR', 'PARAM':'2013,3', 'CMBOBS':'PC_D4', 'CMBPREV':'ENSWRFMED', 'QMONTPREV':'0'},
    431:{'BACIA':5, 'MODELO':'FK', 'REFER':411},

    # Simulações B05
    500:{'BACIA':5, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2'},
    501:{'BACIA':5, 'MODELO':'SACSIMPLES', 'PARAM':'4', 'CMBOBS':'MEDIA'},
    502:{'BACIA':5, 'MODELO':'SACFRACAO', 'PARAM':'1,2,3', 'CMBOBS':'MEDIA'},
    # Previsões B05
    510:{'BACIA':5, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2', 'CMBPREV':'0', 'QMONTPREV':'0'},
    511:{'BACIA':5, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2', 'CMBPREV':'PC_D2', 'QMONTPREV':'0'},
    512:{'BACIA':5, 'MODELO':'SACFRACAO', 'PARAM':'1,2,3', 'CMBOBS':'MEDIA', 'CMBPREV':'0', 'QMONTPREV':'0'},
    513:{'BACIA':5, 'MODELO':'SACFRACAO', 'PARAM':'5,6,7', 'CMBOBS':'PM_D2', 'CMBPREV':'PM_D2', 'QMONTPREV':'0'},
    514:{'BACIA':5, 'MODELO':'RRR', 'PARAM':'2013,2', 'CMBOBS':'THSEN', 'CMBPREV':'0', 'QMONTPREV':'0'},
    515:{'BACIA':5, 'MODELO':'RRR', 'PARAM':'2013,2', 'CMBOBS':'PC_D2', 'CMBPREV':'PC_D2', 'QMONTPREV':'0'},
    516:{'BACIA':5, 'MODELO':'SACFRACAO', 'PARAM':'5,6,7', 'CMBOBS':'PM_D2', 'CMBPREV':'ENSWRFMED', 'QMONTPREV':'0'},
    517:{'BACIA':5, 'MODELO':'RRR', 'PARAM':'2013,2', 'CMBOBS':'PC_D2', 'CMBPREV':'ENSWRFMED', 'QMONTPREV':'0'},
    531:{'BACIA':5, 'MODELO':'FK', 'REFER':511},

    # Simulações B06
    600:{'BACIA':6, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2'},
    601:{'BACIA':6, 'MODELO':'SACSIMPLES', 'PARAM':'4', 'CMBOBS':'MEDIA'},
    602:{'BACIA':6, 'MODELO':'SACFRACAO', 'PARAM':'1,2,3', 'CMBOBS':'MEDIA'},
    # Previsões B06
    610:{'BACIA':6, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2', 'CMBPREV':'0', 'QMONTPREV':'210'},
    611:{'BACIA':6, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2', 'CMBPREV':'PC_D2', 'QMONTPREV':'211'},
    612:{'BACIA':6, 'MODELO':'SACFRACAO', 'PARAM':'1,2,3', 'CMBOBS':'MEDIA', 'CMBPREV':'0', 'QMONTPREV':'212'},
    613:{'BACIA':6, 'MODELO':'SACFRACAO', 'PARAM':'5,6,7', 'CMBOBS':'PM_D2', 'CMBPREV':'PM_D2', 'QMONTPREV':'213'},
    614:{'BACIA':6, 'MODELO':'RRR', 'PARAM':'2013,2', 'CMBOBS':'PC_D4', 'CMBPREV':'0', 'QMONTPREV':'214'},
    615:{'BACIA':6, 'MODELO':'RRR', 'PARAM':'2013,2', 'CMBOBS':'PC_D4', 'CMBPREV':'PC_D4', 'QMONTPREV':'215'},
    616:{'BACIA':6, 'MODELO':'SACFRACAO', 'PARAM':'5,6,7', 'CMBOBS':'PM_D2', 'CMBPREV':'ENSWRFMED', 'QMONTPREV':'216'},
    617:{'BACIA':6, 'MODELO':'RRR', 'PARAM':'2013,2', 'CMBOBS':'PC_D4', 'CMBPREV':'ENSWRFMED', 'QMONTPREV':'217'},
    631:{'BACIA':6, 'MODELO':'FK', 'REFER':611},

    # Simulações B07
    700:{'BACIA':7, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2'},
    701:{'BACIA':7, 'MODELO':'SACSIMPLES', 'PARAM':'4', 'CMBOBS':'PM_D2'},
    702:{'BACIA':7, 'MODELO':'SACFRACAO', 'PARAM':'1,2,3', 'CMBOBS':'PM_D2'},
    # Previsões B07
    710:{'BACIA':7, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2', 'CMBPREV':'0', 'QMONTPREV':'110,310'},
    711:{'BACIA':7, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2', 'CMBPREV':'PC_D2', 'QMONTPREV':'111,311'},
    712:{'BACIA':7, 'MODELO':'SACSIMPLES', 'PARAM':'1,2,3', 'CMBOBS':'MEDIA', 'CMBPREV':'0', 'QMONTPREV':'112,312'},
    713:{'BACIA':7, 'MODELO':'SACFRACAO', 'PARAM':'1,2,3', 'CMBOBS':'PM_D2', 'CMBPREV':'PM_D2', 'QMONTPREV':'113,313'},
    714:{'BACIA':7, 'MODELO':'RRR', 'PARAM':'2013,2', 'CMBOBS': 'THSEN', 'CMBPREV':'0', 'QMONTPREV':'114,314'},
    715:{'BACIA':7, 'MODELO':'RRR', 'PARAM':'2013,2', 'CMBOBS': 'PC_D2', 'CMBPREV':'PC_D2', 'QMONTPREV':'115,315'},
    716:{'BACIA':7, 'MODELO':'SACFRACAO', 'PARAM':'1,2,3', 'CMBOBS':'PM_D2', 'CMBPREV':'ENSWRFMED', 'QMONTPREV':'116,316'},
    717:{'BACIA':7, 'MODELO':'RRR', 'PARAM':'2013,2', 'CMBOBS': 'PC_D2', 'CMBPREV':'ENSWRFMED', 'QMONTPREV':'117,317'},
    731:{'BACIA':7, 'MODELO':'FK', 'REFER':711},

    # Simulações B08
    800:{'BACIA':8, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2'},
    801:{'BACIA':8, 'MODELO':'SACSIMPLES', 'PARAM':'4', 'CMBOBS':'PC_D4'},
    802:{'BACIA':8, 'MODELO':'SACFRACAO', 'PARAM':'1,2,3', 'CMBOBS':'PC_D4'},
    # Previsões B08
    810:{'BACIA':8, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2', 'CMBPREV':'0', 'QMONTPREV':'410,610,710'},
    811:{'BACIA':8, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2', 'CMBPREV':'PC_D2', 'QMONTPREV':'411,611,711'},
    812:{'BACIA':8, 'MODELO':'SACSIMPLES', 'PARAM':'1,2,3', 'CMBOBS':'THSEN', 'CMBPREV':'0', 'QMONTPREV':'412,612,712'},
    813:{'BACIA':8, 'MODELO':'SACSIMPLES', 'PARAM':'5,6,7', 'CMBOBS':'PM_D2', 'CMBPREV':'PM_D2', 'QMONTPREV':'413,613,713'},
    814:{'BACIA':8, 'MODELO':'RRR', 'PARAM':'2013,1', 'CMBOBS': 'MEDIA', 'CMBPREV':'0', 'QMONTPREV':'414,614,714'},
    815:{'BACIA':8, 'MODELO':'RRR', 'PARAM':'2013,2', 'CMBOBS': 'MEDIA', 'CMBPREV':'MEDIA', 'QMONTPREV':'415,615,715'},
    816:{'BACIA':8, 'MODELO':'SACSIMPLES', 'PARAM':'5,6,7', 'CMBOBS':'PM_D2', 'CMBPREV':'ENSWRFMED', 'QMONTPREV':'416,616,716'},
    817:{'BACIA':8, 'MODELO':'RRR', 'PARAM':'2013,2', 'CMBOBS': 'MEDIA', 'CMBPREV':'ENSWRFMED', 'QMONTPREV':'417,617,717'},
    831:{'BACIA':3, 'MODELO':'FK', 'REFER':811},

    # Simulações B09
    900:{'BACIA':9, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2'},
    901:{'BACIA':9, 'MODELO':'SACSIMPLES', 'PARAM':'4', 'CMBOBS':'PM_D2'},
    902:{'BACIA':9, 'MODELO':'SACFRACAO', 'PARAM':'1,2,3', 'CMBOBS':'PC_D4'},
    # Previsões B09
    910:{'BACIA':9, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2', 'CMBPREV':'0', 'QMONTPREV':'510,810'},
    911:{'BACIA':9, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2', 'CMBPREV':'PC_D2', 'QMONTPREV':'511,811'},
    912:{'BACIA':9, 'MODELO':'SACFRACAO', 'PARAM':'5,6,7', 'CMBOBS':'THSEN', 'CMBPREV':'0', 'QMONTPREV':'512,812'},
    913:{'BACIA':9, 'MODELO':'SACSIMPLES', 'PARAM':'5,6,7', 'CMBOBS':'PC_D4', 'CMBPREV':'PC_D4', 'QMONTPREV':'513,813'},
    914:{'BACIA':9, 'MODELO':'RRR', 'PARAM':'2013,2', 'CMBOBS': 'THSEN', 'CMBPREV':'0', 'QMONTPREV':'514,814'},
    915:{'BACIA':9, 'MODELO':'RRR', 'PARAM':'2013,2', 'CMBOBS': 'MEDIA', 'CMBPREV':'MEDIA', 'QMONTPREV':'515,815'},
    916:{'BACIA':9, 'MODELO':'SACSIMPLES', 'PARAM':'5,6,7', 'CMBOBS':'PC_D4', 'CMBPREV':'ENSWRFMED', 'QMONTPREV':'516,816'},
    917:{'BACIA':9, 'MODELO':'RRR', 'PARAM':'2013,2', 'CMBOBS': 'MEDIA', 'CMBPREV':'ENSWRFMED', 'QMONTPREV':'517,817'},
    931:{'BACIA':9, 'MODELO':'FK', 'REFER':911},

    # Simulações B10
    1000:{'BACIA':10, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2'},
    1001:{'BACIA':10, 'MODELO':'SACSIMPLES', 'PARAM':'4', 'CMBOBS':'PC_D2'},
    1002:{'BACIA':10, 'MODELO':'SACFRACAO', 'PARAM':'1,2,3', 'CMBOBS':'PC_D2'},
    # Previsões B10
    1010:{'BACIA':10, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2', 'CMBPREV':'0', 'QMONTPREV':'0'},
    1011:{'BACIA':10, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2', 'CMBPREV':'PC_D2', 'QMONTPREV':'0'},
    1012:{'BACIA':10, 'MODELO':'SACSIMPLES', 'PARAM':'1,2,3', 'CMBOBS':'MEDIA', 'CMBPREV':'0', 'QMONTPREV':'0'},
    1013:{'BACIA':10, 'MODELO':'SACSIMPLES', 'PARAM':'5,6,7', 'CMBOBS':'PC_D2', 'CMBPREV':'PC_D2', 'QMONTPREV':'0'},
    1014:{'BACIA':10, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2', 'CMBPREV':'ENSWRFMED', 'QMONTPREV':'0'},
    1015:{'BACIA':10, 'MODELO':'SACSIMPLES', 'PARAM':'5,6,7', 'CMBOBS':'PC_D2', 'CMBPREV':'ENSWRFMED', 'QMONTPREV':'0'},

    # Simulações B11
    1100:{'BACIA':11, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2'},
    1101:{'BACIA':11, 'MODELO':'SACSIMPLES', 'PARAM':'4', 'CMBOBS':'PC_D2'},
    1102:{'BACIA':11, 'MODELO':'SACFRACAO', 'PARAM':'1,2,3', 'CMBOBS':'PC_D2'},
    # Previsões B11
    1110:{'BACIA':11, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2', 'CMBPREV':'0', 'QMONTPREV':'0'},
    1111:{'BACIA':11, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2', 'CMBPREV':'PC_D2', 'QMONTPREV':'0'},
    1112:{'BACIA':11, 'MODELO':'SACSIMPLES', 'PARAM':'1,2,3', 'CMBOBS':'MEDIA', 'CMBPREV':'0', 'QMONTPREV':'0'},
    1113:{'BACIA':11, 'MODELO':'SACSIMPLES', 'PARAM':'5,6,7', 'CMBOBS':'PC_D2', 'CMBPREV':'PC_D2', 'QMONTPREV':'0'},
    1114:{'BACIA':11, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2', 'CMBPREV':'ENSWRFMED', 'QMONTPREV':'0'},
    1115:{'BACIA':11, 'MODELO':'SACSIMPLES', 'PARAM':'5,6,7', 'CMBOBS':'PC_D2', 'CMBPREV':'ENSWRFMED', 'QMONTPREV':'0'},

    # Simulações B12
    1200:{'BACIA':12, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2'},
    1201:{'BACIA':12, 'MODELO':'RRR', 'PARAM':'2016', 'CMBOBS':'PC_D2'},
    # Previsões B12
    1210:{'BACIA':12, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2', 'CMBPREV':'0', 'QMONTPREV':'914,1010,1110'},
    1211:{'BACIA':12, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2', 'CMBPREV':'PC_D2', 'QMONTPREV':'915,1011,1111'},
    1212:{'BACIA':12, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2', 'CMBPREV':'0', 'QMONTPREV':'912,1012,1112'},
    1213:{'BACIA':12, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2', 'CMBPREV':'PC_D2', 'QMONTPREV':'913,1013,1113'},
    1214:{'BACIA':12, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2', 'CMBPREV':'ENSWRFMED', 'QMONTPREV':'917,1014,1114'},
    1215:{'BACIA':12, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2', 'CMBPREV':'ENSWRFMED', 'QMONTPREV':'916,1015,1115'},
    1218:{'BACIA':12, 'MODELO':'RRR', 'PARAM':'2016', 'CMBOBS':'PC_D2', 'CMBPREV':'ENSWRFMED', 'QMONTPREV':'917,1014,1114'},
    1219:{'BACIA':12, 'MODELO':'RRR', 'PARAM':'2016', 'CMBOBS':'PC_D2', 'CMBPREV':'ENSWRFMED', 'QMONTPREV':'916,1015,1115'},

    # Simulações B13
    1300:{'BACIA':13, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2'},
    1301:{'BACIA':13, 'MODELO':'SACSIMPLES', 'PARAM':'4', 'CMBOBS':'MEDIA'},
    1302:{'BACIA':13, 'MODELO':'SACFRACAO', 'PARAM':'1,2,3', 'CMBOBS':'MEDIA'},
    # Previsões B13
    1310:{'BACIA':13, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2', 'CMBPREV':'0', 'QMONTPREV':'0'},
    1311:{'BACIA':13, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2', 'CMBPREV':'PC_D2', 'QMONTPREV':'0'},
    1312:{'BACIA':13, 'MODELO':'SACSIMPLES', 'PARAM':'1,2,3', 'CMBOBS':'THSEN', 'CMBPREV':'0', 'QMONTPREV':'0'},
    1313:{'BACIA':13, 'MODELO':'SACSIMPLES', 'PARAM':'5,6,7', 'CMBOBS':'MEDIA', 'CMBPREV':'MEDIA', 'QMONTPREV':'0'},
    1314:{'BACIA':13, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2', 'CMBPREV':'ENSWRFMED', 'QMONTPREV':'0'},
    1315:{'BACIA':13, 'MODELO':'SACSIMPLES', 'PARAM':'5,6,7', 'CMBOBS':'MEDIA', 'CMBPREV':'ENSWRFMED', 'QMONTPREV':'0'},

    # Simulações B14
    1400:{'BACIA':14, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2'},
    1401:{'BACIA':14, 'MODELO':'SACSIMPLES', 'PARAM':'4', 'CMBOBS':'PC_D4'},
    1402:{'BACIA':14, 'MODELO':'SACFRACAO', 'PARAM':'1,2,3', 'CMBOBS':'PC_D4'},
    # Previsões B14
    1410:{'BACIA':14, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2', 'CMBPREV':'0', 'QMONTPREV':'0'},
    1411:{'BACIA':14, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2', 'CMBPREV':'PC_D2', 'QMONTPREV':'0'},
    1412:{'BACIA':14, 'MODELO':'SACSIMPLES', 'PARAM':'1,2,3', 'CMBOBS':'PM_D2', 'CMBPREV':'0', 'QMONTPREV':'0'},
    1413:{'BACIA':14, 'MODELO':'SACSIMPLES', 'PARAM':'5,6,7', 'CMBOBS':'PC_D4', 'CMBPREV':'PC_D4', 'QMONTPREV':'0'},
    1414:{'BACIA':14, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2', 'CMBPREV':'ENSWRFMED', 'QMONTPREV':'0'},
    1415:{'BACIA':14, 'MODELO':'SACSIMPLES', 'PARAM':'5,6,7', 'CMBOBS':'PC_D4', 'CMBPREV':'ENSWRFMED', 'QMONTPREV':'0'},

    # Simulações B15
    1500:{'BACIA':15, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2'},
    1501:{'BACIA':15, 'MODELO':'SACSIMPLES', 'PARAM':'4', 'CMBOBS':'THSEN'},
    1502:{'BACIA':15, 'MODELO':'SACFRACAO', 'PARAM':'1,2,3', 'CMBOBS':'THSEN'},
    # Previsões B15
    1510:{'BACIA':15, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2', 'CMBPREV':'0', 'QMONTPREV':'0'},
    1511:{'BACIA':15, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2', 'CMBPREV':'PC_D2', 'QMONTPREV':'0'},
    1512:{'BACIA':15, 'MODELO':'SACSIMPLES', 'PARAM':'1,2,3', 'CMBOBS':'PC_D4', 'CMBPREV':'0', 'QMONTPREV':'0'},
    1513:{'BACIA':15, 'MODELO':'SACFRACAO', 'PARAM':'5,6,7', 'CMBOBS':'THSEN', 'CMBPREV':'THSEN', 'QMONTPREV':'0'},
    1514:{'BACIA':15, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2', 'CMBPREV':'ENSWRFMED', 'QMONTPREV':'0'},
    1515:{'BACIA':15, 'MODELO':'SACFRACAO', 'PARAM':'5,6,7', 'CMBOBS':'THSEN', 'CMBPREV':'ENSWRFMED', 'QMONTPREV':'0'},

    # Simulações B16
    1600:{'BACIA':16, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2'},
    # Previsões B16
    1610:{'BACIA':16, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2', 'CMBPREV':'0', 'QMONTPREV':'1310'},
    1611:{'BACIA':16, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2', 'CMBPREV':'PC_D2', 'QMONTPREV':'1311'},
    1612:{'BACIA':16, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2', 'CMBPREV':'0', 'QMONTPREV':'1312'},
    1613:{'BACIA':16, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2', 'CMBPREV':'PC_D2', 'QMONTPREV':'1313'},
    1614:{'BACIA':16, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2', 'CMBPREV':'ENSWRFMED', 'QMONTPREV':'1314'},
    1615:{'BACIA':16, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2', 'CMBPREV':'ENSWRFMED', 'QMONTPREV':'1315'},

    # Simulações B17
    1700:{'BACIA':17, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2'},
    # Previsões B17
    1710:{'BACIA':17, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2', 'CMBPREV':'0', 'QMONTPREV':'1510'},
    1711:{'BACIA':17, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2', 'CMBPREV':'PC_D2', 'QMONTPREV':'1511'},
    1712:{'BACIA':17, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2', 'CMBPREV':'0', 'QMONTPREV':'1512'},
    1713:{'BACIA':17, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2', 'CMBPREV':'PC_D2', 'QMONTPREV':'1513'},
    1714:{'BACIA':17, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2', 'CMBPREV':'ENSWRFMED', 'QMONTPREV':'1514'},
    1715:{'BACIA':17, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2', 'CMBPREV':'ENSWRFMED', 'QMONTPREV':'1515'},

    # Simulações B18
    1800:{'BACIA':18, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2'},
    # Previsões B18
    1810:{'BACIA':18, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2', 'CMBPREV':'0', 'QMONTPREV':'0'},
    1811:{'BACIA':18, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2', 'CMBPREV':'PC_D2', 'QMONTPREV':'0'},
    1812:{'BACIA':18, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2', 'CMBPREV':'ENSWRFMED', 'QMONTPREV':'0'},

    # Simulações B19
    1900:{'BACIA':19, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2'},
    # Previsões B19
    1910:{'BACIA':19, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2', 'CMBPREV':'0', 'QMONTPREV':'0'},
    1911:{'BACIA':19, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2', 'CMBPREV':'PC_D2', 'QMONTPREV':'0'},
    1912:{'BACIA':19, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2', 'CMBPREV':'ENSWRFMED', 'QMONTPREV':'0'},

    # Simulações B20
    2000:{'BACIA':20, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2'},
    # Previsões B20
    2010:{'BACIA':20, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2', 'CMBPREV':'0', 'QMONTPREV':'/Conceitual/prev_caxias.txt'},
    2011:{'BACIA':20, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2', 'CMBPREV':'PC_D2', 'QMONTPREV':'/Conceitual/prev_caxias.txt'},
    2012:{'BACIA':20, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2', 'CMBPREV':'ENSWRFMED', 'QMONTPREV':'/Conceitual/prev_caxias.txt'},

    # Simulações B21
    2100:{'BACIA':21, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2'},
    2101:{'BACIA':21, 'MODELO':'SACSIMPLES', 'PARAM':'4', 'CMBOBS':'MEDIA'},
    2102:{'BACIA':21, 'MODELO':'SACFRACAO', 'PARAM':'1,2,3', 'CMBOBS':'MEDIA'},
    # Previsões B21
    2110:{'BACIA':21, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2', 'CMBPREV':'0', 'QMONTPREV':'2010'},
    2111:{'BACIA':21, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2', 'CMBPREV':'PC_D2', 'QMONTPREV':'2011'},
    2112:{'BACIA':21, 'MODELO':'SACFRACAO', 'PARAM':'1,2,3', 'CMBOBS':'MEDIA', 'CMBPREV':'0', 'QMONTPREV':'2010'},
    2113:{'BACIA':21, 'MODELO':'SACFRACAO', 'PARAM':'1,2,3', 'CMBOBS':'MEDIA', 'CMBPREV':'MEDIA', 'QMONTPREV':'2011'},
    2114:{'BACIA':21, 'MODELO':'RRR', 'PARAM':'2003', 'CMBOBS':'PC_D2', 'CMBPREV':'ENSWRFMED', 'QMONTPREV':'2012'},
    2115:{'BACIA':21, 'MODELO':'SACFRACAO', 'PARAM':'1,2,3', 'CMBOBS':'MEDIA', 'CMBPREV':'ENSWRFMED', 'QMONTPREV':'2012'}
}

# Lista dos códigos de simulação, na sequência em que devem ser executadas no modo operacional
listaprev = [110, 111, 112, 113, 114, 115, 210, 211,  212, 213, 214, 215, 310, 311, 312, 313, 314, 315, 410, 411, 412, 413, 414, 415,
             510, 511, 512, 513, 514, 515, 610, 611, 612, 613, 614, 615, 710, 711, 712, 713, 714, 715, 810, 811, 812, 813, 814, 815,
             910, 911, 912, 913, 914, 915, 1010, 1011, 1012, 1013, 1110, 1111, 1112, 1113, 1210, 1211, 1212, 1213, 1310, 1311, 1312, 1313,
            1410, 1411, 1412, 1413, 1510, 1511, 1512, 1513, 1610, 1611, 1612, 1613, 1710, 1711, 1712, 1713, 1810, 1811, 1910, 1911,
            2010, 2011, 2110, 2111, 2112, 2113]

listaprev2 = [112, 114, 116, 117, 212, 214, 216,  217, 312, 314, 316, 317, 412, 414, 416, 417, 512, 514, 516, 517,
              612, 614, 616,  617, 712, 714, 716, 717, 812, 814, 816,  817, 912, 914, 916,  917, 1010, 1012, 1014, 1015,
             1110, 1112, 1114, 1115, 1210, 1212, 1214, 1215, 1218, 1219,  1310, 1312, 1314, 1315, 1410, 1412, 1414, 1415, 1510, 1512, 1514, 1515,
             1610, 1612, 1614, 1615, 1710, 1712, 1714, 1715, 1810, 1812, 1910, 1912, 2010, 2012, 2110, 2112, 2114, 2115]
# +-=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---+








# +---------------------------------------------------------------------------------------------------------------------------------+
# |          DADOS DE ENTRADA DA MODELAGEM CONVENCIONAL                                                                             |
# +-=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---+
class entradas(object):
    """ Clase para agregar informações e dados a serem utilizados em ambiente de simulação/previsão hidrológica. 
    A variável deve ser inicializada com os seguintes atributos:
    > self.bacia = var_bacia, onde var_bacia é uma variável bacia (ver iguacu.py);
    > self.inicio = datahora_inicial, é uma variável datetime que corresponde à primeira hora do período de simulação;
    > self.final = datahora_final, é uma variável datetime que corresponde à última hora do período de simulação.
    Além destes atributos obrigatórios, outros são inicializados com None para serem preenchidas futuramente:
    > self.modelo = 'SACSIMPLES' para uso convencional do modelo Sacramento Simplificado, 'SACFRACAO' para uso do método de fracionamento da hidrógrafa com o modelo SACSIMPLES,
    ou 'RRR' para uso do modelo Rainfall-Runoff-Routing;
    > self.parametros = lista com os valores dos parâmetros (ou dos conjuntos de parâmetros no caso do SACFRACAO) do modelo hidrológico;
    > self.etp = dicionário com a série horária de evapotranspiração potencial indexada por datetime;
    > self.cmb = dicionário com a série horária de chuva média na bacia indexada por datetime;
    > self.qmont = dicionário com a série horária de vazão contribuinte de montante indexada por datetime;
    > self.qobs = dicionário com a série horária de vazão na exutória indexada por datetime. Utilizado em simulações com SACFRACAO;"""
    def __init__(self, var_bacia, datahora_inicial, datahora_final):
        if type(var_bacia).__name__ == 'bacia':
            self.bacia = var_bacia
        else:
            erro = '\n     var_bacia ' + repr(var_bacia) + ' não é uma variável "bacia" [ver iguacu.py]'
            raise ValueError(erro)

        if type(datahora_inicial).__name__ == 'datetime':
            self.inicio = datahora_inicial
        else:
            erro = '\n datahora_inicial ' + repr(datahora_inicial) + ' não é uma variável "datetime"'
            raise ValueError(erro)

        if type(datahora_final).__name__ == 'datetime':
            self.final = datahora_final
        else:
            erro = '\n datahora_final' + repr(datahora_final) + ' não é uma variável "datetime"'
            raise ValueError(erro)
        
        self.modelo = None
        self.parametros = None
        self.etp = None
        self.cmb = None
        self.qmont = None
        self.qobs = None


    def valida_simulacao(self):
        """ Função para verificar se já há informações suficientes na variável para iniciar a etapa de simulação hidrológica. """
        strings_aviso = ['\n     Não há informações suficiente para iniciar a simulação:']

        # Verificando modelo
        if self.modelo not in ["SACSIMPLES", "SACFRACAO", "RRR"]:
            strings_aviso.append('\n     - Modelo hidrológico não reconhecido. Opções: "SACSIMPLES", "SACFRACAO" ou "RRR".')

        else:
            # Conjuntos de parâmetros (se modelo hidrológico já foi definido)
            if self.parametros == None:
                strings_aviso.append('\n     - Parâmetros do modelo hidrológico não especificados.')
            else:
                if self.modelo == 'SACFRACAO':
                    if len(self.parametros) != 3:
                        strings_aviso.append('\n     - O modelo SACFRACAO precisa de três conjuntos de parâmetros.')
                else:
                    if len(self.parametros) != 11:
                        strings_aviso.append('\n     - O modelo '+self.modelo+' precisa de 1 conjunto de 11 parâmetros.')

        # Série de evapotranspiração potencial
        if self.etp == None:
            strings_aviso.append('\n     - Não há dados de evapotranspiração potencial.')

        # Série de chuva média na bacia
        if self.cmb == None:
            strings_aviso.append('\n     - Não há dados de chuva média na bacia.')

        # Série de vazão contribuinte de montante, se for bacia interna
        if len(self.bacia.montante) > 0:
            if self.qmont == None:
                strings_aviso.append('\n     - Não há dados de vazão contribuinte de montante.')

        # Série de vazão observada na exutória, se for o modelo SACFRACAO
        if self.modelo == 'SACFRACAO':
            if self.qobs == None:
                strings_aviso.append('\n     - Não há dados de vazão observada na exutória.')

        # Retornando status para simulação
        if len(strings_aviso) == 1:
            return True, '\n     Quantidade de dados e informações adequada para executar simulação hidrológica.'
        else:
            aux = strings_aviso[0]
            for i in range(1,len(strings_aviso)):
                aux += strings_aviso[i]
            return False, aux




def serie_ETP(numbac, intervalo):
    """ Função para transferir dados horários da série climática de evapotranspiração potencial da sub-bacia para o período desejado.

    Descrição das variáveis de entrada:
 > numbac    = inteiro correspondente ao número da bacia no SISPSHI2;
 > intervalo = lista contendo dois elementos: intervalo[0] é a variável datetime do ínicio da série, intervalo[1] o datetime do final. """
    # Armazendo série de dados climatológicos
    clim = {}
    arq = open(str('%s/Dados_Bacias/etpclim_%2.2i.txt' % (base, numbac)), 'r')
    for lin in arq.readlines():
        lin = lin.split()
        dt  = lin[0]+lin[1]+lin[2]
        clim[dt] = float(lin[3])
    arq.close()

    # Gerando dicionário de evapotranspiração para o período desejado
    mtz, dt = {}, intervalo[0]
    while dt <= intervalo[1]:
        mtz[dt] = clim[str('%2.2i%2.2i%2.2i' % (dt.month, dt.day, dt.hour))]
        dt += timedelta(hours = 1)

    del clim
    return mtz




def EntradaPadrao(BAC, t0, tN, codsim):
    """ Função para criar variável do tipo 'entradas', para os processos de simulação utilizados mais frequentemente no SISPSHI2.
> BAC    = variável da classe bacia();
> t0, tN = datahora inicial e final, respectivamente, do período de simulação. Se for previsão pega tref em ~/SISPSHI2/data.txt;
> codsim = código da simulação, deve ser uma das chaves do dicionário bdsimuls."""

    # Inicializando gerente de modelagem
    cliente = entradas(BAC, t0, tN)
    
    # Lista das variáveis datahora do período de modelagem
    datas, t = [], t0
    while t <= tN:
        datas.append(t)
        t += timedelta(hours = 1)

    # Série de evapotranspiração potencial
    cliente.etp = serie_ETP(BAC.numero, [t0, tN])

    # Informações gerais da modelagem
    if codsim not in bdsimuls.keys():
        print '\n\n     Código de simulação,', repr(codsim), ' não é válido!\n'
        raise
    else:
        info = bdsimuls[codsim]
        previsao, tref = False, tN
        if 'CMBPREV' in info.keys():
            previsao = True
            tref = dataexec(['datareferencia']) #ESSA CHAMADA de dataexec aqui dificulta execucao em datas diferentes!
            aux = tN - tref
            nhor = aux.days*24 + aux.seconds/3600

    """ Dados do período de simulação (apenas dados observados) """
    # Série de CMB
    laux = [ str('%s/Dados_Bacias/cmb_%2.2i.txt' % (base, BAC.numero)), TipoCMB[info['CMBOBS']] ]
    cliente.cmb = serie_horaria( [laux], [t0, tref])

    # Série de vazão de montante
    """ Bacias de cabeceira recebem uma série zeros (contribuição de montante é nula). Pode-se, inclusive, extender a série de
    zeros até o período de previsão (se for o caso), pois a vazão de montante também será nula nesse período. Para bacias internas
    deve-se somar as séries de vazão observadas nas sub-bacias a montante. """
    if len(BAC.montante) == 0:
        cliente.qmont = dict( [(dt, 0.0) for dt in datas] )
    else:
        lista = []
        for sbac in BAC.montante:
            arquivo = str('%s/Dados_Bacias/vazao_%2.2i.txt' % (base, sbac))
            lista.append( [arquivo, 5] )    # Lendo sexta coluna do arquivo, vazão preenchida.
        cliente.qmont = serie_horaria(lista, [t0, tref], 'somar')

    # Série de vazão observada sem preenchimento (gerar série modelada para aplicar em preenchimento)
    if not previsao:
        laux = [str('%s/Dados_Bacias/vazao_%2.2i.txt' % (base, BAC.numero)), 4]
        cliente.qobs = serie_horaria( [laux], [t0, tref])
                

    """ Dados do período de previsão """
    if previsao:
        
        # Série de CMB
        if info['CMBPREV'] == '0':
            aux = dict( [(tref+timedelta(hours = i), 0.0) for i in range(1,nhor+1)] ) # dicionário de chuva nula
        elif info['CMBPREV'] == 'ENSWRFMED':
            aux = PrevCMB(BAC, info['CMBPREV'], tref, tN, metodo=2)
        else:
            aux = PrevCMB(BAC, info['CMBPREV'], tref, tN)    # retorna dicionário de dados entre tref+1h e tN
        cliente.cmb.update(aux)                              # agregando dados de CMB prevista

        # Série de vazão de montante prevista
        if info['QMONTPREV'] != '0':
            lista = []

            # Identificando arquivos de dados que serão utilizados
            Lqmp = info['QMONTPREV'].split(',')
            for item in Lqmp:
                """ Os valores contidos na chave 'QMONTPREV' são strings que: (1) podem ser convertidos em inteiros pois são
                códigos de simulações nas bacias a montante ou; (2) nome de arquivo com série de vazão horária. """
                try:
                    idsim   = int(item)
                    arquivo = base + str('/Conceitual/Resultados/%4.4i.txt' % idsim)  #ATENCAO: ISSO AQUI É OK PARA OPERACIONAL, MAS PROBLEMA PARA RODADAS ISOLADAS
                    lista.append([arquivo,6])    # Vazão prevista fica na 7ª coluna, 6 se iniciando no 0.
                except ValueError:
                    # Deve ser um arquivo de dados.
                    if exists(base+item):
                        lista.append([base+item,4])    # Assume que a série de dados é a 5ª coluna, logo após a coluna da hora
                    else:
                        print '\n\n     O arquivo ', repr(base+item), ' não existe!\n'
                        raise
                    
            # Lendo, somando (se houver +1 arquivo) e atualizando série de vazão montante prevista
            aux = serie_horaria(lista, [tref+timedelta(hours=1), tN], 'somar', rejeito=-9e12)
            cliente.qmont.update(aux)

        # Série de vazão observada com preenchimento (série modelada para previsão de vazão)
        laux = [str('%s/Dados_Bacias/vazao_%2.2i.txt' % (base, BAC.numero)), 5]
        cliente.qobs = serie_horaria( [laux], [t0, tref])
 
 
    """ Modelo e Parâmetros
    O SISPSHI2 apresenta certa dinâmica na escolha dos parâmetros dos modelos SACSIMPLES e SACFRACAO. No primeiro
    pode-se desejar escolher o parâmetro específico para a classe da vazão na exutória em tref. No segundo é preciso
    fornecer o conjunto de parâmetros para vazões altas, médias e baixas. O modelo RRR e, em alguns casos o SACSIMPLES,
    utiliza um conjunto de parâmetros genérico (não especializado por classe de magnitude da vazão). """
    cliente.modelo = info['MODELO']
    
    if cliente.modelo == 'RRR':    # Modelo Rainfall Runoff Routing
        aux2 = info['PARAM'].split(',')
        ano = int(aux2[0])
        if ano == 2013:
            aux = ParamRRR(BAC.numero, ano, info['CMBOBS'], int(aux2[1]))
        else:
            aux = ParamRRR(BAC.numero, ano)

    elif cliente.modelo == 'SACSIMPLES':    # Modelo Sacramento Simplificado
        Lparams = info['PARAM'].split(',')

        if len(Lparams) == 1:
            # Designado 1 único conjunto de parâmetros
            aux = ParamSACSIMPLES(BAC.numero, info['CMBOBS'], int(Lparams[0]))

        else: #elif len(Lparams) == 3:
            # Identificando último valor consistente de vazão observada
            qref, i = cliente.qobs[tref], 0
            while qref == None:
                i += 1
                try:
                    qref = cliente.qobs[tref - timedelta(hours = i)]
                except KeyError:
                    print '\n\n     Série de vazão observada não contem dados!\n'
                    raise
                
            # Determinando conjunto de parâmetros conforme a classe da vazão observada em tref
            posto = FluvSISPSHI(cliente.bacia.codigo)
            if qref > posto.Qalta:
                # Parâmetro para vazões altas
                aux = ParamSACSIMPLES(BAC.numero, info['CMBOBS'], int(Lparams[0]))

            elif qref < posto.Qbaixa:
                # Parâmetro para vazões baixas
                aux = ParamSACSIMPLES(BAC.numero, info['CMBOBS'], int(Lparams[2]))

            else:
                # Parâmetro para vazões médias
                aux = ParamSACSIMPLES(BAC.numero, info['CMBOBS'], int(Lparams[1]))

    else: #elif cliente.modelo == 'SACFRACAO':    # Modelo SACSIMPLES com fracionamento do hidrograma
        Lparams = info['PARAM'].split(',')
        
        # Tríade de conjuntos de parâmetros para cada classe de vazão
        aux = [ ParamSACSIMPLES(BAC.numero, info['CMBOBS'], int(Lparams[0])),
                ParamSACSIMPLES(BAC.numero, info['CMBOBS'], int(Lparams[1])),
                ParamSACSIMPLES(BAC.numero, info['CMBOBS'], int(Lparams[2])) ]


    # Repassando conjunto(s) de parâmetros para atributo da variável da classe 'entradas'
    cliente.parametros = aux[:]

    # Completou armazenamento de informações e dados de entrada dos modelos
    return cliente




def EntradaRecuperacao(BAC, t0, tref, tN, codsim):
    """ Função similar a EntradaPadrao(), mas que necessita da data de referência. Serve para executar rodadas passadas e/ou com horizonte
    de previsão diferente. """

    # Inicializando gerente de modelagem
    cliente = entradas(BAC, t0, tN)
    
    # Lista das variáveis datahora do período de modelagem
    datas, t = [], t0
    while t <= tN:
        datas.append(t)
        t += timedelta(hours = 1)

    # Série de evapotranspiração potencial
    cliente.etp = serie_ETP(BAC.numero, [t0, tN])

    # Informações gerais da modelagem
    if codsim not in bdsimuls.keys():
        print '\n\n     Código de simulação,', repr(codsim), ' não é válido!\n'
        raise
    else:
        info = bdsimuls[codsim]


    """ Dados do período de simulação (apenas dados observados) """
    # Série de CMB
    laux = [ str('%s/Dados_Bacias/cmb_%2.2i.txt' % (base, BAC.numero)), TipoCMB[info['CMBOBS']] ]
    cliente.cmb = serie_horaria( [laux], [t0, tref])

    # Série de vazão de montante
    """ Bacias de cabeceira recebem uma série zeros (contribuição de montante é nula). Pode-se, inclusive, extender a série de
    zeros até o período de previsão (se for o caso), pois a vazão de montante também será nula nesse período. Para bacias internas
    deve-se somar as séries de vazão observadas nas sub-bacias a montante. """
    if len(BAC.montante) == 0:
        cliente.qmont = dict( [(dt, 0.0) for dt in datas] )
    else:
        lista = []
        for sbac in BAC.montante:
            arquivo = str('%s/Dados_Bacias/vazao_%2.2i.txt' % (base, sbac))
            lista.append( [arquivo, 5] )    # Lendo sexta coluna do arquivo, vazão preenchida.
        cliente.qmont = serie_horaria(lista, [t0, tref], 'somar')

    # Série de vazão observada sem preenchimento (gerar série modelada para aplicar em preenchimento)
    laux = [str('%s/Dados_Bacias/vazao_%2.2i.txt' % (base, BAC.numero)), 4]
    cliente.qobs = serie_horaria( [laux], [t0, tref])

    # Horizonte de previsão
    x = tN - tref
    nhprev = int(x.days*24 + x.seconds/3600)

    # Série de CMB prevista
    if info['CMBPREV'] == '0':
        aux = dict( [(tref+timedelta(hours = i), 0.0) for i in range(1,nhprev+1)] ) # dicionário de chuva nula
    else:
        aux = PrevCMB(BAC, info['CMBPREV'], tref, tN)    # retorna dicionário de dados entre tref+1h e tN
    cliente.cmb.update(aux)                              # agregando dados de CMB prevista

    # Série de vazão de montante prevista
    if info['QMONTPREV'] != '0':
        lista = []

        # Identificando arquivos de dados que serão utilizados
        Lqmp = info['QMONTPREV'].split(',')
        for item in Lqmp:
            """ Os valores contidos na chave 'QMONTPREV' são strings que: (1) podem ser convertidos em inteiros pois são
            códigos de simulações nas bacias a montante ou; (2) nome de arquivo com série de vazão horária. """
            try:
                idsim   = int(item)
                arquivo = base + str('/Conceitual/Resultados/%4.4i.txt' % idsim)
                lista.append([arquivo,6])    # Vazão prevista fica na 7ª coluna, 6 se iniciando no 0.
            except ValueError:
                # Deve ser um arquivo de dados.
                if exists(base+item):
                    lista.append([base+item,4])    # Assume que a série de dados é a 5ª coluna, logo após a coluna da hora
                else:
                    print '\n\n     O arquivo ', repr(base+item), ' não existe!\n'
                    raise
                
        # Lendo, somando (se houver +1 arquivo) e atualizando série de vazão montante prevista
        aux = serie_horaria(lista, [tref+timedelta(hours=1), tN], 'somar', rejeito=-9e12)
        cliente.qmont.update(aux)

    # Série de vazão observada com preenchimento (série modelada para previsão de vazão)
    laux = [str('%s/Dados_Bacias/vazao_%2.2i.txt' % (base, BAC.numero)), 5]
    cliente.qobs = serie_horaria( [laux], [t0, tref])
 
    # Modelo e Parâmetros
    cliente.modelo = info['MODELO']
    
    if cliente.modelo == 'RRR':    # Modelo Rainfall Runoff Routing
        aux2 = info['PARAM'].split(',')
        ano = int(aux2[0])
        if ano == 2013:
            aux = ParamRRR(BAC.numero, ano, info['CMBOBS'], int(aux2[1]))
        else:
            aux = ParamRRR(BAC.numero, ano)

    elif cliente.modelo == 'SACSIMPLES':    # Modelo Sacramento Simplificado
        Lparams = info['PARAM'].split(',')

        if len(Lparams) == 1:
            # Designado 1 único conjunto de parâmetros
            aux = ParamSACSIMPLES(BAC.numero, info['CMBOBS'], int(Lparams[0]))

        else: #elif len(Lparams) == 3:
            # Identificando último valor consistente de vazão observada
            qref, i = cliente.qobs[tref], 0
            while qref == None:
                i += 1
                try:
                    qref = cliente.qobs[tref - timedelta(hours = i)]
                except KeyError:
                    print '\n\n     Série de vazão observada não contem dados!\n'
                    raise
                
            # Determinando conjunto de parâmetros conforme a classe da vazão observada em tref
            posto = FluvSISPSHI(cliente.bacia.codigo)
            if qref > posto.Qalta:
                # Parâmetro para vazões altas
                aux = ParamSACSIMPLES(BAC.numero, info['CMBOBS'], int(Lparams[0]))

            elif qref < posto.Qbaixa:
                # Parâmetro para vazões baixas
                aux = ParamSACSIMPLES(BAC.numero, info['CMBOBS'], int(Lparams[2]))

            else:
                # Parâmetro para vazões médias
                aux = ParamSACSIMPLES(BAC.numero, info['CMBOBS'], int(Lparams[1]))

    else: #elif cliente.modelo == 'SACFRACAO':    # Modelo SACSIMPLES com fracionamento do hidrograma
        Lparams = info['PARAM'].split(',')
        
        # Tríade de conjuntos de parâmetros para cada classe de vazão
        aux = [ ParamSACSIMPLES(BAC.numero, info['CMBOBS'], int(Lparams[0])),
                ParamSACSIMPLES(BAC.numero, info['CMBOBS'], int(Lparams[1])),
                ParamSACSIMPLES(BAC.numero, info['CMBOBS'], int(Lparams[2])) ]


    # Repassando conjunto(s) de parâmetros para atributo da variável da classe 'entradas'
    cliente.parametros = aux[:]

    # Completou armazenamento de informações e dados de entrada dos modelos
    return cliente

# +-=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---+










# +---------------------------------------------------------------------------------------------------------------------------------+
# |          SIMULAÇÃO HIDROLÓGICA                                                                                                  |
# +-=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---+

def SimulacaoPadrao(cliente):
    """ Executa simulação hidrológica conforme informações armazenadas na variável da classe entrada(), 'cliente'. """
    
    # Verificando se as informações necessárias já foram adicionadas à variável de entrada
    situacao, msg = cliente.valida_simulacao()
    if not situacao: raise IOError(msg)

    # Lista dos timestamps horários durante o período de simulação.
    datas, dt = [], cliente.inicio
    while dt <= cliente.final:
        datas.append(dt)
        dt += timedelta(hours = 1)

    # Primeiro dado consistente de vazão (para inicializar volume no canal)
    Q0, i = cliente.qobs[datas[0]], 0
    while Q0 == None:
        i += 1
        Q0 = cliente.qobs[datas[i]]


    # Executando rodada com modelo Rainfall Runoff Routing
    if cliente.modelo == 'RRR':

        # Estimando volume inicial nos reservatórios do canal
        aux = (Q0 * 3.6 / cliente.bacia.areatot / cliente.parametros[9]) ** (1.0/cliente.parametros[10])
        
        # Inicializando vetor de estados do modelo
        estados = [ cliente.parametros[0]*0.5, cliente.parametros[1]*0.5, aux, aux ]

        # Executando simulação hidrológica ao longo do período
        Qmod = {}
        for dt in datas:
            estados, Qmod[dt] = RRR(cliente.parametros, cliente.bacia.areatot, cliente.bacia.areainc, estados,
                                cliente.etp[dt], cliente.cmb[dt], cliente.qmont[dt])

        del estados, datas
        return Qmod


    # Executando rodada com modelo SACSIMPLES
    if cliente.modelo == 'SACSIMPLES':
        
        # Condições iniciais
        estados = [cliente.parametros[0]*0.5, cliente.parametros[1]*0.5]
        aux = Q0 * 3600 / cliente.parametros[9]
        for i in range(cliente.parametros[10]):
            estados.append(aux)

        return ExecutaSACSIMPLES(cliente.parametros, datas, cliente.etp, cliente.cmb, cliente.qmont, cliente.bacia.areainc,
               estados)


    # Executando rodada com modelo SACFRACAO
    if cliente.modelo == 'SACFRACAO':
        
        # Simulação com parâmetros para vazão alta
        estados = [cliente.parametros[0][0]*0.5, cliente.parametros[0][1]*0.5]
        aux = Q0 * 3600 / cliente.parametros[0][9]
        for i in range(cliente.parametros[0][10]):
            estados.append(aux)
        Qalta = ExecutaSACSIMPLES(cliente.parametros[0], datas, cliente.etp, cliente.cmb, cliente.qmont, cliente.bacia.areainc,
               estados)

        # Simulação com parâmetros para vazão média
        estados = [cliente.parametros[1][0]*0.5, cliente.parametros[1][1]*0.5]
        aux = Q0 * 3600 / cliente.parametros[1][9]
        for i in range(cliente.parametros[1][10]):
            estados.append(aux)
        Qmedia = ExecutaSACSIMPLES(cliente.parametros[1], datas, cliente.etp, cliente.cmb, cliente.qmont, cliente.bacia.areainc,
                 estados)

        # Simulação com parâmetros para vazão baixa
        estados = [cliente.parametros[2][0]*0.5, cliente.parametros[2][1]*0.5]
        aux = Q0 * 3600 / cliente.parametros[2][9]
        for i in range(cliente.parametros[2][10]):
            estados.append(aux)
        Qbaixa = ExecutaSACSIMPLES(cliente.parametros[2], datas, cliente.etp, cliente.cmb, cliente.qmont, cliente.bacia.areainc,
                 estados)

        # Vazão modelada com ponderação pela classe da vazão
        Qmod = Fracionamento(FluvSISPSHI(cliente.bacia.codigo), datas, cliente.qobs, Qalta, Qmedia, Qbaixa)
        
        del Qalta, Qmedia, Qbaixa, estados
        return Qmod




def Fracionamento(posto, datas, Qobs, Qalta, Qmedia, Qbaixa):
    """ Aplicando método de ponderação entre simulações com parâmetros especializados em vazão alta, média e baixa.

    Variáveis de entrada:
> posto  = variável da classe posto_fluvio (ver iguacu.py) com os atributos que definem limite de vazão baixa e alta;
> datas  = lista dos timestamp para cada hora do período de simulação;
> Qobs   = dicionário, indexado por datahora, dos dados de vazão observados na exutória da bacia;
> Qalta  = dicionário, indexado por datahora, de vazão simulada com conjunto de parâmetros especializado em vazão alta;
> Qmedia = dicionário, indexado por datahora, de vazão simulada com conjunto de parâmetros especializado em vazão média;
> Qbaixa = dicionário, indexado por datahora, de vazão simulada com conjunto de parâmetros especializado em vazão baixa;

    Descrição do método presente no artigo "Método Alternativo De Calibração E Simulação De Modelos Hidrológicos Baseado No
Fracionamento Do Hidrograma", de Adrien Paris, Guilherme G. Oliveira, Débora Missio Bayer e Walter Collischonn, apresentado
no XIX Simpósio Brasileiro De Recursos Hídricos, em Maceió, 2011.

    Variável de saída: dicionário indexado por datahora com a vazão modelada oriunda da ponderação entre as simulações por
classe de vazão. """
    # Amplitudes
    AQbax = posto.Qbaixa - posto.Qmin
    AQmed = posto.Qalta - posto.Qbaixa
    AQalt = posto.Qalta + AQbax

    ND = len(datas)    # Quantidade de dados no período de simulação
    
    # Computando nova série de vazão modelada
    Qmod = {}
    for i in range(ND):
        dt = datas[i]
        
        """ Sobre vazão inconsistente ou ausente (Qobs == None):
    Se houver falta de dados na série de vazão observada, e sempre haverá se a lista 'datas' envolver período de previsão, então é feita 
uma complementação básica da série. Se o período de falhas estiver no meio da série, ou seja, há dados consistentes nas pontas do período, os dados são recompostos com interpolação linear. Contudo, se o período de falhas começar no primeiro dado ou terminar no último (sem dados consistentes em ambas as pontas) é feita a repetição do valor consistente mais próximo. Poder-se-ia substituir pela média das séries modeladas para vazão alta, média e baixa. Contudo o teste para verificação da qualidade de previsão com o método do fracionamento considerou a repetição da vazão de referência durante o período de previsão no momento de calcular os pesos do fracionamento. Em outras palavras, os pesos calculados a partir da vazão de referência são empregados em todo o período de previsão. """

        # Vazão consistente mais próxima, se a atual não for consistente
        if Qobs[dt] == None:
            
            # Vazão consistente anterior (sempre está uma hora atrás, pois se ela era None já está preenchida)
            if i == 0:
                Q1 = None
            else:
                j1 = i-1
                Q1 = Qobs[datas[j1]]
                
            # Vazão consistente posterior (agora sim busca um valor consistente até chegar ao fim da série) ...
            if i == ND-1:    #... a menos que seja o último!
                Q2 = None
            else:
                for j2 in range(i+1,ND):
                    if Qobs[datas[j2]] != None: break
                Q2 = Qobs[datas[j2]]
                
            # Sem dados!
            if Q1 == None and Q2 == None:
                erro = str('\n     Não há dado de vazão observada em %s, entre %s e %s,' % (posto.nome, datas[0], datas[-1]))
                erro += 'para aplicar método de fracionamento do hidrograma.\n'
                raise ValueError(erro)

            # Reconstituindo ...
            if Q1 == None:
                Qobs[dt] = Q2
            elif Q2 == None:
                Qobs[dt] = Q1
            else:
                Qobs[dt] = (Q2-Q1)*(i-j1)/(j2-j1) + Q1

        # Seguindo com o método do fracionamento
        if Qobs[dt] <= posto.Qbaixa:    # Faixa de vazões baixas
            peso_media = ( ((Qobs[dt]-posto.Qmin)/AQbax)**2 ) * 0.5
            peso_baixa = 1.0 - peso_media
            peso_alta  = 0.0

        elif Qobs[dt] > posto.Qbaixa and Qobs[dt] <= posto.Qalta:    # Faixa de vazões médias
            peso_alta  = ( ((Qobs[dt]-posto.Qbaixa)/(AQmed))**2.5 ) * 0.5
            peso_baixa = ( ((posto.Qalta-Qobs[dt])/(AQmed))**2.5 ) * 0.5
            peso_media = 1.0 - (peso_alta + peso_baixa)

        elif Qobs[dt] > posto.Qalta and Qobs[dt] <= AQalt:    # Faixa de vazões média-altas
            peso_media = ( ((AQalt-Qobs[dt])/AQbax)**2 ) * 0.5
            peso_alta  = 1.0 - peso_media
            peso_baixa = 0.0

        else:    # (Qobs > AQalt) Vazões muito altas
            peso_alta, peso_media, peso_baixa = 1.0, 0.0, 0.0

        # Vazão modelada
        Qmod[dt] = peso_alta*Qalta[dt] + peso_media*Qmedia[dt] + peso_baixa*Qbaixa[dt]

    return Qmod




def ExecutaSACSIMPLES(param, datas, evap, cmb, qmont, area, condinic, retorna_estados=False):
    """ Executando simulação horária com o modelo Sacramento Simples.
    
    Variáveis de entrada:
> param = lista com os 11 parâmetros do modelo;
> datas = lista com variáveis datetime de cada hora do período de simulação;
> evap  = dicionário de dados de evapotranspiração potencial (evap.keys() == datas);
> cmb   = dicionário de chuva média na bacia (cmb.keys() == datas);
> qmont = dicionário de vazão contribuinte de montante (qmont.keys() == datas);
> area  = área incremental da sub-bacia em km²;
> condinic = lista com os valores dos armazenamentos do modelo para datas[0];
> retorna_estados = booleano para informar se deve retornar dicionário dos armazenamentos do modelo (veja variáveis de saída).

    Ordem obrigatória dos parâmetros:
param[0] =  UZWM: capacidade máxima de armazenamento da camada superior do solo (mm);
param[1] =  LZWM: capacidade máxima de armazenamento da camada inferior do solo (mm);
param[2] =   UZK: taxa de transferência lateral da camada superior do solo (%/dia);
param[3] =   LZK: taxa de transferência lateral da camada inferior do solo (%/dia);
param[4] = ZPERC: coeficiente da equação de percolação (adim.);
param[5] =  IMPX: expoente da equação de escoamento direto proveniente da área impermeável (adim.);
param[6] =  REXP: expoente da equação de percolação (adim.);
param[7] =  TRNX: expoente da equação para cálculo da transpiração (adim.)
param[8] =  SIDE: fração do escoamento subterrâneo que chega ao canal (%);
param[9] =  beta: fração do volume do reservatório de canal que escoa por passo de tempo (%);
param[10]=   NRC: número de reservatórios conceituais (inteiro).

    Variáveis de saída (todos em escala horária):
> qmod    = dicionário de vazão modelada (qmod.keys() == datas);
> estados = dicionário de estados do modelo (umidade das camadas do solo e volume de água nos tramos do canal;
            estados.keys() == datas).

    Funcionamento:
> Seguindo a ordem dos passos de tempo em 'datas', aciona a função SAC_SIMPLES() para atualizar os estados do solo e obter a vazão
gerada pela bacia. Este dado, mais a vazão de contribuinte de montante, são fornecidos à função CRCL() para obter o efeito de
propagação em canal e a vazão modelada em si. Note que aqui não é utilizada vazão observada, portanto não há qualquer pós-processamento
envolvendo vazão modelada e vazão observada."""
    param[10] = int(param[10])    # NRC deve ser um inteiro daqui pra frente

    # Condição inicial do solo da bacia
    Rsolo = [condinic[0], condinic[1]]
    if Rsolo[0] > param[0] or Rsolo[0] < 0:
        erro = '\n     Volume de água na camada superior é inconsistente!'
        erro += str('\n     Condição inicial = %f mm; Máximo comportado = %f mm.\n' % (Rsolo[0], param[0]))
        raise ValueError(erro)
    if Rsolo[1] > param[1] or Rsolo[1] < 0:
        erro = '\n     Volume de água na camada inferior é inconsistente!'
        erro += str('\n     Condição inicial = %f mm; Máximo comportado = %f mm.\n' % (Rsolo[1], param[1]))
        raise ValueError(erro)

    # Condição inicial dos reservatórios de propagação
    Rprop = condinic[2:]
    if len(Rprop) != param[10]:
        erro = '\n     Número de reservatórios na condição inicial é diferente do parâmetro do modelo.'
        erro += str('\n     Valores na C.I. = %i;    NRC = %i.\n' % (len(Rprop), param[10]))
        raise ValueError(erro)
    for i in range(param[10]):
        if Rprop[i] < 0:
            erro = str('\n     Cond. inicial do reservatório %i de propação é nula!\n' % (i+1))
            raise ValueError(erro)

    # Inicializando dicionários de dados simulados
    Qmod, Stados = {}, {}

    # Ciclo temporal da simulação
    for dt in datas:
        Rsolo, VolBac = SAC_Simples(param,Rsolo,evap[dt],cmb[dt])
        VolBac  = VolBac * area * 1000    #Convertendo volume da bacia de mm para m³
        try:
            VolMont = max(qmont[dt] * 3600, 0.0) #Volume proveniente de montante em 1 hora.
            """ O volume proveniente das bacias de montante precisa ser testado quanto ao seu sinal. Não pode ser negativo!
            Em alguns casos, o modelo está tão descolado do observado que após a ancoragem parte da série simulada torna-se
            negativa, e isto é propagado a jusante. Por este motivo há a operação 'max' na atribuição do valor VolMont acima. """
        except TypeError:
            print '\n\n    Vazao de montante é None.\n', dt, '\n'
            raise
        Rprop, VolMod = CRCL(param, Rprop, VolBac, VolMont)
        
        # Estados do modelo ao final do passo de integração
        Stados[dt] = [Rsolo[0], Rsolo[1]].extend(Rprop)    # Não fazer Rsolo.extend(Rprop). Pode vincular Stados a Rsolo.
        
        # Vazão modelada, m³/s
        Qmod[dt] = VolMod / 3600.0

    # Retornando dados modelados
    if retorna_estados:
        return Qmod, Stados
    else:
        del Stados
        return Qmod




# MODELO SAC_SMA SIMPLIFICADO
def SAC_Simples(Param,Ssolo,PET,PREC):
    """ Executa a integração de 1 passo de tempo (horário) do modelo Sacramento Soil Moisture Accounting Simplificado.
    'Param' = lista com os 11 parâmetros do modelo (embora só use 9 na fase bacia)
    'Ssolo' = lista com o volume dos reservatórios do solo, superior e inferior respectivamente, em mm.
    'PET'   = valor da evapotranspiração potencial para a hora a ser integrada.
    'PREC'  = valor da chuva média na bacia para a hora a ser integrada.
    
    Irá retornar a lista de armazenamentos do solo atualizada e o volume (em mm) gerado pela bacia."""
    
    #Calculando a perda por evapotranspiração, na zona superior, no intervalo
    E1 = PET * (Ssolo[0]/Param[0])    #E1  = Evapotranspiração ocorrida na zona superior (mm)

    #Descontando a evapotranspiração da zona superior do solo, porém não pode ser perdida mais água
    #do que há nesta camada.
    if E1 > Ssolo[0]:
        E1 = Ssolo[0]
        Ssolo[0] = 0.0
    else:
        Ssolo[0] = Ssolo[0] - E1
    RED = PET - E1    #RED = Resíduo da evapotranspiração para ser descontada na camada inferior do solo

    #Calculando a perda por evapotranspiração, na zona inferior, no intervalo
    # E2  = Evapotranspiração ocorrida na zona inferior (mm)
    E2 = RED * ((Ssolo[1]/Param[1]) ** Param[7])

    #Descontando a evapotranspiração da zona inferior do solo, porém não pode ser perdida mais água
    #do que há nesta camada.
    if E2 > Ssolo[1]:
        E2 = Ssolo[1]
        Ssolo[1] = 0.0
    else:
        Ssolo[1] = Ssolo[1] - E2

    #Calculando os escoamentos de percolação e superficial.
    # TWX   = Umidade em excesso na zona superior, no intervalo (mm)
    # ROIMP = Escoamento superficial da área impermeável
    try:
        ROIMP = PREC * ((Ssolo[0]/Param[0]) ** Param[5])
        PREC = PREC - ROIMP
    except TypeError:
        print 'PREC recebeu valor None!'
        ROIMP, PREC = 0.0, 0.0

    if (PREC + Ssolo[0]) > Param[0]:
        TWX = PREC + Ssolo[0] - Param[0]
        Ssolo[0] = Param[0]
    else:
        TWX = 0.0
        Ssolo[0] = Ssolo[0] + PREC

    #Inicializando acumuladores do intervalo DT
    SBF   = 0.0                #Escoamento de base
    SSUR  = 0.0                #Escoamento superficial
    SIF   = 0.0                #Escoamento interno (subsuperficial)
    SPERC = 0.0                #Percolação

    #Determinando os incrementos computacionais de tempo para o intervalo básico de tempo.
    #Nenhum incremento irá exceder 5.0 milimetros de Ssolo[0]+TWX.
    # NINC = Número de incrementos de tempo em que o intervalo de tempo será dividido para posterior
    #        contabilidade da umidade do solo.
    # DINC = Comprimento de cada incremento em dias
    # PINC = Quantidade de umidade disponível para cada incremento
    NINC = int( round(1.0 + 0.20*(Ssolo[0]+TWX), 0) )
    DINC = (1.0/NINC) / 24.0    # "/ 24" = "* (1/24)". "1/24" é o DT [dias], ou seja, dados horários.
    PINC = TWX/NINC

    #Calculando frações de deplecionamento da água para o tempo de incremento, sendo que as taxas de
    #depleção são para um dia.
    # DUZ  = Depleção de água da zona superior, por incremento
    # DLZ  = Depleção de água da zona inferior, por incremento
    DUZ  = 1.0 - ( (1.0-Param[2])**DINC )
    DLZ  = 1.0 - ( (1.0-Param[3])**DINC )


    # INICIANDO CICLO DE INTEGRAÇÃO PARA CADA INCREMENTO, PARA O INTERVALO DE TEMPO
    for I in range(NINC):

        #Calculando o escoamento de base da zona inferior e o acumulado do intervalo de tempo
        # BF = Escoamento de base
        BF   = Ssolo[1] * DLZ
        SBF  = SBF + BF
        Ssolo[1] = Ssolo[1] - BF

        #Calculando o volume percolado
        # UZRAT = Umidade da camada superior do solo 
        # LZRAT = Umidade da camada inferior do solo
        # PERC = Volume percolado no incremento de tempo
        UZRAT = Ssolo[0] / Param[0]
        LZRAT = Ssolo[1] / Param[1]
        PERC  = DLZ * Param[1] * (1.0 + Param[4] * ((1.0-LZRAT)**Param[6])) * UZRAT

        #Verificando se o volume percolado está realmente disponível na camada superior
        if PERC > Ssolo[0]:
            PERC = Ssolo[0]

        #Verificando se a camada inferior comporta o volume percolado
        if (PERC+Ssolo[1]) > Param[1]:
            PERC = Param[1] - Ssolo[1]

        #Transferindo água percolada
        Ssolo[0] = Ssolo[0] - PERC
        Ssolo[1] = Ssolo[1] + PERC
        SPERC = SPERC + PERC

        #Calculando o escoamento interno e o acumulado
        # DEL = Escoamento interno
        #OBS: A quantidade PINC ainda não foi adicionada
        DEL  = Ssolo[0] * DUZ
        SIF  = SIF + DEL
        Ssolo[0] = Ssolo[0] - DEL

        #Distribuir PINC entre a zona superior e o escoamento superficial
        SUR = 0.0      
        if PINC > 0.0:
            #Se houver excesso, vira escoamento superficial
            if (PINC+Ssolo[0]) > Param[0]:
                SUR = PINC + Ssolo[0] - Param[0]
                Ssolo[0] = Param[0]
            #Do contrário, adiciona tudo na camada superior
            else:
                Ssolo[0] = Ssolo[0] + PINC
            SSUR = SSUR + SUR

    # FIM DO CICLO DE INTEGRAÇÃO PARA CADA INCREMENTO, PARA O INTERVALO DE TEMPO

    #Descontando volume do escoamento de base que vai para o aquífero
    # BFCC = componente do escoamento de base que vai para o canal
    BFCC = SBF * Param[8]

    #Calculando escoamento afluente da bacia para o canal no intervalo de tempo
    # TCI  = Escoamento afluente total
    # GRND = Escoamento subterrâneo
    # SURF = Escoamento superficial
    TCI = ROIMP + SSUR + SIF + BFCC

    return Ssolo, TCI




# Propagação por Cascata de Reservatórios
def CRCL(Param,Sprop,VOLbac,VOLmont):
    """ Integra o modelo de propagação em canal por Cascata de Reservatórios Conceituais Lineares (CRCL) em 1 passo de
    integração (horário).
    'Param'   = lista com os 11 parâmetros do modelo (9 da fase bacia, o SAC_Simples, e os dois últimos da propagação em si)
    'Ssprop'  = lista com o volume dos reservatórios de propagação. A quantidade de reservatórios é dado pelo parâmetro em
                Param[10] (o último parâmetro da lista)
    'VOLbac'  = volume de escoamento gerado pela bacia em m³/hora
    'VOLmont' = volume da vazão contribuinte das sub-bacias a montante em m³/hora
    
    Irá retornar a lista de armazenamentos de propagação atualizada e a vazão (em m³/hora) na exutória."""
    
    Vprop = [[0.0, 0.0, 0.0] for i in range(Param[10])]

    #Calculando fluxos no início do passo de tempo e adicionando volumes de entrada
    for i in range(Param[10]):
        Vprop[i][0] = Param[9] * Sprop[i]
        Sprop[i] += VOLbac/Param[10]    #Volume produzido pela bacia incremental
    Sprop[0] += VOLmont    #Volume contribuinte de montante

    #Balanço de massa no primeiro reservatório
    Vprop[0][1] = Param[9] * Sprop[0]
    Vprop[0][2] = 0.50 * (Vprop[0][0] + Vprop[0][1])
    Sprop[0]   -= Vprop[0][2]

    #Propagando água entre reservatórios
    for i in range(1,Param[10]):
        Sprop[i]   += Vprop[i-1][2]
        Vprop[i][1] = Param[9] * Sprop[i]
        Vprop[i][2] = 0.50 * (Vprop[i][0] + Vprop[i][1])
        Sprop[i]   -= Vprop[i][2]

    return Sprop, Vprop[Param[10]-1][2]




# MODELO RAINFALL - RUNOFF - ROUTING (3R)
def RRR(Param,Atot,Ainc,Store,PET,PREC,QIN):
    """ Executa a integração de 1 passo de tempo (horário) do modelo 3R.
    'Param' = lista com os 11 parâmetros do modelo
    'Atot' e 'Ainc' = valores da área total e da área incremental da sub-bacia, respectivamente em km².
    'Store' = lista com o volume dos 4 reservatórios do modelo (2 do solo e 2 de propagação) em mm.
    'PET'   = valor da evapotranspiração [mm] potencial para a hora a ser integrada.
    'PREC'  = valor da chuva [mm] média na bacia para a hora a ser integrada.
    'QIN'   = valor da vazão [m³/s] contribuinte das bacias a montante na hora a ser integrada
    
    Irá retornar a lista de armazenamentos atualizada e a vazão simulada (mm/h)."""
    try:
        NSTEP = int(round(PREC*0.5,0)) + 1    # NSTEP é a quantidade de passos de integração dentro.
        if NSTEP < 3: NSTEP = 3
    except TypeError:
        print 'PREC recebeu valor None!'
        NSTEP, PREC = 3, 0.0

    
    h  = 1.0 / float(NSTEP)    # h = StepSize
    hh = h / 2.0
    h6 = h / 6.0
    Linp = [ PET, PREC, max(QIN, 0.0) ]    # Lista dos inputs
    """ O volume proveniente das bacias de montante precisa ser testado quanto ao seu sinal. Não pode ser negativo!
    Em alguns casos, o modelo está tão descolado do observado que após a ancoragem parte da série simulada torna-se negativa, e
    isto é propagado a jusante. Por este motivo há a operação 'max' na atribuição do valor VolMont acima. """
    dSdt1 = derivs(Param, Atot, Ainc, Store, Linp)    # Estimativa inicial das derivadas; dSdt1 = dydx

    for k in range(NSTEP):    # Executa NSTEP passos
        # Primeiro Passo do RK4
        yt = [Store[i] + hh*dSdt1[i] for i in range(4)]
        
        # Segundo Passo do RK4
        dSdt2 = derivs(Param, Atot, Ainc, yt, Linp)       # dSdt2 = dyt
        yt = [Store[i] + hh*dSdt2[i] for i in range(4)]

        # Terceiro Passo do RK4
        dSdt3 = derivs(Param, Atot, Ainc, yt, Linp)       # dSdt3 = dym
        yt = [Store[i] + h*dSdt3[i] for i in range(4)]
        dSdt3 = [dSdt2[i] + dSdt3[i] for i in range(4)]

        # Quarto Passo do RK4
        dSdt2 = derivs(Param, Atot, Ainc, yt, Linp)
        for i in range(4):
            Store[i] = Store[i] + h6 * (dSdt1[i] + dSdt2[i] + 2*dSdt3[i])

    # Computando vazão simulada
    if Store[3] >= 0.0:
        Qout = Param[9] * (Store[3]**Param[10])
        Qout = Qout * Atot/3.6
    else:
        Qout = 0.0

    return Store, Qout

def derivs(Param, Atot, Ainc, S, Linp):
    """ Cálculo das derivadas dos estados (reservatórios) do modelo 3R. """
    dSdt = [0.0 for i in range(4)]
    
    # Forçando consistência!
    for i in range(4):
        if S[i] < 0: S[i] = 0.0
    if S[0] > Param[0]: S[0] = Param[0]
    if S[1] > Param[1]: S[1] = Param[1]

    # Fração de água (umidade) nos reservatórios do solo
    FAS1 = S[0]/Param[0]
    FAS2 = S[1]/Param[1]

    # Escoamentos da fase bacia
    ESUP = Linp[1]*(FAS1**Param[5])                                        #Escoamento Superficial
    PERC = Param[3]*Param[1]*(1.0+Param[4]*((1.0-FAS2)**Param[6]))*FAS1    #Percolação
    EVAP = Linp[0]*FAS1                                                    #Evaporação
    ESUB = Param[2]*S[0]                                                   #Escoamento Subsuperficial
    TRAN = (Linp[0]-EVAP)*(FAS2**Param[7])                                 #Transpiração
    ESOL = Param[3]*S[1]                                                   #Escoamento Subsolo
    EBAS = Param[8]*ESOL + ESUB                                            #Escoamento de Base
    VBAC = ESUP + EBAS                                                     #Vazão gerada na bacia

    #Variação no armazenamento da camada superior do solo
    dSdt[0] = Linp[1] - ESUP - PERC - EVAP - ESUB

    #Variação no armazenamento da camada inferior do solo
    dSdt[1] = PERC - TRAN - ESOL

    #Variação no armazenamento do primeiro tramo
    try:
        dSdt[2] = VBAC*Ainc/Atot + Linp[2]*3.6/Atot - Param[9]*(S[2]**Param[10])
    except TypeError:
        print '\n\n', repr(dSdt[2])
        print repr(VBAC), repr(Ainc), repr(Atot)
        print repr(Linp[2])
        print repr(Param[9]), repr(S[2]), repr(Param[10])
        print '\n\n'
        exit()

    #Variação no armazenamento do tramo final
    dSdt[3] = Param[9]*(S[2]**Param[10]) - Param[9]*(S[3]**Param[10])

    return dSdt
# +-=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---+
