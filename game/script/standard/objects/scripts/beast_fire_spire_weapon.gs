@impact
!if target [gs_object_id>=0] @then0
!if target [gs_object_id>=0] @then1
!scan self 150 activate unit building neutral enemy

@activate
!damageradius self 150 500

@then0
!exec null "set dmg 500"
!hasstate target beast_protect
!exec null "set dmg 0"

@then1
!damage target #dmg#
