@use
!exec self "set aoeRadius 130"
!exec self "set aoeDamage 200"
!attach owner

@attach
!setstate self idle
#!delay self 500

@idling
!die self

@die
#execute effects
!damageradius self #aoeRadius# #aoeDamage# enemy neutral unit player npc item
!givestateradius self #aoeRadius# debuff_0_human 1000
!givestateradius self #aoeRadius# debuff_6 1000
!givestateradius self #aoeRadius# debuff_8 1000

