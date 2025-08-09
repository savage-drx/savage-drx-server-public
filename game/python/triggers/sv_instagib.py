# ---------------------------------------------------------------------------
#           Name: sv_instagib.py
#    Description: Instagib server trigger
# ---------------------------------------------------------------------------

# Savage API
import core
import server

# External modules
import sv_defs
import sv_utils
import random
import time
import threading
import sh_custom_utils
import sh_executor


class _Context:
    GAME_MOD = None
    IS_INITIALIZED = False
    IS_FINISHED = True
    TELEPORT_LOCATIONS = list()
    INSTAGIB_MOD = "INSTAGIB"
    TYPE_LIST = ["CLIENT", "WORKER", "NPC", "MINE", "BASE", "OUTPOST", "BUILDING", "OTHER"]
    # human_stronghold was excluded from the teleport locations
    POSSIBLE_TELEPORT_LOCATIONS = {"spawnflag"}
    # Sec:
    NOTIFY_PERIOD_SEC = 25 * 1000

    ACTIVE_CLIENT_INDICES = set()
    LOCK = threading.Lock()
    DEAD_QUEUE_LOCK = threading.Lock()
    # A queue of dead players that should be revived
    DEAD_QUEUE = set()

    TEAM_FRAGS = [0, 0]
    LAST_NOTIFY_TIME = 0
    FRAG_LIMIT = 30
    FRAG_LIMIT_MULTIPLIER = 0
    CONSTANT_FRAG_LIMIT = 0
    DEFAULT_FRAG_LIMIT = 0

    AVAILABLE_GAME_STATES = (1, 2, 3)
    RESET_STATES = (1, 2)
    NEED_RESET = True

    # Player's inventory structure
    INVENTORY = dict()
    # First-Last frags structure:
    FIRST_AND_LAST_FRAG = dict()
    PLAYERS_FRAGS = dict()
    

# Is called during every server frame
def check():
    try:
        # Run-once
        run_once()

        # Reset vars
        if server.GetGameInfo(GAME_STATE) in _Context.RESET_STATES and _Context.NEED_RESET:
            reset_clients_vars()
            _Context.NEED_RESET = False

        # Runs only for INSTAGIB_MOD
        if _Context.GAME_MOD != _Context.INSTAGIB_MOD:
            return 0

        # If game setup, warmup or normal
        if server.GetGameInfo(GAME_STATE) in _Context.AVAILABLE_GAME_STATES:
            iterate_over_clients()
            get_team_stats()
            calculate_dynamic_frag_limit()
            update_clients_vars()
            is_time_to_finish()
        # Update latest stats for end-game status
        if server.GetGameInfo(GAME_STATE) == 4 and _Context.IS_FINISHED:
            get_team_stats()
            update_clients_vars()
            _Context.IS_FINISHED = False
    except:
        sh_custom_utils.get_and_log_exception_info()
    return 0


def run_once():
    if not _Context.IS_INITIALIZED:
        _Context.IS_INITIALIZED = True
        check_mod()
        find_teleport_locations()
        get_vars_from_config()


# Checks the current mod of the game
def check_mod():
    _Context.GAME_MOD = core.CvarGetString('sv_map_gametype')
    # core.ConsolePrint(f"[!] __________  sv_map_gametype: {core.CvarGetString('sv_map_gametype')}\n")
    # core.ConsolePrint(f"[!] __________  MOD: {_Context.GAME_MOD}\n")


def get_vars_from_config():
    _Context.FRAG_LIMIT = _Context.DEFAULT_FRAG_LIMIT = int(core.CvarGetValue('py_instagib_fragLimit'))
    _Context.FRAG_LIMIT_MULTIPLIER = int(core.CvarGetValue('py_instagib_fragLimitMultiplier'))
    _Context.CONSTANT_FRAG_LIMIT = int(core.CvarGetValue('py_instagib_constantFragLimit'))
    if _Context.CONSTANT_FRAG_LIMIT > 0:
        _Context.FRAG_LIMIT = _Context.CONSTANT_FRAG_LIMIT


# Gets an array of the team frags ([T1_FRAGS, T2_FRAGS]).
# There could be the same server variable and this duplicate logic is useless
def get_team_stats():
    objects_team_1 = []
    objects_team_2 = []
    _Context.TEAM_FRAGS = [0, 0]
    for index in range(0, MAX_CLIENTS):
        if sv_defs.clientList_Team[index] == 1:
            objects_team_1.append(str(index))
        if sv_defs.clientList_Team[index] == 2:
            objects_team_2.append(str(index))
    for idx_1 in objects_team_1:
        frags = int(server.GetClientInfo(int(idx_1), STAT_KILLS))
        _Context.TEAM_FRAGS[0] += frags
        track_first_and_last_frag(idx_1, frags)
    for idx_2 in objects_team_2:
        frags = int(server.GetClientInfo(int(idx_2), STAT_KILLS))
        _Context.TEAM_FRAGS[1] += frags
        track_first_and_last_frag(idx_2, frags)
    return _Context.TEAM_FRAGS


