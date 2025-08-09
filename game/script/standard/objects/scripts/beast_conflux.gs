@spawn
!exec self "set conflux#gs_object_id# 0"
!exec self "set conflux#gs_object_id#entropy 0"
!exec self "set conflux#gs_object_id#fire 0"
!exec self "set conflux#gs_object_id#strata 0"
!if self [!altars_set] @then1

@then1
!exec self "set altars_entropy 0"
!exec self "set altars_fire 0"
!exec self "set altars_strata 0"
!exec self "set altars_set 1"

@idling
!exec self "cvarcopy conflux#gs_object_id#entropy checkdrop"
!if self [checkdrop>=1] @then7
!exec self "cvarcopy conflux#gs_object_id#fire checkdrop"
!if self [checkdrop>=1] @then8
!exec self "cvarcopy conflux#gs_object_id#strata checkdrop"
!if self [checkdrop>=1] @then9

@walking
!exec self "cvarcopy conflux#gs_object_id#entropy checkdrop"
!if self [checkdrop>=1] @then7
!exec self "cvarcopy conflux#gs_object_id#fire checkdrop"
!if self [checkdrop>=1] @then8
!exec self "cvarcopy conflux#gs_object_id#strata checkdrop"
!if self [checkdrop>=1] @then9

@chasing
!exec self "cvarcopy conflux#gs_object_id#entropy checkdrop"
!if self [checkdrop>=1] @then7
!exec self "cvarcopy conflux#gs_object_id#fire checkdrop"
!if self [checkdrop>=1] @then8
!exec self "cvarcopy conflux#gs_object_id#strata checkdrop"
!if self [checkdrop>=1] @then9

@then7
!if self [altars_entropy>=3] @then4
!spawnobject owner beast_altar_entropy #gs_object_team# neutral nearby
!exec self "inc conflux#gs_object_id#entropy -1"

@then8
!if self [altars_fire>=3] @then5
!spawnobject owner beast_altar_fire #gs_object_team# neutral nearby
!exec self "inc conflux#gs_object_id#fire -1"

@then9
!if self [altars_strata>=3] @then6
!spawnobject owner beast_altar_strata #gs_object_team# neutral nearby
!exec self "inc conflux#gs_object_id#strata -1"

@then4
!exec self "giveresource entropy 150 #gs_object_team#"

@then5
!exec self "giveresource fire 50 #gs_object_team#"

@then6
!exec self "giveresource strata 50 #gs_object_team#"

@die
