@spawn
!exec self "set _deployed#gs_object_id# 0"

@hit
!exec owner "cvarcopy _ballista_deploy#gs_object_id# _deploy"
!if null [_deploy==1] @then0

@then0
!test target ally
!exec self "cvarcopy _deployed#gs_object_id# repaircheck"
!exec self "cvarcopy gs_game_time gametime"
!exec self "inc gametime -#repaircheck#"
!if null [gametime>=1000] @then1
!if null [gametime<=0] @then9

@then1
!if self [gs_object_healthpercent>=1] @then2
!heal self 50
!exec self "set _deployed#gs_object_id# #gs_game_time#"
!playeffect self repair nearby

@then2
!giveammo self 1 1 0

@then9
!exec self "set _deployed#gs_object_id# 0"
!playeffect self resourcesfull nearby