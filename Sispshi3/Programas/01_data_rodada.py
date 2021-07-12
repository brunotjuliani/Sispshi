import datetime as dt
import csv

## 1 - DATAS PADRAO
#Ultima Rodada
att_anterior = open('../Dados/disparo.txt')
data_ant = att_anterior.readline().strip()
data0 = att_anterior.readline().strip()
att_anterior.close()

#Rodada Atual
hora = dt.datetime.utcnow() #- dt.timedelta(hours = 1)
dispara = dt.datetime(hora.year, hora.month, hora.day,  hora.hour,
                      tzinfo=dt.timezone.utc)

#Atualiza arquivo com ultima rodada e rodada atual
with open("../Dados/disparo.txt", "w",newline='') as file:
    writer = csv.writer(file)
    writer.writerow([data0])
    writer.writerow([dispara])

print('#####-----#####-----#####-----#####-----#####-----#####')
print(f'01 - Rodada com atualiazação até {dispara}')
print('#####-----#####-----#####-----#####-----#####-----#####\n')
