@idling
!if self [gs_object_team!=0] @then0
!if self [gs_object_team==0] @then1

@then0
!exec self "objedit gold_autominer"
!exec self "objset isVulnerable 1"
!exec self "cvarcopy minerhp_#gs_object_id# minertemp"
!exec self "set dmgtemp [gs_object_health - minertemp]"
!damage self #dmgtemp#
!damage self 25 1
!exec self "set minerhp_#gs_object_id# #gs_object_health#"
!exec self "objedit gold_autominer"
!exec self "objset isVulnerable 0"

@then1
!exec self "set minerhp_#gs_object_id# #gs_object_health#"
