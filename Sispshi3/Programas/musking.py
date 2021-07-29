real    :: C1, C2, C3
real    :: Km         !K travel time in hrs in reach
real    :: X          !weighting factors 0<=X<=0.5
real    :: dt         !routing period in hrs
real    :: avgbf      !average base flow for initial condition
real    :: qup        !inflow from previous timestep
real    :: quc        !inflow  of current timestep
real    :: qdp        !outflow of previous timestep
real    :: dth        !timestep in hours
integer :: idx        ! index

dth = dt/3600.    !hours in timestep
C1 = (dth - 2.0 *Km*X)/(2.0*Km*(1.0-X)+dth)
C2 = (dth+2.0*Km*X)/(2.0*Km*(1.0-X)+dth)
C3 = (2.0*Km*(1.0-X)-dth)/(2.0*Km*(1.0-X)+dth)
MUSKING = (C1*quc)+(C2*qup)+(C3*qdp)
