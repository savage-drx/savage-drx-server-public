@use
!toss target 20 1.0

@toss
!setstate self idle
!delay self 5000

@idling
!scan self 50 activate unit neutral enemy

@activate
#!exec owner client "set cl_haze 1"
!delay self 500

@active
!die self

@die
!damageradius self 150 500
#!exec owner client "set cl_haze 0"
