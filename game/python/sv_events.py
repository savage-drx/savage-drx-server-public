# ---------------------------------------------------------------------------
#           Name: sv_events.py
#    Description: Silverback Event Entries (init, frame, status changes)
# ---------------------------------------------------------------------------

# Savage API
import server

# External modules
import sv_defs
import sv_maps
import sv_triggers
import sh_custom_utils
import sv_events_handler
import sh_logger as log
import binascii
import hashlib
import sh_io
from time import strftime, localtime, time
import sv_lifecycle
import sv_messaging
import sv_utils
import sv_warmup
import sv_bans
from sv_permissions import PermissionsContext as pc
from sv_context import SharedContext

# fix for: 'unknown encoding: idna'
import encodings.idna


class EventsSettings:
    # Date format
    DATE_FORMAT = "%Y.%m.%d - %H:%M:%S"


class EventsContext:
    spawned_players = dict()
    is_online_low = False
    is_online_high = False


# ------------------------------------------------------------
# Modules contains functions called directly by Silverback
# ------------------------------------------------------------
def init():
    log.check_visual_formatting()
    log.info("Initializing sv_events...")

    try:
        # Init Server Modules
        sv_maps.init()
        sv_triggers.init()
        sv_bans.init_banned()

    except:
        sh_custom_utils.get_and_log_exception_info()


def frame():
    # Refresh System Information
    try:
        sv_defs.gameTime = server.GetGameInfo(GAME_TIME)
    except:
        pass

    # Refresh Object Data
    [sv_defs.objectList_Active, sv_defs.objectList_Team, sv_defs.objectList_Type,
     sv_defs.objectList_Name, sv_defs.objectList_Health, sv_defs.objectList_MaxHealth,
     sv_defs.objectList_Construct, sv_defs.objectList_Last] = server.GetObjectList()

    # Refresh Client Data
    [sv_defs.clientList_Active, sv_defs.clientList_Bot, sv_defs.clientList_Team,
     sv_defs.clientList_Officer, sv_defs.clientList_Squad, sv_defs.clientList_Charge,
     sv_defs.clientList_Mana, sv_defs.clientList_MaxMana, sv_defs.clientList_Health,
     sv_defs.clientList_MaxHealth, sv_defs.clientList_Stamina,
     sv_defs.clientList_MaxStamina] = server.GetClientList()

    # Refresh Team Data
    [sv_defs.teamList_Base, sv_defs.teamList_Commander, sv_defs.teamList_RaceName,
     sv_defs.teamList_RaceDesc, sv_defs.teamList_Missions, sv_defs.teamList_Last] = server.GetTeamList()

    # Check Triggers
    sv_triggers.frame()

    sv_events_handler.return_initial_items(EventsContext.spawned_players)
    sv_warmup.on_frame()


def status():
    try:
        sv_lifecycle.StatusDispatcher.ON_STATUS[server.GetGameInfo(GAME_STATE)]()
    except:
        sh_custom_utils.get_and_log_exception_info()


@log.log_debug_info
# message_type: global, team, squad, selected
def chat_message(client_index, message_type, message):
    # Accept chat by default
    answer = 1
    try:
        answer = sv_messaging.process_chat_message(client_index, message_type, message)
    except:
        sh_custom_utils.get_and_log_exception_info()
    return answer


@log.log_debug_info
def private_message(sender_idx, receiver_idx, message):
    # Accept private message by default
    answer = 1
    try:
        answer = sv_messaging.process_private_message(sender_idx, receiver_idx, message)
    except:
        sh_custom_utils.get_and_log_exception_info()
    return answer


@log.log_debug_info
def client_connected(client_index, client_ip, client_version):
    try:
        # uid request is unreachable here
        client_name = server.GetClientInfo(client_index, INFO_NAME)
        log.info(f'Connected: {client_name}, client_index: {client_index}, '
                 f'ip: {client_ip}, client_version: {client_version}')
    except:
        sh_custom_utils.get_and_log_exception_info()


@log.log_debug_info
def client_disconnected(client_index):
    try:
        uid = server.GetClientInfo(client_index, INFO_UID)
        log.info(f'Disconnected: {server.GetClientInfo(client_index, INFO_NAME)}, uid: {uid}')
    except:
        sh_custom_utils.get_and_log_exception_info()


def client_connected_extended(client_index, ip, cn):
    try:
        uid = server.GetClientInfo(client_index, INFO_UID)
        name = server.GetClientInfo(client_index, INFO_NAME)

        msg = f'Auth info: {ip}; {name}; idx:{client_index}; uid:{uid}'
        log.info(msg)

        msg_with_date = f'[{strftime(EventsSettings.DATE_FORMAT, localtime())}]   {msg}'
        sh_io.save_to_file("connected_clients", msg_with_date)

        sv_bans.check_banned(name, ip, uid)
    except:
        sh_custom_utils.get_and_log_exception_info()


