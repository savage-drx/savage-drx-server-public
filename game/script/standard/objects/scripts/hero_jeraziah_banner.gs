@spawn
!playeffect self hero_jeraziah_banner_flame nearby
!exec self "cvarcopy gs_game_time #gs_object_id#_spawntime"
!setstate self idle

@idling
!exec self "cvarcopy #gs_object_id#_spawntime spawntime"
!exec self "cvarcopy gs_game_time gametime"
!exec self "inc gametime -#spawntime#"
!if null [gametime>=10000] @then0
!reviveradius self 180 1 7000 ally player unit
!givestateradius self 180 blessing 1000

@then0
!die self

@die
#!exec self "set banner_height 0"
