@spawn
!exec owner "set _ballista_deploy#gs_object_id# 0"

@use
!exec owner "cvarcopy _ballista_deploy#gs_object_id# _deploy"
!if null [_deploy==0] @then0
!if null [_deploy==1] @then1

@then0
!givestate owner human_ballista_deploy -1
!exec owner "set _ballista_deploy#gs_object_id# 1"

@then1
!givestate owner human_ballista_deploy 0
!exec owner "set _ballista_deploy#gs_object_id# 0"