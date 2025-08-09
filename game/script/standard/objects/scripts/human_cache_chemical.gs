@spawn
!exec self "inc caches_chemical 1"
!setstate self idle

@die
!exec self "giveresource chemical 50 #gs_object_team#"
!exec self "inc caches_chemical -1"
