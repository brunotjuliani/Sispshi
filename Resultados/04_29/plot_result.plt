reset

#set terminal png size 1200, 900 font arial 14
#set output 'fig01.png'

set xdata time
set timefmt "%Y %m %d %H"
set format x "%d/%m %Hh"

# set datafile missing '-999'
 #set xrange["2017 05 29 11 00":"2017 05 29 11 00"]
set ylabel "Vazão [m3]"
set grid

plot "1216.txt" using 1:7 title "1216" with line, \
     "1217.txt" using 1:7 title "1217" with line, \
     "1218.txt" using 1:7 title "1218" with line, \
     "1219.txt" using 1:7 title "1219" with line

#set out
pause -1