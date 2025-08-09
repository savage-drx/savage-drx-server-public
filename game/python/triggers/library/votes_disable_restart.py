#---------------------------------------------------------------------------
#           Name: votes_disable_restart.py
#        Authors: Mohican & Groentjuh
#  Last Modified: 22/01/2011
#    Description: Server Trigger for disabling restart votes after 5 min.
#---------------------------------------------------------------------------

# Savage API
import core
import server

# Trigger Variables
global doneOnce
doneOnce = 0


#-------------------------------
def check():
    
    global doneOnce

    # Check that server is in play mode, and sufficient time has ellapsed
    if server.GetGameInfo(GAME_STATE) == 3 and server.GetGameInfo(GAME_TIME) > 300000 and not doneOnce:
        doneOnce = 1
        return 1

    return 0


#-------------------------------
def execute():

    # Circulate notification to all clients
    server.Notify(-1, "^9905 ^990minutes ^990have ^990passed. ^990Restart-votes ^990have ^990been ^900DISABLED^990!")

    # Disable Restart Votes
    core.CvarSetValue('sv_allowRestartVotes', 0)
