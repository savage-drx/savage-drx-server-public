@spawn
!exec self "cvarcopy gs_game_time #gs_object_id#_spawntime"
!setstate self idle

@idling
#lifespan timer check
!exec self "cvarcopy #gs_object_id#_spawntime spawntime"
!exec self "cvarcopy gs_game_time gametime"
!exec self "inc gametime -#spawntime#"
!if null [gametime>=2000] @then0

# search flags relative to target
!exec self "cvarcopy ophelia_#gs_object_team# ophelia_id"
!search self 120 ally player unit 1st
!if found [gs_object_id!=ophelia_id] @then5
!search self 120 ally player unit 2nd
!if found [gs_object_id!=ophelia_id] @then5
!search self 120 ally player unit 3rd
!if found [gs_object_id!=ophelia_id] @then5
!search self 120 ally player unit 4th
!if found [gs_object_id!=ophelia_id] @then5

@then0
!targetIndex self #ophelia_id#
!if found [gs_object_healthpercent>0] @then9
!die self

@then9                	
!playeffect found hero_ophelia_teleport_vanish nearby
!teleport found home


@then5
!if found [gs_object_id>=0] @then8

@then8
!playeffect found hero_ophelia_teleport_vanish nearby
!teleport found home

@die
