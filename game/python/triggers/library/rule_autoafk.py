#---------------------------------------------------------------------------
#           Name: autoafk.py
#        Authors: Milka 
#  Last Modified: 02/04/2012
#    Description: Server Trigger for moving afk players to spectator.
#          
#   Cvars:                  name:        default:        possibilites:     
#                 trigger_autoafk               2                    0 - turns the trigger off 
#                                                                    1 - warns every active ref if afk player is detected
#                                                                    2 - automatically moves afk players to spectator
#
#       trigger_autoafk_norefcase               1                    0 - if the trigger is in warn mode and there is no ref, it does nothing
#                                                                    1 - if the trigger is in warn mode and there is no ref, it goes auto mode
#
#   trigger_autoafk_checkinterval               30000                Any number above sv_survival_interval. Represents the delay between checks in ms.
#
#      trigger_autoafk_checkcount               6                    Any number above 0. Represents the number of checks.
#
#   Action is going to be taken after someone has been afk for trigger_autoafk_checkinterval*trigger_autoafk_checkcount time (in ms).
#---------------------------------------------------------------------------

import core
import server
import sv_defs
import sv_utils

global index
core.CvarSetValue('trigger_autoafk', 2)
core.CvarSetValue('trigger_autoafk_norefcase', 1)
core.CvarSetValue('trigger_autoafk_checkinterval', 30000)
core.CvarSetValue('trigger_autoafk_checkcount', 6)
global checkinterval
global checkcount
global clients
clients = [None]*MAX_CLIENTS
global lastRefresh
lastRefresh = 0


class Client:
    index = -1
    xp = 0
    nextCheck = 0
    position = 0
    stats = -1
    stage = 0


def check():
    if server.GetGameInfo(1) is not 3:
        return 0
    if int(core.CvarGetValue('trigger_autoafk')) is not 0:
        global lastRefresh
        global checkinterval
        global refs
        if int(core.CvarGetValue('sv_xp_survival_interval')) < int(core.CvarGetValue('trigger_autoafk_checkinterval')):
            checkinterval = int(core.CvarGetValue('trigger_autoafk_checkinterval'))
        elif int(core.CvarGetValue('sv_xp_survival_interval')) == int(core.CvarGetValue('trigger_autoafk_checkinterval')):
            checkinterval = int(core.CvarGetValue('trigger_autoafk_checkinterval'))+1000
        elif int(core.CvarGetValue('sv_xp_survival_interval')) > int(core.CvarGetValue('trigger_autoafk_checkinterval')):
            checkinterval = int(core.CvarGetValue('sv_xp_survival_interval'))+1000
        global checkcount
        if int(core.CvarGetValue('trigger_autoafk_checkcount')) > 0:
            checkcount = int(core.CvarGetValue('trigger_autoafk_checkcount'))
        global clients
        if lastRefresh+10000 <= sv_defs.gameTime or lastRefresh == 0:
            refs = []
            lastRefresh = sv_defs.gameTime
        for clientIndex in range(MAX_CLIENTS):
            if server.GetClientInfo(clientIndex, 8) == 1:
                if refs.count(clientIndex) == 0:
                    refs.append(clientIndex)
            if clients[clientIndex] is None:
                clients[clientIndex] = Client()
                client = clients[clientIndex]
                client.index = clientIndex
                client.xp = 0
                client.nextCheck = sv_defs.gameTime+checkinterval
                client.position = 0
                client.stats = -1
                client.stage = 0
            else:
                client = clients[clientIndex]
            if (server.GetClientInfo(client.index, 0) == 1 or client.stage != 0) and sv_defs.clientList_Team[client.index] != 0 and server.GetClientInfo(client.index, 6) != 3:                
                if server.GetClientInfo(client.index, 0) is 0:
                    client.xp = 0
                    client.nextCheck = 0
                    client.position = 0
                    client.stats = -1
                    client.stage = 0
                    continue
                if client.stage >= checkcount:
                    continue
                if sv_defs.gameTime >= client.nextCheck:                   
                    if client.stage == 0:
                        client.xp = server.GetClientInfo(client.index, 33)
                        client.nextCheck = sv_defs.gameTime+checkinterval
                        client.position = sv_utils.get_point3(client.index)
                        client.stats = server.GetClientInfo(client.index, 6) + server.GetClientInfo(client.index, 12)+server.GetClientInfo(client.index, 13)+server.GetClientInfo(client.index, 15)+server.GetClientInfo(client.index, 17)+server.GetClientInfo(client.index, 19)+server.GetClientInfo(client.index, 22)+server.GetClientInfo(client.index, 26)+server.GetClientInfo(client.index, 27)+server.GetClientInfo(client.index, 28)+server.GetClientInfo(client.index, 31)
                        client.stage = 1
                        continue
                    else:
                        if client.xp == server.GetClientInfo(client.index, 33):
                            client.nextCheck = sv_defs.gameTime+checkinterval
                            client.stage += 1
                            if client.stage == (checkcount/2)+1:
                                server.Notify(client.index, "^yDo ^ysomething, ^yor ^yyou ^ywill ^ybe ^ymoved ^yto ^yspectators ^ybecause ^yof ^ybeing ^yafk.")
                            continue
                        elif client.position == sv_utils.get_point3(client.index) and client.stats == server.GetClientInfo(client.index, 6) + server.GetClientInfo(client.index, 12)+server.GetClientInfo(client.index, 13)+server.GetClientInfo(client.index, 15)+server.GetClientInfo(client.index, 17)+server.GetClientInfo(client.index, 19)+server.GetClientInfo(client.index, 22)+server.GetClientInfo(client.index, 26)+server.GetClientInfo(client.index, 27)+server.GetClientInfo(client.index, 28)+server.GetClientInfo(client.index, 31):
                            client.nextCheck = sv_defs.gameTime+checkinterval
                            client.stage += 1
                            if client.stage == (checkcount/2)+1:
                                server.Notify(client.index, "^yDo ^ysomething, ^yor ^yyou ^ywill ^ybe ^ymoved ^yto ^yspectators ^ybeacuse ^yof ^ybeing ^yafk.")                                
                            continue
                        else:
                            client.stage = 0
    return 1
    
def execute():
    global clients
    for client in clients:
        if client is not None:
            if client.stage >= checkcount:
                if int(core.CvarGetValue('trigger_autoafk')) == 1:
                    if refs == []:
                        if int(core.CvarGetValue('trigger_autoafk_norefcase')) is 1:
                            server.Broadcast("^g%s ^yhas ^ybeen ^ymoved ^yto ^yspectators, ^ybecause ^yof ^ybeing ^yafk" % (server.GetClientInfo(client.index, 2)))
                            core.CommandExec("switchteam 0 %s" % (client.index))
                            client.stage = 0
                        else:
                             return
                    else:
                        for ref in refs:
                            server.Notify(ref, "^g%s ^g[%s] ^yis ^yafk, ^yyou ^yshould ^ymove ^yhim ^yto ^yspectators." % (server.GetClientInfo(client.index, 2), client.index))
                            client.stage = 0                            

                elif int(core.CvarGetValue('trigger_autoafk')) is 2:
                    server.Broadcast("^g%s ^yhas ^ybeen ^ymoved ^yto ^yspectators, ^ybecause ^yof ^ybeing ^yafk" % (server.GetClientInfo(client.index, 2)))
                    core.CommandExec("switchteam 0 %s" % (client.index))
                    client.stage = 0
