@spawn
!exec self "inc caches_electric 1"
!setstate self idle

@die
!exec self "giveresource electric 50 #gs_object_team#"
!exec self "inc caches_electric -1"
