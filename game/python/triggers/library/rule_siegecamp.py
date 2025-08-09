#---------------------------------------------------------------------------
#           Name: siegecamp.py
#        Authors: Milka 
#  Last Modified: 02/04/2012
#    Description: Server Trigger for preventing players from camping siege.
#          
#   Cvars:                    name:        default:        possibilites:     
#                 trigger_siegecamp               1                    0 - turns the trigger off 
#                                                                      1 - warns every active ref
#                                                                      2 - acts automatically
#  
#       trigger_siegecamp_norefcase               1                    0 - if the trigger is in warn mode and there is no ref, it does nothing
#                                                                      1 - if the trigger is in warn mode and there is no ref, it acts automatically
#  
#          trigger_siegecamp_stages               4                    Any number above 0. Represents the number of stages the trigger has.
#  
#   trigger_siegecamp_warningstages               3                    Any number above 0. Represents the number of warnings the player recieves.
#
#        trigger_siegecamp_basetime               5000                 Any number above 0. Represents the duration the player must pass away in order to change stage.
#  
#     trigger_siegecamp_warningtime               5000                 Any number above 0. Represents the time period between the warnings.
#  
#        trigger_siegecamp_distance               250                  Any number above 0. Represents the distance from spawnflags which should count as the camping area.
#
#trigger_siegecamp_distance_outpost               350                  Any number above 0. Represents the distance from outposts which should count as the camping area. (should be bigger by 100 than the one for flags)              
#
#   trigger_siegecamp_distance_base               500                  Any number above 0. Represents the distance from bases which should count as the camping area. (should be bigger by 250 than the one for flags)
#
#   Action is going to be taken after someone has continously passed trigger_siegecamp_stages*trigger_siegecamp_basetime+trigger_siegecamp_warningstages*trigger_siegecamp_warningtime time in trigger_siegecamp_distance range of an allied spawnpoint.
#   The amount of time spent outside the area negates from the time spent inside.
#---------------------------------------------------------------------------
import core
import server
import sv_defs
import sv_utils
import random


global campers
campers = [None]*MAX_CLIENTS
global refs
refs = []
global spawnpoints
spawnpoints = []
global stages
global warningstages
global basetime
global warningtime
global distance
global mode
global lastRefresh
lastRefresh = 0
global siege
siege = ['human_ballista', 'human_catapult', 'beast_summoner', 'beast_behemoth']
core.CvarSetValue('trigger_siegecamp', 1)
core.CvarSetValue('trigger_siegecamp_NoRefCase', 1)
core.CvarSetValue('trigger_siegecamp_stages', 4)
core.CvarSetValue('trigger_siegecamp_warningstages', 3)
core.CvarSetValue('trigger_siegecamp_basetime', 5000)
core.CvarSetValue('trigger_siegecamp_warningtime', 5000)
core.CvarSetValue('trigger_siegecamp_distance', 250)
core.CvarSetValue('trigger_siegecamp_distance_outpost', 350)
core.CvarSetValue('trigger_siegecamp_distance_base', 500)

class Client:
    index = -1
    stage = 0
    nextCheck = 0
    buildingDmg = 0
    
    def trigger(self):
        if self.stage == 0:
            self.stage += 1
            self.nextCheck = sv_defs.gameTime+basetime
            self.buildingDmg = server.GetClientInfo(self.index, 17)
            return
        if self.stage > 0 and self.stage <= stages:
            if self.nextCheck <= sv_defs.gameTime:
                if server.GetClientInfo(self.index, 17) > self.buildingDmg:
                    self.stage = 0
                    return
                else:    
                    self.stage += 1
                    self.nextCheck = sv_defs.gameTime+basetime
                    return
        if self.stage > stages and self.stage <= stages+warningstages:
            if self.nextCheck <= sv_defs.gameTime:
                if server.GetClientInfo(self.index, 17) > self.buildingDmg:
                    self.stage = 0
                    return
                else:
                    server.Notify(self.index, "^900You ^900have ^y%s ^900seconds ^900to ^900move ^900away ^900from ^900spawnpoints, ^900change ^900unit ^900or ^900attack ^900buildings" % ((warningstages+stages-self.stage+1)*warningtime/1000)) 
                    self.stage += 1
                    self.nextCheck = sv_defs.gameTime+warningtime
                    return
        if self.stage == stages+warningstages+1:
            if self.nextCheck <= sv_defs.gameTime:
                if server.GetClientInfo(self.index, 17) > self.buildingDmg:
                    self.stage = 0
                else:
                    self.stage += 1
      


