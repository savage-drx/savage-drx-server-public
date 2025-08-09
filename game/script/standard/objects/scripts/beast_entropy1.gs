@impact
# !testnot target ally
!if target ally @then2
!ifnot target ally @then0

@then0
!if target [gs_object_id>=0] @then1

@then1
# search flags relative to target
!search target 300 ally neutral unit 1st
!if found [gs_object_id>=0] @then5
!search target 300 ally neutral unit 2nd
!if found [gs_object_id>=0] @then5
!search target 300 ally neutral unit 3rd
!if found [gs_object_id>=0] @then5
!search target 300 ally neutral unit 4th
!if found [gs_object_id>=0] @then5

@then2
!if target [gs_object_id>=0] @then3

@then3
# search flags relative to target
!search target 300 enemy neutral unit 1st
!if found [gs_object_id>=0] @then5
!search target 300 enemy neutral unit 2nd
!if found [gs_object_id>=0] @then5
!search target 300 enemy neutral unit 3rd
!if found [gs_object_id>=0] @then5
!search target 300 enemy neutral unit 4th
!if found [gs_object_id>=0] @then5
!stop null

@then5
!weaponfire found beast_entropy1split