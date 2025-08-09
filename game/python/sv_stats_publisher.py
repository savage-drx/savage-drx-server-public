# -------------------------------------------------------------------------------------------------------
#          Name: sv_stats_publisher.py
#   Description: Accumulating and publishing of the server statistics
# -------------------------------------------------------------------------------------------------------

# Savage API
import server
import core

import sv_defs
import time
import sh_custom_utils
import sh_executor
import sh_logger as log
import json
import sv_requests


# ____________ PUBLIC API ____________

def publish_end_game_stats():
    sh_executor.submit_task(__publish_end_game_results)


def update_players_stats():
    sh_executor.submit_task(__update_players_stats)


# ____________ PRIVATE ____________


class _PublisherContext:
    STATS_PUBLISHER_END_GAME_URL = core.CvarGetString('sv_authserver') + "history/results"
    players_by_uids = dict()
    players_by_ips = dict()


def __update_players_stats():
    try:
        log.info("Updating players stats")
        current_players = dict()

        for client_index in range(MAX_CLIENTS):
            # Ignore inactive Client Slots and Bots
            if server.GetClientInfo(client_index, INFO_ACTIVE) and not sv_defs.clientList_Bot[client_index]:
                uid = int(server.GetClientInfo(client_index, INFO_UID))

                # Fill only with the authorized players
                if uid > 0:
                    p = _Player(
                        name=server.GetClientInfo(client_index, INFO_NAME),
                        uid=uid,
                        clan_id=int(server.GetClientInfo(client_index, INFO_CLANID)),
                        clan_tag_name=server.GetClientInfo(client_index, INFO_CLANABBREV),
                        info=_PlayerInfo(client_index),
                        accuracy=_PlayerAccuracy(client_index).accuracy)

                    current_players[p.uid] = p

        # first run
        if not _PublisherContext.players_by_uids:
            for current_uid, current_player in current_players.items():
                _PublisherContext.players_by_uids[current_uid] = current_player
                _PublisherContext.players_by_ips[current_player.ip_address] = current_player
            return

        for current_uid, current_player in current_players.items():
            # if it is the same player then we simply update him
            if current_uid in _PublisherContext.players_by_uids:
                _PublisherContext.players_by_uids[current_uid] = current_player
            # now we have to check is it the same player or newly connected:
            elif current_player.ip_address in _PublisherContext.players_by_ips:
                cached_player_by_ip = _PublisherContext.players_by_ips[current_player.ip_address]
                del _PublisherContext.players_by_uids[cached_player_by_ip.uid]
                _PublisherContext.players_by_uids[current_uid] = current_player
                _PublisherContext.players_by_ips[current_player.ip_address] = current_player
            # it is not an old player, so we have to add him
            else:
                _PublisherContext.players_by_uids[current_uid] = current_player
                _PublisherContext.players_by_ips[current_player.ip_address] = current_player

    except:
        sh_custom_utils.get_and_log_exception_info()


def __get_end_game_results_json():
    players = list()
    for p in _PublisherContext.players_by_uids.values():
        players.append(p)

    return json.dumps(_EndGameResults(players),
                      default=lambda x: x.__dict__,
                      skipkeys=False, ensure_ascii=True, check_circular=True, allow_nan=True,
                      cls=None, indent=None, separators=None, sort_keys=False)


def __reset_context():
    _PublisherContext.players_by_uids = dict()
    _PublisherContext.players_by_ips = dict()


def __publish_end_game_results():
    try:
        log.info("Publishing end of game results...")
        __update_players_stats()
        data = str(__get_end_game_results_json())
        resp = sv_requests.post_request(_PublisherContext.STATS_PUBLISHER_END_GAME_URL, data=data)
        code = resp.getcode()
        __reset_context()
        log.info("Finished publishing end of game results. Code: {}".format(code))
        return code

    except:
        sh_custom_utils.get_and_log_exception_info()
        return 404


class _EndGameResults(object):
    def __init__(self, players):
        self.game = _Game()
        self.timestamp = self.game.timestamp
        self.winner = server.GetGameInfo(GAME_WINTEAM)
        self.players = players

    def __str__(self):
        return str(self.__dict__)


class _Game(object):
    def __init__(self):
        self.map_name = core.CvarGetString('world_name')
        self.timestamp = int(time.time())
        self.game_time = server.GetGameInfo(GAME_TIME)
        self.game_state = server.GetGameInfo(GAME_STATE)
        self.teams = {}
        self.online = 0
        self.__init_teams()

    def __init_teams(self):
        for i in range(int(core.CvarGetString('sv_numTeams'))):
            self.teams[i] = _Game.GTeam(i)
        # fill teams with players
        for client_index in range(MAX_CLIENTS):
            # Ignore inactive Client Slots and Bots
            if server.GetClientInfo(client_index, INFO_ACTIVE) and not sv_defs.clientList_Bot[client_index]:
                team_id = sv_defs.objectList_Team[client_index]
                self.online = self.online + 1

                p = _Game.GPlayer(
                    name=server.GetClientInfo(client_index, INFO_NAME),
                    uid=int(server.GetClientInfo(client_index, INFO_UID)),
                    clan_id=int(server.GetClientInfo(client_index, INFO_CLANID)),
                    clan_tag_name=server.GetClientInfo(client_index, INFO_CLANABBREV),
                    is_commander=True if client_index == sv_defs.teamList_Commander[team_id] else False,
                    connect_time=server.GetClientInfo(client_index, STAT_CONNECTTIME),
                    on_team_time=server.GetClientInfo(client_index, STAT_ONTEAMTIME))

                self.teams[team_id].players.append(p)

    class GTeam(object):
        def __init__(self, team_id):
            self.team_id = team_id
            self.team_name = ''
            self.race = sv_defs.teamList_RaceName[team_id]
            self.players = list()

            if self.team_id == 0:
                self.team_name = 'Spectators'
            else:
                self.team_name = 'Team %s' % self.team_id

        def __str__(self):
            return str(self.__dict__)

    class GPlayer(object):
        def __init__(self, name: str, uid: int, clan_id: int, clan_tag_name: str, is_commander: bool, connect_time: int,
                     on_team_time: int):
            self.name = name
            self.uid = uid
            self.clan_id = clan_id
            self.clan_tag_name = clan_tag_name
            self.is_commander = is_commander
            self.connect_time = connect_time
            self.on_team_time = on_team_time

        def __str__(self):
            return str(self.__dict__)

    def __str__(self):
        return str(self.__dict__)