@log.log_debug_info
def player_spawned(client_index):
    try:
        sv_events_handler.on_spawn(client_index, EventsContext.spawned_players)
        sv_events_handler.check_banned_units(client_index)
        sv_warmup.on_spawn(client_index)
    except:
        sh_custom_utils.get_and_log_exception_info()


@log.log_debug_info
def player_killed(client_index, killer_index):
    try:
        # Don't log bots
        if sv_defs.clientList_Bot[client_index]:
            return

        sv_events_handler.check_banned_units(client_index)

        # check killerIndex first, might not be client, and might not even be a valid object
        if 0 <= killer_index < MAX_CLIENTS:
            name = server.GetClientInfo(killer_index, INFO_NAME)

            # sv_events_handler.send_frag_to_discord(client_index, killer_index)

        elif killer_index < MAX_OBJECTS:
            name = sv_defs.objectList_Name[killer_index]
        else:
            log.error(f'Player {server.GetClientInfo(client_index, INFO_NAME)} '
                      f'({client_index}) was killed in mysterious ways')
            return
        log.info(f'Player {server.GetClientInfo(client_index, INFO_NAME)} '
                 f'({client_index}) was killed by {name} ({killer_index})')

        sv_events_handler.process_death_from_siege(client_index, killer_index)
        sv_warmup.on_death(client_index)
    except:
        sh_custom_utils.get_and_log_exception_info()


@log.log_debug_info
def commander_set(team, uid):
    # when commander is elected
    pass


@log.log_debug_info
def on_team_switch(uid, old_team, new_team):
    log.info(f'Team switch uid: {uid}, old team: {old_team}, new team: {new_team}')

    try:
        online_state = sv_utils.OnlineState()
        max_active_players = python_config.getint('Python_General', 'MAX_ACTIVE_PLAYERS_FOR_LOW_ONLINE')

        if online_state.online <= max_active_players:
            if not EventsContext.is_online_low and not EventsContext.is_online_high:
                sv_events_handler.apply_low_online_settings(online_state, max_active_players)
                EventsContext.is_online_low = True
            elif EventsContext.is_online_high and not EventsContext.is_online_low:
                sv_events_handler.apply_low_online_settings(online_state, max_active_players)
                EventsContext.is_online_low = True
                EventsContext.is_online_high = False
        elif online_state.online > max_active_players:
            if not EventsContext.is_online_high and EventsContext.is_online_low:
                sv_events_handler.apply_high_online_settings(online_state, max_active_players)
                EventsContext.is_online_low = False
                EventsContext.is_online_high = True

    except:
        sh_custom_utils.get_and_log_exception_info()


@log.log_debug_info
def building_construct(uid, building_type):
    pass


@log.log_debug_info
def building_destroyed(uid):
    pass


@log.log_debug_info
def building_research(uid, research_type):
    pass


@log.log_debug_info
def building_researchcomplete(uid, research_type):
    pass


@log.log_debug_info
def building_claim(uid, by_uid):
    pass


@log.log_debug_info
def on_buff_request(uid, buff_type):
    pass


@log.log_debug_info
def on_money_request(uid, param):
    pass


@log.log_debug_info
def on_build_request(uid, param):
    pass


@log.log_debug_info
def is_team_switch_allowed(uid, old_team, new_team):
    # todo: this does not work during the [warmup -> start] since all of the clients are connecting again with uid as 0
    if new_team > 0 and uid > 0:
        return int(pc.has_privilege('CAN_JOIN_TEAM', uid))
    return 1


@log.log_debug_info
def is_name_change_allowed(uid, name):
    # todo: the issue when the connected client has uid = 0 (the same as unauthorized); leads to the change-name for all
    if uid > 0:
        return int(pc.has_privilege('CAN_USE_ANY_NICKNAME', uid))
    else:
        return 1


@log.log_debug_info
def is_voice_command_allowed(uid):
    return int(pc.has_privilege('CAN_USE_VOICE_COMMANDS', uid))


@log.log_debug_info
def is_buff_allowed(uid):
    return int(pc.has_privilege('CAN_DO_POWERUP_REQUEST', uid))


@log.log_debug_info
def is_money_allowed(uid):
    return int(pc.has_privilege('CAN_DO_MONEY_REQUEST', uid))


@log.log_debug_info
def is_build_allowed(uid):
    return int(pc.has_privilege('CAN_DO_BUILD_REQUEST', uid))


@log.log_debug_info
def name_change(uid: int, name: str) -> str:
    return name