def check():  
    if server.GetGameInfo(1) != 3:
        return 0
    global spawnpoints
    global refs
    global lastRefresh
    global campers
    if int(core.CvarGetValue('trigger_siegecamp')) != 0:
        if int(core.CvarGetValue('trigger_siegecamp_stages')) > 0:
            global stages
            stages = int(core.CvarGetValue('trigger_siegecamp_stages'))
        if int(core.CvarGetValue('trigger_siegecamp_warningstages')) > 0:
            global warningstages
            warningstages = int(core.CvarGetValue('trigger_siegecamp_warningstages'))
        if int(core.CvarGetValue('trigger_siegecamp_basetime')) > 0:
            global basetime
            basetime = int(core.CvarGetValue('trigger_siegecamp_basetime'))
        if int(core.CvarGetValue('trigger_siegecamp_warningtime')) > 0:
            global warningtime
            warningtime = int(core.CvarGetValue('trigger_siegecamp_warningtime'))
        if int(core.CvarGetValue('trigger_siegecamp_distance')) > 0:
            global distance
            distance = int(core.CvarGetValue('trigger_siegecamp_distance'))
        if int(core.CvarGetValue('trigger_siegecamp_distance_outpost')) > 0:
            global distanceOutpost
            distanceOutpost = int(core.CvarGetValue('trigger_siegecamp_distance_outpost'))
        if int(core.CvarGetValue('trigger_siegecamp_distance_base')) > 0:
            global distanceBase
            distanceBase = int(core.CvarGetValue('trigger_siegecamp_distance_base'))
        if lastRefresh+10000 <= sv_defs.gameTime or lastRefresh == 0:
            refs = []
            spawnpoints = []
            for objIndex in range(MAX_CLIENTS,sv_defs.objectList_Last):
                if not sv_defs.objectList_Active[objIndex]:
                    continue
                if not sv_defs.objectList_Type[objIndex] == OBJTYPE_BASE and not sv_defs.objectList_Type[objIndex] == OBJTYPE_OUTPOST:
                    continue
                spawnpoints.append(objIndex)
            lastRefresh = sv_defs.gameTime
        for clientIndex in range(MAX_CLIENTS):
            if server.GetClientInfo(clientIndex, 8) == 1:
                if refs.count(clientIndex) == 0:
                    refs.append(clientIndex)
            if server.GetClientInfo(clientIndex, 6) == 4 and sv_defs.objectList_Name[clientIndex] in siege and sv_defs.clientList_Health[clientIndex] > 0:
                if campers[clientIndex] is None:
                    campers[clientIndex] = Client()
                    campers[clientIndex].index = clientIndex
                client = campers[clientIndex]
                nearestSpawnpoint = find_nearest_spawnpoint(client.index, sv_utils.get_point3(client.index))
                if nearestSpawnpoint[0] == OBJTYPE_BASE and nearestSpawnpoint[1] < distanceBase:
                    client.trigger()
                    continue
                elif nearestSpawnpoint[0] == OBJTYPE_OUTPOST and nearestSpawnpoint[2] != "spawnflag" and nearestSpawnpoint[1] < distanceOutpost:
                    client.trigger()
                    continue
                elif nearestSpawnpoint[1] < distance:
                    client.trigger()
                    continue
            if campers[clientIndex] is not None:
                client = campers[clientIndex]
                if client.stage > 0:
                    if client.nextCheck <= sv_defs.gameTime:
                        client.stage -= 1
                        client.nextCheck = sv_defs.gameTime+basetime
                            
    return 1
 
def execute():
    for client in campers:
        if client is not None:
            if client.stage > stages+warningstages+1:
                if int(core.CvarGetValue('trigger_siegecamp')) == 1:
                    if refs == [] and int(core.CvarGetValue('trigger_siegecamp_NoRefCase')) == 1:
                        core.CommandExec("slay %s" % (client.index)) 
                        server.Broadcast("^g%s ^900has ^900been ^900slain ^900because ^900of ^900siege ^900camping ^900near ^900a ^900spawnpoint." %(server.GetClientInfo(client.index, 2))) 
                        server.Notify(client.index, "You have been warned.")
                        client.stage = 0
                    else:
                        if refs == []:
                            continue
                        for refIndex in refs:
                            server.Notify(refIndex, "^g%s [%s] ^900is ^900siege ^900camping." % (server.GetClientInfo(client.index, 2), client.index))
                            client.stage = 0
                        server.Notify(client.index, "^900Referees ^900have ^900been ^900warned ^900about ^900you ^900siege ^900camping.")
                elif int(core.CvarGetValue('trigger_siegecamp')) == 2:
                    core.CommandExec("slay %s" % (client.index)) 
                    server.Broadcast("^g%s ^900has ^900been ^900slain ^900because ^900of ^900siege ^900camping ^900near ^900a ^900spawnpoint." % (server.GetClientInfo(client.index, 2))) 
                    server.Notify(client.index, "You have been warned.")
                    client.stage = 0
 
def find_nearest_spawnpoint(clientIndex,targetPos):
    # Find nearest enemy Client
    nearestDist = 999999999
    nearestIndex = -1
    for objIndex in spawnpoints:
        # Check spawnpoint's team
        if not sv_defs.objectList_Team[objIndex] == sv_defs.objectList_Team[clientIndex] and not sv_defs.objectList_Name[objIndex] == 'spawnflag':
            continue

        # Check spawnpoint's health
        if sv_defs.objectList_Health[objIndex] <= 0:
            continue

        # Check spawnpoint is construted
        if sv_defs.objectList_Construct[objIndex] > 0:
            continue                    

        # Compare distanen
        objPos = sv_utils.get_point3(objIndex)
        if objPos.distance(targetPos) < nearestDist:
            nearestDist = objPos.distance(targetPos)
            nearestIndex = objIndex

    return [sv_defs.objectList_Type[nearestIndex], nearestDist, sv_defs.objectList_Name[nearestIndex]]
