@impact
!setscanalgo self 1
!exec self "set _range 70"
!exec self "set _duration 11000"

!givestateradius self #_range# human_potion #_duration#

!count self #_range# ally unit player
#!if found [gs_count==0] @then1
#!if found [gs_count==1] @then1
!if found [gs_count==2] @then2
!if found [gs_count==3] @then3
!if found [gs_count>=4] @then4

@then0


#@then1
#!givestateradius self #_range# human_potion #_duration#

@then2
!givestateradius self #_range# human_potion_1 #_duration#

@then3
!givestateradius self #_range# human_potion_2 #_duration#

@then4
!givestateradius self #_range# human_potion_3 #_duration#

!clearstateradius self #_range# 2
!clearstateradius self #_range# 4
!givestateradius self #_range# human_potion #_duration#