class _PlayerInfo(object):
    def __init__(self, client_index):
        self.on_team_time = server.GetClientInfo(client_index, STAT_ONTEAMTIME)
        self.deaths = server.GetClientInfo(client_index, STAT_DEATHS)
        self.kills = server.GetClientInfo(client_index, STAT_KILLS)
        self.kill_streak = server.GetClientInfo(client_index, STAT_KILLSTREAK)
        self.blocks = server.GetClientInfo(client_index, STAT_BLOCKS)
        self.jumps = server.GetClientInfo(client_index, STAT_JUMPS)
        self.carn_hp = server.GetClientInfo(client_index, STAT_CARNHP)
        self.npc_damage = server.GetClientInfo(client_index, STAT_NPCDMG)
        self.npc_kill = server.GetClientInfo(client_index, STAT_NPCKILL)
        self.peon_damage = server.GetClientInfo(client_index, STAT_PEONDMG)
        self.peon_kill = server.GetClientInfo(client_index, STAT_PEONKILL)
        self.build_damage = server.GetClientInfo(client_index, STAT_BUILDDMG)
        self.build_kill = server.GetClientInfo(client_index, STAT_BUILDKILL)
        self.outpost_damage = server.GetClientInfo(client_index, STAT_OUTPOSTDMG)
        self.client_damage = server.GetClientInfo(client_index, STAT_CLIENTDMG)
        self.melee_kill = server.GetClientInfo(client_index, STAT_MELEEKILL)
        self.ranged_kill = server.GetClientInfo(client_index, STAT_RANGEDKILL)
        self.siege_kill = server.GetClientInfo(client_index, STAT_SIEGEKILL)
        self.mine = server.GetClientInfo(client_index, STAT_MINE)
        self.heal = server.GetClientInfo(client_index, STAT_HEAL)
        self.build = server.GetClientInfo(client_index, STAT_BUILD)
        self.money_gained = server.GetClientInfo(client_index, STAT_MONEYGAIN)
        self.money_spent = server.GetClientInfo(client_index, STAT_MONEYSPEND)
        self.order_give = server.GetClientInfo(client_index, STAT_ORDERGIVE)
        self.order_obeyed = server.GetClientInfo(client_index, STAT_ORDEROBEY)
        self.experience = server.GetClientInfo(client_index, STAT_EXPERIENCE)
        self.auto_buff = server.GetClientInfo(client_index, STAT_AUTOBUFF)
        self.sacrifice = server.GetClientInfo(client_index, STAT_SACRIFICE)
        self.flag_capture = server.GetClientInfo(client_index, STAT_FLAGCAPTURE)

    def __str__(self):
        return str(self.__dict__)


class _PlayerAccuracy(object):
    def __init__(self, client_index):
        self.unfiltered = _PlayerAccuracy.PUnfiltered(client_index)
        self.accuracy = list(self.unfiltered.accuracy)
        del self.unfiltered

    class PUnfiltered(object):
        def __init__(self, client_index):
            [
                self.weapon,  # array
                self.shots,  # array
                self.kills,  # array
                self.deaths,  # array
                self.hits,  # array
                self.siege_hits,  # array
                self.damage,  # array
                self.last  # int
            ] = server.GetAccuracyList(client_index)

            self.accuracy = list()

            for index in range(0, self.last):
                if self.weapon[index] is not '<NULL>':
                    weapon = _PlayerAccuracy.PWeapon(
                        self.weapon[index],
                        self.shots[index],
                        self.kills[index],
                        self.deaths[index],
                        self.hits[index],
                        self.siege_hits[index],
                        self.damage[index]
                    )
                    self.accuracy.append(weapon)

        def __str__(self):
            return str(self.__dict__)

    class PWeapon(object):
        def __init__(self, name, shots, kills, deaths, hits, siege_hits, damage):
            self.name = name
            self.shots = shots
            self.kills = kills
            self.deaths = deaths
            self.hits = hits
            self.siege_hits = siege_hits
            self.damage = damage

        def __str__(self):
            return str(self.__dict__)

    def __str__(self):
        return str(self.__dict__)


class _Player(object):
    def __init__(self, name, uid, clan_id, clan_tag_name,
                 info: _PlayerInfo, accuracy: list):
        self.name = name
        self.uid = uid
        self.clan_id = clan_id
        self.clan_tag_name = clan_tag_name
        self.info = info
        self.accuracy = accuracy

    def __str__(self):
        return str(self.__dict__)
