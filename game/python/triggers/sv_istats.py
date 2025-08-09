# ---------------------------------------------------------------------------
#           Name: sv_stats.py
#    Description: Server trigger to manage the awards in the end of the game
# ---------------------------------------------------------------------------

# Savage API
import core
import server

# External modules
import copy
import re
import time
import sh_custom_utils
import sv_defs


# Don't save players with UID = 0 (0 is for unauthorized clients)
class Player(object):
    # Robot icon
    default_clan_id = 86846
    default_clan_tag = '^gBOT'

    def __init__(self, uid):
        self.uid = uid
        self.clan_id = self.default_clan_id
        self.clan_tag = self.default_clan_tag
        self.last_used_name = ""
        self.accuracy_stats = AccuracyStats(self.uid)
        self.awards = Awards(self.uid)
        # These attributes should not be sent through the json
        self.kills = 0
        self.deaths = 0
        self.killstreak = 0
        self.npc_killed = 0
        self.mvp = 0
        # frags per minute
        self.fpm = 0
        # 0 means no award; 1 - got award
        self.first_frag = 0
        # 0 means no award; 1 - got award
        self.last_frag = 0
        self.jumps = 0

    def json_repr(self):
        return dict(uid=self.uid, clanId=self.clan_id, lastUsedName=self.last_used_name,
                    accuracyStats=self.accuracy_stats,
                    awards=self.awards)

    def __str__(self):
        return "Player: [UID: %s], [CLAN_ID: %s], [NAME: %s]" % (self.uid, self.clan_id, self.last_used_name)


class AccuracyStats(object):
    def __init__(self, uid):
        self.uid = uid
        self.desc = 'Coil Rifle'

        self.last_shots = 0
        self.last_hits = 0
        self.last_frags = 0
        self.accuracy_percent = 0

        self.accumulated_shots = 0
        self.accumulated_hits = 0
        self.accumulated_frags = 0
        self.accumulated_percent = 0

        self.timestamp = 0

    def json_repr(self):
        return dict(uid=self.uid, desc=self.desc, lastShots=self.last_shots, lastFrags=self.last_frags,
                    lastHits=self.last_hits)

    def __str__(self):
        return "Coil Rifle: [UID: %s], [ACCURACY: %s], [SHOTS: %s], [FRAGS: %s], [HITS: %s]" % (
            self.uid, self.accuracy_percent, self.last_shots, self.last_frags, self.last_hits)


