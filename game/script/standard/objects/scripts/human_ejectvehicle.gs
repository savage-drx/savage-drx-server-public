@use
#!notify target all EJECT
!test target ally
!test target npc
!test target healer
#Disables balloon explosion damage in case of ejecting the worker
!exec target "set balloon#gs_object_id#damage 0"
!die target
!spawnobject target human_worker #gs_object_team# neutral nearby

