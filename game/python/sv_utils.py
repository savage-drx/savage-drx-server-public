# ---------------------------------------------------------------------------
#           Name: sv_utils.py
#         Author: Anthony Beaucamp (aka Mohican), CrashDay
#    Description: Useful Routines for Finding Objects
#          State: Modified
# ---------------------------------------------------------------------------

import server
import core
import sv_defs
import sh_logger as log
from euclid import *


# -------------------------------
def getIndexFromName(name):
    for team in range(0, sv_defs.teamList_Last):
        for index in range(0, MAX_CLIENTS):
            # Ignore inactive Client Slots and Bots
            if not server.GetClientInfo(index, INFO_ACTIVE) or sv_defs.clientList_Bot[index]:
                continue

                # Check Player's Team
            if sv_defs.clientList_Team[index] != team:
                continue

            # Collect Information
            tempname = server.GetClientInfo(index, INFO_NAME)
            if tempname.lower().find(name.lower()) != -1:
                return index


# -------------------------------
def getIndexFromFullName(name):
    for team in range(0, sv_defs.teamList_Last):
        for index in range(0, MAX_CLIENTS):
            # Ignore inactive Client Slots and Bots
            if not server.GetClientInfo(index, INFO_ACTIVE) or sv_defs.clientList_Bot[index]:
                continue

                # Check Player's Team
            if sv_defs.clientList_Team[index] != team:
                continue

            # Collect Information
            temp_name = server.GetClientInfo(index, INFO_NAME)
            if temp_name.lower() == name.lower():
                return index

    # if nothing was found
    return None


# -------------------------------
def getIndicesFromTeam(team):
    indices = []
    for index in range(0, MAX_CLIENTS):
        # Ignore inactive Client Slots and Bots
        if not server.GetClientInfo(index, INFO_ACTIVE) or sv_defs.clientList_Bot[index]:
            continue

            # Check Player's Team
        if str(sv_defs.clientList_Team[index]) == team:
            indices.append(str(index))
    return indices


# -------------------------------
def getActiveIndices():
    indices = []
    for team in range(0, sv_defs.teamList_Last):
        for index in range(0, MAX_CLIENTS):
            # Ignore inactive Client Slots and Bots
            if not server.GetClientInfo(index, INFO_ACTIVE) or sv_defs.clientList_Bot[index]:
                continue

                # Check Player's Team
            if sv_defs.clientList_Team[index] != team:
                continue

            # Collect Information
            indices.append(str(index))
    return indices


# -------------------------------
def is_client(objIndex):
    # Test if object is any type of building
    if sv_defs.objectList_Type[objIndex] == OBJTYPE_CLIENT:
        return 1
    else:
        return 0


# -------------------------------
def is_building(objIndex):
    # Test if object is any type of building
    if OBJTYPE_BASE <= sv_defs.objectList_Type[objIndex] <= OBJTYPE_BUILDING:
        return 1
    else:
        return 0


# -------------------------------
def get_point3(objIndex):
    # Return Object position as Point3
    [x, y, z] = server.GetObjectPos(objIndex)
    return Point3(x, y, z)


# -------------------------------
def find_nearest_enemy(botIndex, maxDist):
    # Find nearest enemy Client
    botPos = get_point3(botIndex)
    nearestDist = maxDist
    nearestIndex = -1
    for objIndex in range(0, MAX_CLIENTS):
        # Only active clients
        if not sv_defs.objectList_Active[objIndex]:
            continue

        # Check client's team
        if sv_defs.objectList_Team[objIndex] == sv_defs.objectList_Team[botIndex]:
            continue

        # Check object's team (don't want no spectator)
        if sv_defs.objectList_Team[objIndex] == 0:
            continue

            # Check client's health
        if sv_defs.objectList_Health[objIndex] <= 0:
            continue

        # Check client is not Commanding
        if objIndex == sv_defs.teamList_Commander[sv_defs.objectList_Team[objIndex]]:
            continue

        # Compare distance to current nearest
        objPos = get_point3(objIndex)
        if objPos.distance(botPos) < nearestDist:
            nearestDist = objPos.distance(botPos)
            nearestIndex = objIndex

    return nearestIndex


# -------------------------------
def find_nearest_enemy_object(botIndex, maxDist):
    # Find nearest enemy non-Client
    botPos = get_point3(botIndex)
    nearestDist = maxDist
    nearestIndex = -1
    for objIndex in range(MAX_CLIENTS, sv_defs.objectList_Last):
        # Only active Objects
        if not sv_defs.objectList_Active[objIndex]:
            continue

        # Check object's team
        if sv_defs.objectList_Team[objIndex] == sv_defs.objectList_Team[botIndex]:
            continue

        # Check object's team (don't need no neutral creeps)
        if sv_defs.objectList_Team[objIndex] == 0:
            continue

        # Check object's health
        if sv_defs.objectList_Health[objIndex] <= 0:
            continue

        # Compare distance to current nearest
        objPos = get_point3(objIndex)
        if objPos.distance(botPos) < nearestDist:
            nearestDist = objPos.distance(botPos)
            nearestIndex = objIndex

    return nearestIndex


