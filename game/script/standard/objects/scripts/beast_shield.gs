@impact
!if target [gs_object_id>=0] @then0

@then0
!test target ally
!givestate target beast_shield 400
!givestate owner beast_shield_lock 400
!exec owner client "play2d /sound/effects/magic_shield_2.wav"
