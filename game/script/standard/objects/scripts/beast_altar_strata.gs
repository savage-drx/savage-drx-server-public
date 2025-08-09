@spawn
!exec self "inc altars_strata 1"
!setstate self idle

@die
!exec self "giveresource strata 50 #gs_object_team#"
!exec self "inc altars_strata -1"
