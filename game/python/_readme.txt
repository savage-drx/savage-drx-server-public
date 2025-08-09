#---------------------------------------------------------------------------
#           Name: readme.txt
#         Author: Anthony Beaucamp (aka Mohican)
#  Last Modified: 30/07/2012
#    Description: Silverback Python Scripting Information
#---------------------------------------------------------------------------

Proudly bringing you a new and very powerful feature in XR: Python Scripting.
The standard Python library is located in /game/python/lib/
This includes: ssh, fpt, smtp, mysql, zip, IO, md5, xml...

The archive savage0.zip contains the default Savage XR Python modules.
The engine automatically calls functions from the following modules:
	- cl_events.py: client events
	- sv_events.py: server events
	- sv_bots.py: Bots AI

It is possible to customize modules by copying them into the folder /game/python/ 
You can edit them with notepad++, or any other python friendly editor.

It is also possible to compile custom script packs, with names like savage1.zip, savage2.zip...

You can use the scripting system to perform advanced operations such as uploading game stats 
on a private website with server triggers (see /triggers) and much more!
	
Note that the Bot AI has been made OpenSource in the hope that the community will help 
us improve this important aspect of gameplay on servers with low population!


Description of the Silverback APIs (more functions coming soon!):

-------------------------- CORE API ------------------------------

    // System Commands
    void    core.CommandExec(string command) - Execute command in Console.
	void	core.CommandBuffer(string command) - Execute Console Command (buffered, for use in threads).
    void    core.ConsolePrint(string text) - Print text in Console.
    float   core.CvarGetValue(string cvar) - Get float value of specified Cvar.
    void    core.CvarSetValue(string cvar,float value) - Set float value of specified Cvar.
    strng   core.CvarGetString(string cvar) - Get string value of specified Cvar.
    void    core.CvarSetString(string cvar,string value) - Set string value of specified Cvar.
    void    core.RegisterCmd(string cmd, string pyfile, string pyfunc) - Register python function as console command.

	
-------------------------- SERVER API ------------------------------
	
    // Data Fetching Commands
    misc.   server.GetGameInfo(int infoType) - Get specified info about Game (see sv_defs.py).
    lists   server.GetTeamList() - Get detailed lists of Teams (see sv_defs.py).
    misc.   server.GetClientInfo(int cliIndex,int infoType) - Get specified info about Client (see sv_defs.py).

    # returns -1 if nothing was found
    misc.   server.GetIndexFromUID(int UID) - Get client index from specified UID of the Client

    lists   server.GetClientList() - Get detailed lists of Clients (see sv_defs.py).
    lists   server.GetAccuracyList(int cliIndex) - Get detailed lists of Client's Weapon Accuracy (see sv_stats.py).
    lists   server.GetObjectList() - Get detailed lists of Objects (see sv_defs.py).
    f,f,f   server.GetObjectPos(int objIndex) - Get position of specified Object.
	f,f,f	server.GetObjectAng(int objIndex) - Get angles of specified Object.
    
    // Data Setting Commands
    void    server.SetRefStatus(int cliIndex, string status) - 'none', 'guest', 'normal', 'god'.

    // Game Scripting Commands
    void    server.Notify(int cliIndex,string message) - Send message to specified client (cliIndex -1 sends to all clients).
	void	server.Broadcast(string message) - Broadcast message to all clients.

	// example: server.Chat("chat ^clan 87151^Discord^clan 87151^> Hello, World!")  sends message from discord user
	void    server.Chat(message) - chat message from the discord client

	void	server.GameScript(int cliIndex, string command) - Execute specified GameScript command on target client.
	
	
-------------------------- CLIENT API ------------------------------

    // Data Fetching Commands
	misc.	client.GetGameInfo(int infoType) - Get info about Game.
	lists	client.GetClientList() - Get detailed lists of Clients.
	
	// Model Customization Commands 
	int		client.GetModelByType(int unitType) - Get ID of default Model for Unit Type.
	int 	client.GetModelByFile(string fileName) - Get ID of custom Model loaded from File.
	int  	client.GetSkinByFile(int modelID, string fileName) - Get ID of custom Skin loaded from File.
	int  	client.AddCustomItem(string name, int uid, int clanid, string type, string unit, string file) - Add custom item.
	

--------------------------- GUI API ------------------------------

    // General functions
    void    gui.Hide(string widget) - Hides a widget
    void    gui.Show(string widget) - Shows a hidden widget
    void    gui.Move(string widget, int x, int y) - Moves a widget (relative)
    void    gui.Param(string widget, string param, string value) - Variable manipulation
    void    gui.FadeIn(string widget, int time [, int delay]) - Fades widget in
    void    gui.FadeOut(string widget, int time [, int delay]) - Fades widget out
    void    gui.Focus(string widget) - Give focus to widget
    void    gui.EventCmd(string widget) - Execute command on event (mousedown, mouseover, mouseup, mouseout, show, hide or move)
    void    gui.Resize(string widget, int width, int height) - Resize a widget (absolute)
    void    gui.HideAll() - Hides all widgets
    void    gui.StaticDepth(boolean b) - States wether the widgets can change layer positions in the gui
    void    gui.Destroy(string widget) - Destroy widget
    void    gui.Reload() - Reload GUI"

    // Get state functions
    int     gui.IsVisible(string widget) - is widget visible?
    int     gui.IsInteractive(string widget) - is widget interactive?

	
