@spawn
!exec self "inc altars_fire 1"
!setstate self idle

@die
!exec self "giveresource fire 50 #gs_object_team#"
!exec self "inc altars_fire -1"