class MapAwards:
    def __init__(self):
        template = {"uid": 0, "clan_id": Player.default_clan_id, "name": "", "value": 0, "full_nick": "",
                    "clan_tag": Player.default_clan_tag}
        # most kills - deaths
        self.mvp = copy.copy(template)
        self.mvp["award_text"] = '%s (kills - deaths)'
        # most kills
        self.sadist = copy.copy(template)
        self.sadist["award_text"] = '%s Kills'
        # most kills in a row
        self.survivor = copy.copy(template)
        self.survivor["award_text"] = '%s Kills in a row'
        # most deaths
        self.ripper = copy.copy(template)
        self.ripper["award_text"] = '%s Deaths'
        # most npcs killed
        self.phoe = copy.copy(template)
        self.phoe["award_text"] = '%s Npc kills'
        # most accurate
        self.aimbot = copy.copy(template)
        self.aimbot["award_text"] = '%s%% Accuracy'
        # first frag
        self.first_frag = copy.copy(template)
        self.first_frag["award_text"] = 'First kill'
        # last frag that made your team win
        self.last_frag = copy.copy(template)
        self.last_frag["award_text"] = 'Last kill'
        # 0 deaths
        self.camper = copy.copy(template)
        self.camper["award_text"] = '%s Deaths'
        # fpm (frags per minute): game time / frags
        self.fpm = copy.copy(template)
        self.fpm["award_text"] = '%s Kills per minute'
        # bunny
        self.bunny = copy.copy(template)
        self.bunny["award_text"] = '%s Jumps'

    def update_awards_text(self):
        default_value = 0
        self.mvp["award_text"] %= self.mvp["value"] if self.mvp["value"] > 0 else default_value
        self.sadist["award_text"] %= self.sadist["value"] if self.sadist["value"] > 0 else default_value
        self.survivor["award_text"] %= self.survivor["value"] if self.survivor["value"] > 0 else default_value
        self.ripper["award_text"] %= self.ripper["value"] if self.ripper["value"] > 0 else default_value
        self.phoe["award_text"] %= self.phoe["value"] if self.phoe["value"] > 0 else default_value
        self.aimbot["award_text"] %= self.aimbot["value"] if self.aimbot["value"] > 0 else default_value
        self.camper["award_text"] %= self.camper["value"] if self.camper["value"] > 0 else default_value
        self.fpm["award_text"] %= self.fpm["value"] if self.fpm["value"] > 0 else default_value
        self.bunny["award_text"] %= self.bunny["value"] if self.bunny["value"] > 0 else default_value

    # Hardcoded structure
    def get_transmit_value(self):
        self.update_awards_text()
        delimiter = ','
        result = \
            str(self.mvp["award_text"]) + delimiter + str(self.mvp["full_nick"]) + delimiter + \
            str(self.sadist["award_text"]) + delimiter + str(self.sadist["full_nick"]) + delimiter + \
            str(self.survivor["award_text"]) + delimiter + str(self.survivor["full_nick"]) + delimiter + \
            str(self.ripper["award_text"]) + delimiter + str(self.ripper["full_nick"]) + delimiter + \
            str(self.phoe["award_text"]) + delimiter + str(self.phoe["full_nick"]) + delimiter + \
            str(self.aimbot["award_text"]) + delimiter + str(self.aimbot["full_nick"]) + delimiter + \
            str(self.first_frag["award_text"]) + delimiter + str(self.first_frag["full_nick"]) + delimiter + \
            str(self.last_frag["award_text"]) + delimiter + str(self.last_frag["full_nick"]) + delimiter + \
            str(self.camper["award_text"]) + delimiter + str(self.camper["full_nick"]) + delimiter + \
            str(self.fpm["award_text"]) + delimiter + str(self.fpm["full_nick"]) + delimiter + \
            str(self.bunny["award_text"]) + delimiter + str(self.bunny["full_nick"]) + delimiter
        return result


class Awards(object):
    def __init__(self, uid):
        self.uid = uid
        self.mvp = 0
        self.sadist = 0
        self.survivor = 0
        self.ripper = 0
        self.phoe = 0
        self.aimbot = 0

        self.accumulated_mvp = 0
        self.accumulated_sadist = 0
        self.accumulated_survivor = 0
        self.accumulated_ripper = 0
        self.accumulated_phoe = 0
        self.accumulated_aimbot = 0

    def json_repr(self):
        return dict(uid=self.uid, mvp=self.mvp, sadist=self.sadist, survivor=self.survivor,
                    ripper=self.ripper, phoe=self.phoe, aimbot=self.aimbot)

    def has_awards(self):
        return bool(self.accumulated_mvp) or bool(self.accumulated_sadist) or bool(self.accumulated_survivor) \
               or bool(self.accumulated_ripper) or bool(self.accumulated_phoe) or bool(self.accumulated_aimbot)

    def __str__(self):
        return "Awards : [UID: %s], [AIMBOT: %s], [MVP: %s], [SADIST: %s], [SURVIVOR: %s], [RIPPER: %s], [PHOE: %s]" \
               % (self.uid, self.accumulated_aimbot, self.accumulated_mvp, self.accumulated_sadist,
                  self.accumulated_survivor, self.accumulated_ripper, self.accumulated_phoe)


class MapStats(object):
    def __init__(self):
        self.map_name = 'default_map_name'
        self.red_score = 0
        self.blue_score = 0
        self.winner = 'draw'

    def json_repr(self):
        return dict(mapName=self.map_name, redScore=self.red_score, blueScore=self.blue_score, winner=self.winner)

    def __str__(self):
        return "MapStats: [MAP_NAME: %s], [RED: %s], [BLUE: %s], [WINNER: %s]" % (self.map_name, self.red_score,
                                                                                  self.blue_score, self.winner)


