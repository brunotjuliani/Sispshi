reset

#set terminal png size 2400, 2400 font arial 16
#set output 'fig01.png'
set size 1, 0.5
set multiplot layout 1,2 ;




set xdata time
set timefmt "%Y %m %d %H"
#set format x "%d/%m %Hh"
# set datafile missing '-999'
set xrange["2017 05 30 13":"2017 06 09 13"]
set ylabel "Vazão [m3]"
set grid

#Figura 1
set title "B09-Uniao da Vitoria";
#set origin 0,0
plot "0912.txt" using 1:7 title "0912" with line, \
     "0914.txt" using 1:7 title "0914" with line, \
     "0916.txt" using 1:7 title "0916" with line, \
     "0917.txt" using 1:7 title "0917" with line

#Figura 2
set title "B12-Foz do Areia";
#set origin 0.5,0
plot "1210.txt" using 1:7 title "1210" with line, \
     "1212.txt" using 1:7 title "1212" with line, \
     "1214.txt" using 1:7 title "1214" with line, \
     "1215.txt" using 1:7 title "1215" with line, \
     "1218.txt" using 1:7 title "1218" with line, \
     "1219.txt" using 1:7 title "1219" with line


#unset multiplot
#set out
pause -1