@use
!setstate self active

@impact
!hasstate target jera_exclude 1
!if target [gs_object_id>=0] @then0

@then0
!testnot target building
!if target ally @then1
!if target enemy @then2

@then1
!if target [gs_object_healthpercent<1] @then3

@then3
!testnot target siege
!heal target 120
!heal owner 120

@then2
!heal owner 120