class _Context:
    GAME_MOD = core.CvarGetString('sv_map_gametype')
    GAME_END_FLAG = False
    PLAYERS = list()
    MAP_STATS = MapStats()
    # Will replace all symbols from the name that are not: '0-9A-Za-z-_() '
    REGEXP_FOR_NAME = '[^0-9^A-Z^a-z^\-^_^(^) ]'


# Is called during every server frame
def check():
    try:
        # If game state == 4 ('Game Ended') -> save stats.
        if server.GetGameInfo(GAME_STATE) == 4 and not _Context.GAME_END_FLAG:
            _Context.GAME_END_FLAG = True
            calculate_players_and_awards()
        return 0
    except:
        sh_custom_utils.get_and_log_exception_info()


# Is called when check() returns 1
# Is not used in the current script
def execute():
    pass


def calculate_players_and_awards():
    calculate_players_stats()
    calculate_map_stats()
    map_awards = calculate_map_awards()
    bind_awards_to_players(map_awards)
    update_clients_vars(map_awards)


# Gets the accuracy for the selected player by client_index
def get_accuracy(client_index):
    client_index = int(client_index)
    # new object that will be returned
    acs = AccuracyStats(client_index)
    try:
        [accuracyList_weapon, accuracyList_shots, accuracyList_kills, accuracyList_deaths,
         accuracyList_hits, accuracyList_siegehits, accuracyList_damage, accuracyList_last] \
            = server.GetAccuracyList(client_index)

        for weapon in range(0, accuracyList_last):
            if str(accuracyList_weapon[weapon]) == 'Coil Rifle':
                acs.uid = int(server.GetClientInfo(client_index, INFO_UID))
                acs.last_shots = int(accuracyList_shots[weapon])
                acs.last_frags = int(accuracyList_kills[weapon])
                acs.last_hits = int(accuracyList_hits[weapon])
                if acs.last_shots == 0:
                    acs.accuracy_percent = 0
                else:
                    acs.accuracy_percent = acs.last_hits * 100 / acs.last_shots
                acs.timestamp = int(round(time.time() * 1000))
    except:
        sh_custom_utils.get_and_log_exception_info()
    return acs


# Gets accuracy for all active players
def calculate_players_stats():
    first_frag_index = int(core.CvarGetValue('gs_first_frag_guid'))
    last_frag_index = int(core.CvarGetValue('gs_last_frag_guid'))
    try:
        for client_index in range(0, sv_defs.objectList_Last):
            if sv_defs.objectList_Active[client_index]:
                uid = int(server.GetClientInfo(client_index, INFO_UID))
                if uid > 0:
                    player = Player(uid)
                    clan_id = int(server.GetClientInfo(client_index, INFO_CLANID))
                    player.clan_id = player.default_clan_id if clan_id == 0 else clan_id
                    clan_tag = server.GetClientInfo(client_index, INFO_CLANABBREV)
                    player.clan_tag = player.default_clan_tag if not clan_tag else clan_tag
                    player.last_used_name = re.sub(_Context.REGEXP_FOR_NAME, '',
                                                   server.GetClientInfo(client_index, INFO_NAME))
                    player.kills = int(server.GetClientInfo(client_index, STAT_KILLS))
                    player.deaths = int(server.GetClientInfo(client_index, STAT_DEATHS))
                    player.killstreak = int(server.GetClientInfo(client_index, STAT_KILLSTREAK))
                    player.jumps = int(server.GetClientInfo(client_index, STAT_JUMPS))
                    player.npc_killed = int(server.GetClientInfo(client_index, STAT_NPCKILL))
                    player.mvp = player.kills - player.deaths
                    if player.kills > 0:
                        player.fpm = round(player.kills
                                           / (float(server.GetClientInfo(client_index, STAT_ONTEAMTIME)) / 1000)
                                           * 60, 1)
                    if client_index == first_frag_index:
                        player.first_frag = 1
                    if client_index == last_frag_index:
                        player.last_frag = 1
                    player.accuracy_stats = get_accuracy(client_index)
                    _Context.PLAYERS.append(player)
    except:
        sh_custom_utils.get_and_log_exception_info()


