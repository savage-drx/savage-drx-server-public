#---------------------------------------------------------------------------
#           Name: votes_game_end.py
#        Authors: Mohican & Groentjuh
#  Last Modified: 22/01/2011
#    Description: Server Trigger for intelligent votes management.
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

    # Check that game has ended, or a new map is loading
    if server.GetGameInfo(GAME_STATE) > 3 and not doneOnce:
        doneOnce = 1
        return 1

    return 0


#-------------------------------
def execute():

    # Set votes to game ended state
    core.CvarSetValue('sv_allowConcedeVotes', 0)
    core.CvarSetValue('sv_allowDrawVotes', 0)
    core.CvarSetValue('sv_allowElectVotes', 0)
    core.CvarSetValue('sv_allowImpeachVotes', 0)
    core.CvarSetValue('sv_allowKickVotes', 1)
    core.CvarSetValue('sv_allowMapVotes', 1)
    core.CvarSetValue('sv_allowMsgVotes', 1)
    core.CvarSetValue('sv_allowMuteVotes', 1)
    core.CvarSetValue('sv_allowNextMapVotes', 1)
    core.CvarSetValue('sv_allowPauseVotes', 0)
    core.CvarSetValue('sv_allowUnPauseVotes', 0)
    core.CvarSetValue('sv_allowRaceVotes', 0)
    core.CvarSetValue('sv_allowRefVotes', 1)
    core.CvarSetValue('sv_allowRestartVotes', 1)
    core.CvarSetValue('sv_allowShuffleVotes', 0)
    core.CvarSetValue('sv_allowTimeVotes', 0)