# -------------------------------
def find_nearest_construct(botIndex, maxDist):
    # Find nearest ally building under construction
    botPos = get_point3(botIndex)
    nearestDist = maxDist
    nearestIndex = -1
    for objIndex in range(MAX_CLIENTS, sv_defs.objectList_Last):
        # Only active Objects
        if not sv_defs.objectList_Active[objIndex]:
            continue

        # Check object's team
        if not sv_defs.objectList_Team[objIndex] == sv_defs.objectList_Team[botIndex]:
            continue

        # Check object's type
        if sv_defs.objectList_Type[objIndex] < OBJTYPE_BASE or sv_defs.objectList_Type[objIndex] > OBJTYPE_BUILDING:
            continue

        # Check building is under contruction
        if not sv_defs.objectList_Construct[objIndex]:
            continue

        # Compare distance to current nearest
        objPos = get_point3(objIndex)
        if objPos.distance(botPos) < nearestDist:
            nearestDist = objPos.distance(botPos)
            nearestIndex = objIndex

    return nearestIndex


# -------------------------------
def find_nearest_repair(botIndex, maxDist):
    # Find nearest ally building not at full health (=needs repairing)
    botPos = get_point3(botIndex)
    nearestDist = maxDist
    nearestIndex = -1
    for objIndex in range(MAX_CLIENTS, sv_defs.objectList_Last):
        # Only active Objects
        if not sv_defs.objectList_Active[objIndex]:
            continue

        # Check object's team
        if not sv_defs.objectList_Team[objIndex] == sv_defs.objectList_Team[botIndex]:
            continue

        # Check object's type
        if sv_defs.objectList_Type[objIndex] < OBJTYPE_BASE or sv_defs.objectList_Type[objIndex] > OBJTYPE_BUILDING:
            continue

        # Check object's health
        if not sv_defs.objectList_Health[objIndex] < sv_defs.objectList_MaxHealth[objIndex]:
            continue

        # Compare distance to current nearest
        objPos = get_point3(objIndex)
        if objPos.distance(botPos) < nearestDist:
            nearestDist = objPos.distance(botPos)
            nearestIndex = objIndex

    return nearestIndex


# -------------------------------
def find_nearest_mine(botIndex, mineType):
    # Find nearest mine
    botPos = get_point3(botIndex)
    nearestDist = 999999999
    nearestIndex = -1
    for objIndex in range(MAX_CLIENTS, sv_defs.objectList_Last):
        # Only active Objects
        if not sv_defs.objectList_Active[objIndex]:
            continue

        # Check object's type (Mine!)
        if not sv_defs.objectList_Type[objIndex] == OBJTYPE_MINE:
            continue

            # Check mine's resource type
        if not mineType == MINETYPE_ANY:
            if mineType == MINETYPE_GOLD:
                if not sv_defs.objectList_Name[objIndex] == 'gold_mine':
                    continue
            elif mineType == MINETYPE_STONE:
                if not sv_defs.objectList_Name[objIndex] == 'redstone_mine':
                    continue

                    # TODO: Add check if mine has resources left?

        # Compare distance to current nearest
        objPos = get_point3(objIndex)
        if objPos.distance(botPos) < nearestDist:
            nearestDist = objPos.distance(botPos)
            nearestIndex = objIndex

    return nearestIndex


# -------------------------------
def find_nearest_critter(botIndex, maxDist, objDibber):
    # Find nearest valid goodie
    botPos = get_point3(botIndex)
    nearestDist = maxDist
    nearestIndex = -1
    for objIndex in range(MAX_CLIENTS, sv_defs.objectList_Last):
        # Only active Objects
        if not sv_defs.objectList_Active[objIndex]:
            continue

        # Is object a valid critter? (only small fry allowed!)
        if not sv_defs.objectList_Name[objIndex] == 'npc_monkit' and not sv_defs.objectList_Name[
            objIndex] == 'npc_oschore' and not sv_defs.objectList_Name[objIndex] == 'npc_macaque':
            continue

        # Check critter's health
        if sv_defs.objectList_Health[objIndex] <= 0:
            continue

        # Check dibs status
        if not objDibber[objIndex] == -1 and not objDibber[objIndex] == botIndex:
            continue

        # Compare distance to current nearest
        objPos = get_point3(objIndex)
        if objPos.distance(botPos) < nearestDist:
            nearestDist = objPos.distance(botPos)
            nearestIndex = objIndex

    return nearestIndex


