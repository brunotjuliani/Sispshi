real    :: C1, C2, C3
real    :: KMSK         !K travel time in hrs in reach
real    :: XMSK          !weighting factors 0<=XMSK<=0.5
real    :: dt         !routing period in hrs
real    :: avgbf      !average base flow for initial condition
real    :: qup        !inflow from previous timestep
real    :: quc        !inflow  of current timestep
real    :: qdp        !outflow of previous timestep
real    :: dth        !timestep in hours
integer :: idx        ! index

dth = dt/3600.    !hours in timestep
C1 = (dth - 2.0 *KMSK*XMSK)/(2.0*KMSK*(1.0-XMSK)+dth)
C2 = (dth+2.0*KMSK*XMSK)/(2.0*KMSK*(1.0-XMSK)+dth)
C3 = (2.0*KMSK*(1.0-XMSK)-dth)/(2.0*KMSK*(1.0-XMSK)+dth)
MUSKING = (C1*quc)+(C2*qup)+(C3*qdp)
