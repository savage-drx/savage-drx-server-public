@spawn
!exec self "set apc#gs_object_id# 0"
!exec self "set apc#gs_object_id#chemical 0"
!exec self "set apc#gs_object_id#magnetic 0"
!exec self "set apc#gs_object_id#electric 0"
!if self [!caches_set] @then1

@then1
!exec self "set caches_chemical 0"
!exec self "set caches_magnetic 0"
!exec self "set caches_electric 0"
!exec self "set caches_set 1"

@idling
!exec self "cvarcopy apc#gs_object_id#chemical checkdrop"
!if self [checkdrop>=1] @then7
!exec self "cvarcopy apc#gs_object_id#magnetic checkdrop"
!if self [checkdrop>=1] @then8
!exec self "cvarcopy apc#gs_object_id#electric checkdrop"
!if self [checkdrop>=1] @then9

@walking
!exec self "cvarcopy apc#gs_object_id#chemical checkdrop"
!if self [checkdrop>=1] @then7
!exec self "cvarcopy apc#gs_object_id#magnetic checkdrop"
!if self [checkdrop>=1] @then8
!exec self "cvarcopy apc#gs_object_id#electric checkdrop"
!if self [checkdrop>=1] @then9

@chasing
!exec self "cvarcopy apc#gs_object_id#chemical checkdrop"
!if self [checkdrop>=1] @then7
!exec self "cvarcopy apc#gs_object_id#magnetic checkdrop"
!if self [checkdrop>=1] @then8
!exec self "cvarcopy apc#gs_object_id#electric checkdrop"
!if self [checkdrop>=1] @then9

@then7
!if self [caches_chemical>=3] @then4
!spawnobject owner human_cache_chemical #gs_object_team# neutral nearby
!exec self "inc apc#gs_object_id#chemical -1"

@then8
!if self [caches_magnetic>=3] @then5
!spawnobject owner human_cache_magnetic #gs_object_team# neutral nearby
!exec self "inc apc#gs_object_id#magnetic -1"

@then9
!if self [caches_electric>=3] @then6
!spawnobject owner human_cache_electric #gs_object_team# neutral nearby
!exec self "inc apc#gs_object_id#electric -1"

@then4
!exec self "giveresource chemical 50 #gs_object_team#"

@then5
!exec self "giveresource magnetic 50 #gs_object_team#"

@then6
!exec self "giveresource electric 50 #gs_object_team#"

@die
