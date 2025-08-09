@spawn
!exec self "set guardian#gs_object_id# 3"

@walking
!exec self "cvarcopy guardian#gs_object_id# selfaura"
!if self [selfaura==3] @then0
!if self [selfaura==1] @then6
!if self [selfaura==2] @then7
!if self [selfaura==0] @then8

@chasing
!exec self "cvarcopy guardian#gs_object_id# selfaura"
!if self [selfaura==3] @then0
!if self [selfaura==1] @then6
!if self [selfaura==2] @then7
!if self [selfaura==0] @then8

@idling
!exec self "cvarcopy guardian#gs_object_id# selfaura"
!if self [selfaura==3] @then0
!if self [selfaura==1] @then6
!if self [selfaura==2] @then7
!if self [selfaura==0] @then8

@hit
!test target ally
!exec self "cvarcopy guardian#gs_object_id# selfaura"
!if self [selfaura==0] @then1
!if self [selfaura==1] @then2
!if self [selfaura==2] @then3
!if self [selfaura==3] @then3

@then0
!givestate self guardian_default 2000

@then1
!exec self "set guardian#gs_object_id# 1"
!givestate self guardian_health 2000

@then2
!exec self "set guardian#gs_object_id# 2"
!givestate self guardian_stamina 2000

@then3
!exec self "set guardian#gs_object_id# 0"
!givestate self guardian_mana 2000

@then6
!givestate self guardian_health 2000

@then7
!givestate self guardian_stamina 2000

@then8
!givestate self guardian_mana 2000

@then9

@die

