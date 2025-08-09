<<< Silverback XR Unified Game Script System >>>
	   >  Mohican / XR Dev Team / 2008  <

The folder /script/standard/ contains the entire script required to run the RTSS version of Savage.
It contains the Objects/States... used in SEP/SFE, TS-SEP, and XR maps.

Description of the contents:
/configs/		Ressource Types & Races definition; Experience Tables
/objects/		Tech Tree Objects 
/states/		States conferred by Items/Buffs... (ex: adrenaline, snare)
/stringtables/	...  
/tupgrades/		Optional Team Upgrades
/voice/			Voice Chat definition

Different Object Lists (.objlist) can be loaded for the various existing Map Prefix (ex: ts_, xr_ ....)
The file /game/server_maps_lookup.cfg contains a reference table of the lists associated with each Prefix.

Full Game Conversions can be added to this reference table, like "Duel". 
In such case, the conversion folder /script/duel/ does not need to contain all the files found in /script/standard/
Files not found in the conversion folder will be loaded from the folder /script/standard/ 

