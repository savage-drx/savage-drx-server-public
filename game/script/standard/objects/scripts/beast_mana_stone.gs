@spawn
!if owner healer @then0
!ifnot owner healer @then1

@then0
!givestate owner beast_mana_stone_healer -1

@then1
!givestate owner beast_mana_stone -1

@fuse
!spawngoodie self extra4 1 #gs_object_team# nearby
!spawngoodie self ammo 1 #gs_object_team# nearby
!spawngoodie self ammo 1 #gs_object_team# nearby
!exec null "play2d /sound/beast/items/mana_crystal.ogg"
!givestate owner beast_mana_stone 0
!givestate owner beast_mana_stone_healer 0
