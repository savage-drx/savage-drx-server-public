@spawn
!exec self "inc caches_magnetic 1"
!setstate self idle

@die
!exec self "giveresource magnetic 50 #gs_object_team#"
!exec self "inc caches_magnetic -1"