# Fill MapStats for save
def calculate_map_stats():
    _Context.MAP_STATS = MapStats()
    _Context.MAP_STATS.map_name = str(core.CvarGetString('world_name'))
    _Context.MAP_STATS.red_score = int(core.CvarGetValue('gs_transmit1'))
    _Context.MAP_STATS.blue_score = int(core.CvarGetValue('gs_transmit2'))
    if _Context.MAP_STATS.red_score > _Context.MAP_STATS.blue_score:
        _Context.MAP_STATS.winner = 'red'
    elif _Context.MAP_STATS.red_score < _Context.MAP_STATS.blue_score:
        _Context.MAP_STATS.winner = 'blue'


# Calculates awards for active players
def calculate_map_awards():
    map_awards = MapAwards()
    frag_limit = int(core.CvarGetValue('py_instagib_fragLimit'))
    red_score = int(core.CvarGetValue('gs_transmit1'))
    blue_score = int(core.CvarGetValue('gs_transmit2'))

    full_nick_template = '%s ^w^clan %s^ ^w%s'
    try:
        for p in _Context.PLAYERS:
            # sadist
            if p.kills > map_awards.sadist["value"]:
                map_awards.sadist["uid"] = p.uid
                map_awards.sadist["clan_id"] = p.clan_id
                map_awards.sadist["name"] = p.last_used_name
                map_awards.sadist["value"] = p.kills
                map_awards.sadist["clan_tag"] = p.clan_tag
                map_awards.sadist["full_nick"] = full_nick_template % (p.clan_tag, p.clan_id, p.last_used_name)
            # ripper
            if p.deaths > map_awards.ripper["value"]:
                map_awards.ripper["uid"] = p.uid
                map_awards.ripper["clan_id"] = p.clan_id
                map_awards.ripper["name"] = p.last_used_name
                map_awards.ripper["value"] = p.deaths
                map_awards.ripper["clan_tag"] = p.clan_tag
                map_awards.ripper["full_nick"] = full_nick_template % (p.clan_tag, p.clan_id, p.last_used_name)
            # mvp
            if p.kills - p.deaths > map_awards.mvp["value"]:
                map_awards.mvp["uid"] = p.uid
                map_awards.mvp["clan_id"] = p.clan_id
                map_awards.mvp["name"] = p.last_used_name
                map_awards.mvp["value"] = p.kills - p.deaths
                map_awards.mvp["clan_tag"] = p.clan_tag
                map_awards.mvp["full_nick"] = full_nick_template % (p.clan_tag, p.clan_id, p.last_used_name)
            # survivor
            if p.killstreak > map_awards.survivor["value"]:
                map_awards.survivor["uid"] = p.uid
                map_awards.survivor["clan_id"] = p.clan_id
                map_awards.survivor["name"] = p.last_used_name
                map_awards.survivor["value"] = p.killstreak
                map_awards.survivor["clan_tag"] = p.clan_tag
                map_awards.survivor["full_nick"] = full_nick_template % (p.clan_tag, p.clan_id, p.last_used_name)
            # aimbot
            if p.accuracy_stats.accuracy_percent > map_awards.aimbot["value"]:
                map_awards.aimbot["uid"] = p.uid
                map_awards.aimbot["clan_id"] = p.clan_id
                map_awards.aimbot["name"] = p.last_used_name
                map_awards.aimbot["value"] = p.accuracy_stats.accuracy_percent
                map_awards.aimbot["clan_tag"] = p.clan_tag
                map_awards.aimbot["full_nick"] = full_nick_template % (p.clan_tag, p.clan_id, p.last_used_name)
            # phoe
            if p.npc_killed > map_awards.phoe["value"]:
                map_awards.phoe["uid"] = p.uid
                map_awards.phoe["clan_id"] = p.clan_id
                map_awards.phoe["name"] = p.last_used_name
                map_awards.phoe["value"] = p.npc_killed
                map_awards.phoe["clan_tag"] = p.clan_tag
                map_awards.phoe["full_nick"] = full_nick_template % (p.clan_tag, p.clan_id, p.last_used_name)
            # first frag
            if p.first_frag == 1:
                map_awards.first_frag["uid"] = p.uid
                map_awards.first_frag["clan_id"] = p.clan_id
                map_awards.first_frag["name"] = p.last_used_name
                map_awards.first_frag["value"] = p.first_frag
                map_awards.first_frag["clan_tag"] = p.clan_tag
                map_awards.first_frag["full_nick"] = full_nick_template % (p.clan_tag, p.clan_id, p.last_used_name)
            # last frag that made your team win
            if p.last_frag == 1 and (red_score == frag_limit or blue_score == frag_limit):
                map_awards.last_frag["uid"] = p.uid
                map_awards.last_frag["clan_id"] = p.clan_id
                map_awards.last_frag["name"] = p.last_used_name
                map_awards.last_frag["value"] = p.last_frag
                map_awards.last_frag["clan_tag"] = p.clan_tag
                map_awards.last_frag["full_nick"] = full_nick_template % (p.clan_tag, p.clan_id, p.last_used_name)
            # camper (0 deaths)
            if p.deaths == 0 and p.kills > 0:
                map_awards.camper["uid"] = p.uid
                map_awards.camper["clan_id"] = p.clan_id
                map_awards.camper["name"] = p.last_used_name
                map_awards.camper["value"] = p.deaths
                map_awards.camper["clan_tag"] = p.clan_tag
                map_awards.camper["full_nick"] = full_nick_template % (p.clan_tag, p.clan_id, p.last_used_name)
            # fpm (frags per minute)
            if p.fpm > map_awards.fpm["value"]:
                map_awards.fpm["uid"] = p.uid
                map_awards.fpm["clan_id"] = p.clan_id
                map_awards.fpm["name"] = p.last_used_name
                map_awards.fpm["value"] = p.fpm
                map_awards.fpm["clan_tag"] = p.clan_tag
                map_awards.fpm["full_nick"] = full_nick_template % (p.clan_tag, p.clan_id, p.last_used_name)
            # bunny
            if p.jumps > map_awards.bunny["value"]:
                map_awards.bunny["uid"] = p.uid
                map_awards.bunny["clan_id"] = p.clan_id
                map_awards.bunny["name"] = p.last_used_name
                map_awards.bunny["value"] = p.jumps
                map_awards.bunny["clan_tag"] = p.clan_tag
                map_awards.bunny["full_nick"] = full_nick_template % (p.clan_tag, p.clan_id, p.last_used_name)
    except:
        sh_custom_utils.get_and_log_exception_info()
    return map_awards


# Binds awards to the owners
def bind_awards_to_players(map_awards):
    for p in _Context.PLAYERS:
        p.awards.mvp = 1 if map_awards.mvp["uid"] == p.uid else 0
        p.awards.sadist = 1 if map_awards.sadist["uid"] == p.uid else 0
        p.awards.survivor = 1 if map_awards.survivor["uid"] == p.uid else 0
        p.awards.ripper = 1 if map_awards.ripper["uid"] == p.uid else 0
        p.awards.phoe = 1 if map_awards.phoe["uid"] == p.uid else 0
        p.awards.aimbot = 1 if map_awards.aimbot["uid"] == p.uid else 0


# Global variables (gs_transmit4-9) that are being transferred to the clients:
def update_clients_vars(map_awards):
    # gs_transmit4 = all awards in one variable with delimiters. Supposed to be parsed on the client side.
    core.CommandExec("set gs_transmit4 %s" % map_awards.get_transmit_value())
