@spawn
!exec self "inc altars_entropy 1"
!setstate self idle

@die
!exec self "giveresource entropy 150 #gs_object_team#"
!exec self "inc altars_entropy -1"
