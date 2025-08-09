#---------------------------------------------------------------------------
#           Name: votes_enable_concede.py
#        Authors: Mohican & Groentjuh
#  Last Modified: 22/01/2011
#    Description: Server Trigger for enabling concede votes after 45 min.
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
    if server.GetGameInfo(GAME_STATE) == 3 and server.GetGameInfo(GAME_TIME) > 2700000 and not doneOnce:
        doneOnce = 1
        return 1

    return 0


#-------------------------------
def execute():

    # Circulate notification to all clients
    server.Notify(-1, "^99045 ^990minutes ^990have ^990passed. ^990Concede-votes ^990have ^990been ^090ENABLED^990!")

    # Enable concede votes
    core.CvarSetValue('sv_allowConcedeVotes', 1)
    