@use
!givestate owner fullstop 2500
!attach owner

@attach
!setstate self idle
!delay self 1350

@idling
!die self

@die
!givestateradius owner 180 solar_avatar 10000
!givestate owner solar_avatar 10000