def track_first_and_last_frag(client_index, frags):
    # If game is in the normal state
    if server.GetGameInfo(GAME_STATE) == 3:
        if frags == 1 and 'first' not in _Context.FIRST_AND_LAST_FRAG:
            _Context.FIRST_AND_LAST_FRAG['first'] = client_index
            core.CommandExec(f'set gs_first_frag_guid {client_index}')
        if client_index not in _Context.PLAYERS_FRAGS:
            _Context.PLAYERS_FRAGS[client_index] = frags
        elif frags > _Context.PLAYERS_FRAGS[client_index]:
            _Context.PLAYERS_FRAGS[client_index] = frags
            _Context.FIRST_AND_LAST_FRAG['last'] = client_index
            core.CommandExec(f'set gs_last_frag_guid {client_index}')


# Global variables (gs_transmit1-3) that are being transferred to the clients:
def update_clients_vars():
    # gs_transmit1 = TEAM_1 Frags (RED)
    core.CommandExec(f'set gs_transmit1 {_Context.TEAM_FRAGS[0]}')
    # gs_transmit2 = TEAM_2 Frags (BLUE)
    core.CommandExec(f'set gs_transmit2 {_Context.TEAM_FRAGS[1]}')
    # gs_transmit3 = _Context.FRAG_LIMIT
    core.CommandExec(f'set gs_transmit3 {_Context.FRAG_LIMIT}')


def reset_clients_vars():
    for idx in range(1, 10):
        # reset all except gs_transmit 5
        if idx != 5:
            core.CommandExec(f'set gs_transmit{idx} 0')
    core.CommandExec("set gs_first_frag_guid -1")
    core.CommandExec("set gs_last_frag_guid -1")


def calculate_dynamic_frag_limit():
    active_clients = len(_Context.ACTIVE_CLIENT_INDICES)
    if active_clients > 0 and _Context.CONSTANT_FRAG_LIMIT == 0:
        current_frag_limit = int(core.CvarGetValue('py_instagib_fragLimit'))
        future_frag_limit = _Context.DEFAULT_FRAG_LIMIT + active_clients * _Context.FRAG_LIMIT_MULTIPLIER
        if future_frag_limit > current_frag_limit:
            _Context.FRAG_LIMIT = future_frag_limit
            core.CvarSetValue('py_instagib_fragLimit', future_frag_limit)


def iterate_over_clients():
    for client_index in range(0, sv_defs.objectList_Last):
        if sv_defs.objectList_Active[client_index] and sv_defs.objectList_Team[client_index] > 0:
            object_type = str(_Context.TYPE_LIST[sv_defs.objectList_Type[client_index]])
            object_health = int(sv_defs.objectList_Health[client_index])
            if object_type == "CLIENT" and object_health == 0:
                teleport_and_revive(client_index)
                remove_items_on_death(client_index)
            if object_type == "CLIENT":
                _Context.ACTIVE_CLIENT_INDICES.add(client_index)
                check_for_frags_and_items(client_index)
                # If game is in the 'setup' state - notify players to hit F3
                # if server.GetGameInfo(GAME_STATE) == 1 or server.GetGameInfo(GAME_STATE) == 2:
                #    notify_to_get_ready(client_index)


def remove_items_on_death(client_index):
    # Cleaning 2 slots:
    server.GameScript(client_index, '!remove target 3')
    server.GameScript(client_index, '!remove target 4')


def check_for_frags_and_items(client_index):
    try:
        client_index = int(client_index)
        kills_for_sensor = 3
        kills_for_reloc = 1
        # kills_for_mist = 5

        # Checking is there enough ammo in the Coil
        server.GameScript(client_index, '!inventory target 1')
        slot1 = int(core.CvarGetString('gs_inventory_count'))
        if slot1 <= 0:
            # !give target human_coilrifle ammo slot (slots: 0,1,2,3,4)
            server.GameScript(client_index, '!give target human_coilrifle 100 1')

        server.GameScript(client_index, '!inventory target 2')
        slot2 = bool(core.CvarGetString('gs_inventory_name'))
        server.GameScript(client_index, '!inventory target 3')
        slot3 = bool(core.CvarGetString('gs_inventory_name'))
        server.GameScript(client_index, '!inventory target 4')
        slot4 = bool(core.CvarGetString('gs_inventory_name'))
        kills = int(server.GetClientInfo(client_index, STAT_KILLS))
        # killstreak = int(server.GetClientInfo(client_index, STAT_KILLSTREAK))

        # Always give beast_tracking_sense
        if slot2 <= 0:
            server.GameScript(client_index, '!give target beast_tracking_sense 1 2')

        template = '^gReceived new item: ^y%s'
        if client_index in _Context.INVENTORY:

            # if not bool(kills % kills_for_mist) and inventory[client_index][1] != kills and not bool(slot3):
            #     server.GameScript(client_index, '!give target beast_camouflage 1 3')
            #     inventory[client_index][1] = kills
            #     server.Notify(client_index, template % 'Mist Shroud')
            # elif not bool(kills % kills_for_mist) and bool(slot3):
            #     inventory[client_index][1] = kills

            if not bool(kills % kills_for_sensor) and _Context.INVENTORY[client_index][1] != kills and not bool(slot3):
                server.GameScript(client_index, '!give target human_motion_sensor 1 3')
                _Context.INVENTORY[client_index][1] = kills
                server.Notify(client_index, template % 'Sensor')
            elif not bool(kills % kills_for_sensor) and bool(slot3):
                _Context.INVENTORY[client_index][1] = kills

            if not bool(kills % kills_for_reloc) and _Context.INVENTORY[client_index][2] != kills and not bool(slot4):
                server.GameScript(client_index, '!give target human_relocater 1 4')
                _Context.INVENTORY[client_index][2] = kills
                server.Notify(client_index, template % 'Relocater')
            elif not bool(kills % kills_for_reloc) and bool(slot4):
                _Context.INVENTORY[client_index][2] = kills

        else:
            _Context.INVENTORY[client_index] = [0, 0, 0]
    except:
        sh_custom_utils.get_and_log_exception_info()


