@spawn
!exec self "cvarcopy gs_game_time #gs_object_id#_spawntime"
!exec self "createvar _beacon#gs_object_id#_lifecounter 0"
!exec self "set oldtime 0"
!exec self "cvarcopy ophelia_#gs_object_team# owner_id#gs_object_id#"
!setstate self idle

@idling
!givestateradius self 180 ophelia_tag 1000 
!exec self "cvarcopy #gs_object_id#_spawntime spawntime"
!exec self "cvarcopy gs_game_time gametime"
!exec self "inc gametime -#spawntime#"
!exec self "inc oldtime 1"
!if null [gametime>=10000] @then0
!if null [oldtime>=10] @then9

!exec self "cvarcopy owner_id#gs_object_id# owner_id"
!targetIndex self #owner_id#
!hasstate found ophelia_tag
!test found healer
!givestate found manaburn 1000

@then9
!spawngoodie self ammo 1 #gs_object_team# coords #gs_object_posx# #gs_object_posy# 50
!exec self "set oldtime 0"

@then0
!spawngoodie self extra4 1 #gs_object_team# coords #gs_object_posx# #gs_object_posy# 50
!die self

@die
#!exec self "set beacon_height 0"
