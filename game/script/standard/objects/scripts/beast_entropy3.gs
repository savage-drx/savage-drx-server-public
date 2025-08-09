@impact
#!search self 110 enemy unit 1st
#!if found [gs_object_id>=0] @then0

!search self 110 enemy unit 2nd
!if found [gs_object_id>=0] @then1

!search self 110 enemy unit 3rd
!if found [gs_object_id>=0] @then2

!search self 110 enemy unit 4th
!if found [gs_object_id>=0] @then3


#@then0
#!damageradius self 110 9 enemy unit

@then1
!damageradius self 110 9 enemy unit

@then2
!damageradius self 110 9 enemy unit

@then3
!damageradius self 110 9 enemy unit