def teleport_and_revive(client_index):
    client_index = int(client_index)
    with _Context.DEAD_QUEUE_LOCK:
        if client_index not in _Context.DEAD_QUEUE:
            _Context.DEAD_QUEUE.add(client_index)
            sh_executor.submit_task(execute_waiting_and_reviving, client_index)


def execute_waiting_and_reviving(client_index):
    client_index = int(client_index)
    # Sleeping N seconds before any further actions. Is done to prevent interrupting of the death animation and effects
    time.sleep(1)

    # Check if client's hp > 0 - return (already teleported)
    if int(sv_defs.clientList_Health[client_index]) > 0:
        _Context.DEAD_QUEUE.remove(client_index)
        return

    # If game state is setup, warmup or normal
    try:
        if server.GetGameInfo(GAME_STATE) in _Context.AVAILABLE_GAME_STATES:
            with _Context.LOCK:
                core.CommandExec('revive %s' % client_index)
                point = get_random_spawn_location()
                # core.ConsolePrint(f"Teleporting: {server.GetClientInfo(client_index, INFO_NAME)} [{point[0]}, {point[1]}]\n")
                server.GameScript(client_index, '!teleport target coords %s %s' % (point[0], point[1]))
                server.GameScript(client_index, '!heal target 500')
                server.GameScript(client_index, '!givestamina target 100')
                if client_index in _Context.DEAD_QUEUE:
                    _Context.DEAD_QUEUE.remove(client_index)
                time.sleep(0.5)
    except:
        sh_custom_utils.get_and_log_exception_info()


# Finds all possible teleport location from the 'teleport_locations' list.
# Should be run-once at start
def find_teleport_locations():
    for index in range(0, sv_defs.objectList_Last):
        if sv_defs.objectList_Active[index]:
            object_name = str(sv_defs.objectList_Name[index])
            if object_name in _Context.POSSIBLE_TELEPORT_LOCATIONS:
                _Context.TELEPORT_LOCATIONS.append(sv_utils.get_point3(index))


def get_random_spawn_location():
    return random.choice(_Context.TELEPORT_LOCATIONS)


# Checks conditions (such as time and frag limits) to end the current game
def is_time_to_finish():
    # Normal play mode: 3
    if server.GetGameInfo(GAME_STATE) == 3:
        # Dirty hack to count max_time without 1 second (was done to prevent overtime)
        max_time = int(core.CvarGetValue('gs_game_status_end')) - 500
        current_time = int(core.CvarGetValue('gs_game_time'))
        _team_frags = get_team_stats()
        if current_time >= max_time:
            # current_time >= max_time  current_time=509, max_time=-1000
            core.CommandExec('endgame %s' % get_team_winner(_team_frags))
            return
        if _team_frags[0] == _Context.FRAG_LIMIT and _team_frags[1] == _Context.FRAG_LIMIT:
            core.CommandExec('endgame 0')
            return
        if _team_frags[0] == _Context.FRAG_LIMIT:
            core.CommandExec('endgame 1')
            return
        if _team_frags[1] == _Context.FRAG_LIMIT:
            core.CommandExec('endgame 2')


def get_team_winner(frags):
    if frags[0] > frags[1]:
        return 1
    elif frags[0] < frags[1]:
        return 2
    return 0


def notify_to_get_ready(client_index):
    current_time_millis = int(round(time.time() * 1000))
    if current_time_millis > _Context.LAST_NOTIFY_TIME + _Context.NOTIFY_PERIOD_SEC:
        _Context.LAST_NOTIFY_TIME = current_time_millis
        server.Notify(client_index, '^gGet ^gReady! ^yPress ^900F3 ^gto ^gstart ^gthe ^ggame.')


# Is called when check() returns 1
# Is not used in the current script
def execute():
    pass