--------------------------- BOT API ------------------------------

    // Bots Status
    int	    bot.GetStatus(int botIndex) - Get bot's status (1: load-out, 2: playing, 3: dead).
    int	    bot.GetMoney(int botIndex) - Get instant value of bot's money.
    void    bot.SetName(int botIndex,string unit) - Set bot's name.

    // Bots Requests
    bool    bot.RequestMoney(int botIndex,int amount) - Bot request money.
    bool    bot.RequestUnit(int botIndex,string unit) - Bot request unit (load-out only).
    bool    bot.RequestItem(int botIndex,string item) - Bot request item (load-out only).

    // Virtual inputs	
    void    bot.SetAngle(int botIndex,int angleIndex,float angleValue) - Set camera angle.
    void    bot.SetMotion(int botIndex,int motionIndex,int motionState) - Set motion state.
    void    bot.SetButton(int botIndex,int buttonIndex,int buttonState) - Set button state.
    void    bot.GetButton(int botIndex,int buttonIndex) - Get button state.
    void    bot.SwitchButton(int botIndex,int buttonIndex) - Switch button state.
    int     bot.SearchInvent(int botIndex,string itemName) - Search for item in inventory (-1 if not found).
    void    bot.SetInventSel(int botIndex,int itemIndex) - Set inventory selection.
    int     bot.GetInventSel(int botIndex) - Get inventory selection.
    int     bot.GetInventType(int botIndex,int itemIndex) - Get inventory item's type.
    int     bot.GetInventReady(int botIndex,int itemIndex) - Check inventory item has enough mana/ammo.
    float   bot.GetInventRange(int botIndex,int itemIndex) - Get inventory item's range.
    int     bot.GetInventCharge(int botIndex,int itemIndex) - Does inventory item need charging?

    // Navigation system
    void    bot.NavUpdate(int botIndex) - Advance Bot's Navigation.
    int     bot.NavGetType(int botIndex) - Get Navigation Target type (1: object, 2: position).
    int     bot.NavGetGoal(int botIndex) - Get current Navigation Goal.
    int     bot.NavGetState(int botIndex) - Get current Navigation State.
    int     bot.NavGetOrder(int botIndex) - Get last Navigation Order.
    int     bot.NavIsBridging(int botIndex) - Is Bot currently bridging a prop?
    void    bot.NavSetTargetObj(int botIndex,int objIndex,int goalIndex) - Set Navigation target (Object).
    void    bot.NavSetTargetPos(int botIndex,float posX,float posY,int goalIndex) - Set Navigation target (Position).
    int     bot.NavGetTargetObj(int botIndex) - Get index of Navigation target (-1 if none found).
    f,f,f   bot.NavGetTargetPos(int botIndex) - Get position of Navigation target.
    f,f,f   bot.NavGetWayPoint(int botIndex) - Get position of next WayPoint.
    int     bot.NavTargetVisible(int botIndex,float range) - Check whether Bot's Target is directly visible within the specified range.
    void    bot.NavMeshSubtract(int botIndex,int subtract) - Subtract (or not) area around Bot from Navigation Mesh.

Bot management commands (from https://www.newerth.com/wiki/index.php?title=Server_Commands):

botadd <numbots>
   Add specified amount of bots to the server.
botrem <botnum>
   Remove bot with specified client ID from server.
botspawn <botnum>
   Spawn selected bot near command centre.
botkill <botnum>
   Kills selected bot (only works if bot has already spawned).
botteam <botnum> <team>
   Switch selected bot to specified team.
botsquad <botnum> <squad>
   Switch selected bot to specified squad.
botunit <botnum> <unit>
   Bot attempts to purchase specified unit (ex: human_savage).
botgive <botnum> <wpn/item>
   Bot attempts to purchase specified weapon or item (ex: beast_snare).
botgiveback <botnum> <wpn/item>
   Bot returns specified weapon or item from inventory (ex: human_repeater).
botrequest <botnum> <id> <amount/type>
   Bot sends a request to commander.
botitem <botnum> <slot>
   Bot selects specified slot in his inventory.
botctrl <botnum> <movement/action>
   Bot performs the specified movement or action.
     Valid movements: fwd, bck, lft, rgt, jmp (and "stp" to stop all movements).
     Valid actions: att, blk, use, spr (and "clr" to stop all actions).
botaxis <botnum> <axis> <value>
   Bot rotate specified axis to match value.
     Valid axis: pit, yaw.
     Valid values: 0-360.
botclientid <botCommand> <clientId> |arguments|
   Advanced command to use if you don't know the bot's number <botnum> for the other commands (e.g. scripts, triggers).
     Example: botclientid botunit 5 human_savage