# -------------------------------
def find_nearest_goodie(botIndex, maxDist, objDibber):
    # Find nearest valid goodie
    botPos = get_point3(botIndex)
    nearestDist = maxDist
    nearestIndex = -1
    for objIndex in range(MAX_CLIENTS, sv_defs.objectList_Last):
        # Only active Objects
        if not sv_defs.objectList_Active[objIndex]:
            continue

        # Is object a goodie?
        if not sv_defs.objectList_Name[
            objIndex] == 'goodiebag':  # and not sv_defs.objectList_Name[objIndex] == 'ammo_box' and not sv_defs.objectList_Name[objIndex] == 'mana_stone':
            continue  # TODO: prevent bot from stopping, when it cant pick-up goodies like ammo

        # Check goodie's team
        if not sv_defs.objectList_Team[objIndex] == 0 and not sv_defs.objectList_Team[objIndex] == \
                sv_defs.objectList_Team[botIndex]:
            continue

        # Check dibs status
        if not objDibber[objIndex] == -1 and not objDibber[objIndex] == botIndex:
            continue

        # Compare distance to current nearest
        objPos = get_point3(objIndex)
        if objPos.distance(botPos) < nearestDist:
            nearestDist = objPos.distance(botPos)
            nearestIndex = objIndex

    return nearestIndex


# -------------------------------
def find_best_spawnpoint(botIndex, targetPos):
    # Find nearest enemy Client
    nearestDist = 999999999
    nearestIndex = -1
    for objIndex in range(MAX_CLIENTS, sv_defs.objectList_Last):
        # Only active objects
        if not sv_defs.objectList_Active[objIndex]:
            continue

        # Is spawnpoint?
        if not sv_defs.objectList_Type[objIndex] == OBJTYPE_BASE and not sv_defs.objectList_Type[
            objIndex] == OBJTYPE_OUTPOST:
            continue

        # Reject spawnflags (to avoid getting stuck!)
        if sv_defs.objectList_Name[objIndex] == 'spawnflag':
            continue

        # Check spawnpoint's team
        if not sv_defs.objectList_Team[objIndex] == sv_defs.objectList_Team[botIndex]:
            continue

        # Check spawnpoint's health
        if sv_defs.objectList_Health[objIndex] <= 0:
            continue

        # Check spawnpoint is construted, 0 means constructed
        if sv_defs.objectList_Construct[objIndex] > 0:
            continue

        # Compare distance to current nearest
        objPos = get_point3(objIndex)
        if objPos.distance(targetPos) < nearestDist:
            nearestDist = objPos.distance(targetPos)
            nearestIndex = objIndex

    return nearestIndex


def get_teams():
    # HvB size should be 2 (excluding specs)
    teams = []
    for i in range(int(core.CvarGetString('sv_numTeams'))):
        if i is not 0:
            teams.append(i)
    return teams


def get_comm_indices():
    # define teams
    teams = get_teams()
    # define commanders
    comm_indices = set()
    for team in teams:
        if sv_defs.teamList_Commander[team] != -1:
            comm_indices.add(sv_defs.teamList_Commander[team])
    return comm_indices


def is_commander(client_index):
    comm_indices = get_comm_indices()
    return client_index in comm_indices


def are_commanders_elected():
    comm_indices = get_comm_indices()
    teams = get_teams()
    # check if there are enough commanders
    log.info(f'Number of commanders: {len(comm_indices)}, number of teams: {len(teams)}')
    return len(comm_indices) == len(teams)


def are_bases_damaged(allowable_hp_percentage):
    teams = get_teams()
    bases = {}
    for team in teams:
        base_idx = int(sv_defs.teamList_Base[team])
        bases[base_idx] = sv_defs.objectList_Name[base_idx]
    for base_idx, base_name in bases.items():
        current_hp = int(sv_defs.objectList_Health[base_idx])
        max_hp = int(sv_defs.objectList_MaxHealth[base_idx])
        current_hp_percentage = current_hp * 100 / max_hp
        if current_hp_percentage < allowable_hp_percentage:
            return {'base_name': base_name, 'hp_percentage': current_hp_percentage}
    return {}


def get_game_time_in_seconds():
    return sv_defs.gameTime / 1000


class PlayerStatus:
    STATUS_LOBBY = 0
    STATUS_UNIT_SELECT = 1
    STATUS_SPAWNPOINT_SELECT = 2
    STATUS_COMMANDER = 3
    STATUS_PLAYER = 4
    STATUS_SPECTATE = 5
    STATUS_ENDGAME = 6
    STATUS_SHOPPING = 7


