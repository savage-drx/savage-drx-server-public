@use
!attach target

@attach
!setstate self idle 10000 activate

@activate
!damageradius owner 100 5300
!damage owner 999999

@fizzle
!die self

@idling
!if owner [gs_object_health<1] @then0

@then0
!die self
