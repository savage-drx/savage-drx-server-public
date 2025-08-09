@impact
!if target [gs_object_id>=0] @then0

@then0
!testnot target building
!testnot target ally
!testnot target npc
!testnot target siege
!hasstate target sheepify 1
!exec target "cvarcopy gs_object_name #gs_object_id#_sheep_old_unit"
!changeunit target human_sheep
!exec target client "invswitch 0"
!playeffect target sheepify_burst nearby
!playeffect target sheepify_fumes nearby
!givestate target sheepify 8000
!attach target

@attach
!setstate self idle 8000 activate

@activate
!exec owner "cvarcopy #gs_object_id#_sheep_old_unit sheep_old_unit" 
!changeunit owner #sheep_old_unit#
!playeffect target sheepify_burst nearby
!playeffect target sheepify_fumes nearby
!die self