class OnlineState:
    def __init__(self):
        self.map_name = core.CvarGetString('world_name')
        self.teams = {}
        self.online = 0
        self.active_players = 0
        self.active_indices_without_commanders = []
        self.bots = []
        self.__init_teams()

    def __init_teams(self):
        for i in range(int(core.CvarGetString('sv_numTeams'))):
            self.teams[i] = OnlineState.Team(i)
        # fill teams with players
        for client_index in range(MAX_CLIENTS):
            # init bots
            if sv_defs.clientList_Bot[client_index]:
                team_id = sv_defs.objectList_Team[client_index]
                self.teams[team_id].bots[client_index] = server.GetClientInfo(client_index, INFO_NAME)
                self.bots.append(client_index)
            # Ignore inactive Client Slots and Bots
            if server.GetClientInfo(client_index, INFO_ACTIVE) and not sv_defs.clientList_Bot[client_index]:
                team_id = sv_defs.objectList_Team[client_index]
                self.online = self.online + 1
                # add commander
                if client_index == sv_defs.teamList_Commander[team_id]:
                    self.teams[team_id].commander["client_index"] = client_index
                    self.teams[team_id].commander["name"] = server.GetClientInfo(client_index, INFO_NAME)
                else:
                    # add player
                    self.teams[team_id].players[client_index] = server.GetClientInfo(client_index, INFO_NAME)
                    if team_id != 0:
                        self.active_players = self.active_players + 1
                        self.active_indices_without_commanders.append(client_index)

    class Team:
        def __init__(self, team_id):
            self.team_id = team_id
            self.team_name = ""
            self.race = sv_defs.teamList_RaceName[team_id]
            self.players = {}
            self.bots = {}
            self.commander = {"name": None}

            if self.team_id == 0:
                self.team_name = "Spectators"
            else:
                self.team_name = "Team %s" % self.team_id

        def __str__(self):
            return "Team name: %s, id: %s, race: %s, commander: %s, players: %s" % \
                   (self.team_name, self.team_id, self.race, self.commander, self.players)

    def __str__(self):
        return "Online: world: %s, teams: %s, total: %s, active: %s" % \
               (self.map_name, len(self.teams) - 1, self.online, self.active_players)


class ClientState:
    def __init__(self, client_index):
        self.client_index = client_index
        self.name = server.GetClientInfo(client_index, INFO_NAME)
        self.team = server.GetClientInfo(client_index, INFO_TEAM)

        self.xp = 0
        self.position = None

        self.blocks = 0
        self.jumps = 0
        self.npc_dmg = 0
        self.peon_dmg = 0
        self.building_dmg = 0
        self.client_dmg = 0
        self.mine = 0
        self.heal = 0
        self.build = 0
        self.orders = 0

        self.update_state()

    def update_state(self):
        self.xp = server.GetClientInfo(self.client_index, STAT_EXPERIENCE)
        self.position = get_point3(self.client_index)
        self.blocks = server.GetClientInfo(self.client_index, STAT_BLOCKS)
        self.jumps = server.GetClientInfo(self.client_index, STAT_JUMPS)
        self.npc_dmg = server.GetClientInfo(self.client_index, STAT_NPCDMG)
        self.peon_dmg = server.GetClientInfo(self.client_index, STAT_PEONDMG)
        self.building_dmg = server.GetClientInfo(self.client_index, STAT_BUILDDMG)
        self.client_dmg = server.GetClientInfo(self.client_index, STAT_CLIENTDMG)
        self.mine = server.GetClientInfo(self.client_index, STAT_MINE)
        self.heal = server.GetClientInfo(self.client_index, STAT_HEAL)
        self.build = server.GetClientInfo(self.client_index, STAT_BUILD)
        self.orders = server.GetClientInfo(self.client_index, STAT_ORDERGIVE)

    def is_afk(self, other):
        if self.position != other.position:
            return False
        return self.__are_stats_equal(other)

    def __are_stats_equal(self, other):
        return self.blocks == other.blocks and \
               self.jumps == other.jumps and \
               self.npc_dmg == other.npc_dmg and \
               self.peon_dmg == other.peon_dmg and \
               self.building_dmg == other.building_dmg and \
               self.client_dmg == other.client_dmg and \
               self.mine == other.mine and \
               self.heal == other.heal and \
               self.build == other.build and \
               self.orders == other.orders

    def switch_to_specs(self):
        core.CommandExec("switchteam 0 %s" % self.client_index)
        log.info("%s is AFK" % self.name)
        server.Broadcast("^g%s ^yhas ^ybeen ^ymoved ^yto ^yspectators, ^ybecause ^yof ^ybeing ^900AFK" % self.name)

    def __str__(self):
        return "Client: name: %s, xp: %s, position: %s" % (self.name, self.xp, self.position)
