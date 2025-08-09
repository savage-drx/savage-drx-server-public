#---------------------------------------------------------------------------
#           Name: update_server.py
#        Authors: Mohican & Groentjuh
#  Last Modified: 22/01/2011
#    Description: Server Trigger for automatic Server Update
#---------------------------------------------------------------------------

# Savage API
import core
import server


#-------------------------------
def check():

    # Check that server is loading a new map (or reloading the same one!)
    if server.GetGameInfo(GAME_STATE) > 4 and core.CvarGetValue('svr_update') > 0:
        return 1

    return 0


#-------------------------------
def execute():

    # First notify all clients that update will take place
    if core.CvarGetValue('svr_update') == 1:
        server.Notify(-1, "^779(XR AutoUpdater) ^wThe server will restart to apply XR's latest updates.")
        server.Notify(-1, "^779(XR AutoUpdater) ^wPlease Wait! You will automatically reconnect if you have the latest version of XR.")
        core.CvarSetValue('svr_update', 2)

    # Then force server to shutdown
    elif core.CvarGetValue('svr_update') == 2:
        core.CommandExec('quit')
