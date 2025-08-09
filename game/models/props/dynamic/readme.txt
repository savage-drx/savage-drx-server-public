<< XR 2.0: Bullet Physics Engine>>
>>>    Anthony Beaucamp 2008   <<<
>>>>>		aka Mohican		 <<<<<

Please place all dynamic objects in this subfolder
Important Note: 
	Dynamic Objects should have their Centre of Gravity at approximately (0,0,0).
	Failure to comply with this requirement will produce unpredictable behaviour of the object.

Physics Parameters:
	* obj_physicsDynamic: Physics engine on/off switch for this object type
	* obj_physicsMass: Mass of object when scale = 1.0 (otherwise, Mass = obj_physicsMass * scale^3)
	* obj_physicsFlammable: Can object be set on fire?

	* obj_physicsGrab: Can Players grab object?
	* obj_physicsThrow: Can Players throw object?
	* obj_physicsPush: Can Players push object?
	* obj_physicsGrabOffsetX (Y) (Z): Position from default Player Grabbing Point
	* obj_physicsGrabRotateX (Y) (Z): Rotation from default Player Grabbing Point	
