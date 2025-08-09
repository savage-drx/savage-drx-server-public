#---------------------------------------------------------------------------
#           Name: commsiegespawn.py
#        Authors: Milka 
#  Last Modified: 02/04/2012
#    Description: Server Trigger for pretending commanders to spawn siege.
#          
#   Cvars:                  name:        default:        possibilites:     
#          trigger_commsiegespawn               1                    0 - turns the trigger off 
#                                                                    1 - warns every active ref
#                                                                    2 - acts automatically
#
#trigger_commsiegespawn_norefcase               1                    0 - if the trigger is in warn mode and there is no ref, it does nothing
#                                                                    1 - if the trigger is in warn mode and there is no ref, it goes auto mode
#
#trigger_CommSiegeSpawn_fewplayers              0                   If you have less players than this number, the trigger is not gonna act.
#   Action is going to be taken if a commander spawns a siege unit.
#---------------------------------------------------------------------------

import core
import server
import sv_defs

global siege
global clients
global refs
global lastRefresh
refs = []
lastRefresh = 0
clients = [0]*MAX_CLIENTS
siege = ['human_ballista', 'human_catapult', 'beast_summoner', 'beast_behemoth']

core.CvarSetValue('trigger_CommSiegeSpawn', 1)
core.CvarSetValue('trigger_CommSiegeSpawn_NoRefCase', 1)
core.CvarSetValue('trigger_CommSiegeSpawn_fewplayers', 0)

class Team:
    commId = None
    commUid = None
    commState = 0
    commTime = 0
    def __init__(self, index):
        self.index = index
        
def define():
    global teams
    teams = []
    for i in range(int(core.CvarGetString('sv_numTeams'))):
        teams.append(Team(i))
define() 
def check():
    return 1


def execute():
    global teams
    global siege
    global clients
    global lastRefresh
    global lastRefresh
    if int(core.CvarGetValue('trigger_CommSiegeSpawn')) != 0:
        if server.GetGameInfo(1) != 3:
            return 0
        global playerAmount
        playerAmount = 0
        if lastRefresh+10000 <= sv_defs.gameTime or lastRefresh == 0:
            global refs
            refs = []
            lastRefresh = sv_defs.gameTime
        for clientIndex in range(MAX_CLIENTS):
            if server.GetClientInfo(clientIndex, 8) == 1:
                if refs.count(clientIndex) == 0:
                    refs.append(clientIndex)
            if server.GetClientInfo(clientIndex, 0) != 1:
                playerAmount += 1
        if playerAmount < int(core.CvarGetValue('trigger_CommSiegeSpawn_fewplayers')):
            return 0
        for clientIndex in range(MAX_CLIENTS):
            if server.GetClientInfo(clientIndex, 3) != 0 and server.GetClientInfo(clientIndex, 0) != clients[clientIndex]:
                clients[clientIndex] = server.GetClientInfo(clientIndex, 0)
                if clients[clientIndex] == 1:
                    for team in teams:
                        if server.GetClientInfo(clientIndex, 3) == team.commUid:
                            team.commId = clientIndex
                elif clients[clientIndex] == 0:
                    for team in teams:
                        if team.commId == clientIndex:
                            team.commId = None
        for team in teams:
            if sv_defs.teamList_Commander[team.index] != -1:
                team.commId = sv_defs.teamList_Commander[team.index]
                team.commUid = server.GetClientInfo(sv_defs.teamList_Commander[team.index], 3)
                team.commTime = server.GetClientInfo(sv_defs.teamList_Commander[team.index], 39)
            elif team.commId is not None:
                if server.GetClientInfo(team.commId, 39) > team.commTime:
                    team = Team(team.index)
                    continue
                if sv_defs.objectList_Name[team.commId] in siege and sv_defs.clientList_Team[team.commId] is team.index and sv_defs.clientList_Health[team.commId] > 0:
                    if int(core.CvarGetValue('trigger_CommSiegeSpawn')) == 1:
                        if team.commState == 0:
                            if server.GetClientInfo(team.commId, 6) == 1:
                                server.Notify(team.commId, "^900If ^900you ^900spawn ^900a ^900siege ^900unit, ^900while ^900being ^900commander, ^900you ^900will ^900be ^900punished.")
                                team.commState = 1
                                if refs == []:
                                    continue
                                for ref in refs:
                                    server.Notify(ref, "^g%s [%s] ^900is ^900about ^900to ^900spawn ^900a ^900siege ^900unit ^900while ^900being ^900the ^900commander ^900of ^900team ^g%s ^900(S)he ^900has ^900been ^900warned." % (server.GetClientInfo(team.commId, 2), team.commId, team.index))
                                continue
                        if team.commState == 1:
                            if server.GetClientInfo(team.commId, 6) == 4:
                                if refs == []:
                                    if int(core.CvarGetValue('trigger_CommSiegeSpawn_NoRefCase')) is 1:
                                        core.CommandExec("slay %s" % (team.commId))  
                                        server.Broadcast("^g%s ^900has ^900been ^900slain ^900because ^900of ^900spawning ^900siege ^900while ^900being ^900commander" % (server.GetClientInfo(team.commId, 2)))
                                        server.Notify(team.commId, "You have been warned.")
                                    team.commState = 0
                                    continue
                                for ref in refs:
                                    server.Notify(ref, "^g%s [%s] ^900has ^900spawned ^900a ^900siege ^900unit, ^900while ^900being ^900the ^900commander ^900of ^900team ^g%s ^900take ^900action!" % (server.GetClientInfo(team.commId, 2), team.commId, sv_defs.clientList_Team[team.commId]))
                                team.commState = 0
                                continue   
                    if int(core.CvarGetValue('trigger_CommSiegeSpawn')) == 2:
                        if server.GetClientInfo(team.commId, 6) == 1:
                            if team.commState == 0:
                                server.Notify(team.commId, "^900If ^900you ^900spawn ^900a ^900siege ^900unit, ^900while ^900being ^900commander, ^900you ^900will ^900be ^900punished.")
                                team.commState = 1
                                continue
                            if team.commState == 1:
                                core.CommandExec("slay %s" % (team.commId))  
                                server.Broadcast("^g%s ^900has ^900been ^900slain ^900because ^900of ^900spawning ^900siege ^900while ^900being ^900commander" % (server.GetClientInfo(team.commId, 2)))
                                server.Notify(team.commId, "You have been warned.")
                                team.commState = 0
                                continue
