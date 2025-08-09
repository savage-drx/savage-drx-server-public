# ---------------------------------------------------------------------------
#           Name: sv_maps.py
#    Description: Manager for Map Rotation and Votes
# ---------------------------------------------------------------------------

# Savage API
import core
import server

# Python Library Modules
import random
import urllib.request as req
import os
import sh_logger as log
import sh_custom_utils
import sh_executor

# Generates first value for the future random values
random.seed()

# fix for: 'unknown encoding: idna'
import encodings.idna


class MapSettings:
    VOTE_ALLOWED = 1
    VOTE_FORBIDDEN = 0

    IS_WORLD_LIST_ENABLED = python_config.getboolean('Python_Maps', 'IS_WORLD_LIST_ENABLED')
    WORLD_LIST_FILE_NAME = python_config.get('Python_Maps', 'WORLD_LIST_FILE_NAME')
    SKIP_MAP_CHECK = python_config.getboolean('Python_Maps', 'SKIP_MAP_CHECK')

    WORLD_FOLDER = 'world/'
    S2Z_EXTENSION = '.s2z'
    OVERHEAD_EXTENSION = '_overhead.jpg'

    # stateful:
    last_called_map = ''
    # List (for each map): Names of all Maps on this Server
    map_name = []
    # Names of Maps to ignore
    map_filter = ["benchmark", "_undo_", "xr_tutorial_b1", "xr_tutorial_h1", "tutorial", "xr_duel_tutor2"]

    @staticmethod
    def map_to_s2z(name):
        return name + MapSettings.S2Z_EXTENSION

    @staticmethod
    def map_to_overhead(name):
        return name + MapSettings.OVERHEAD_EXTENSION


class RemoteFile:
    def __init__(self, name, size, url_open):
        self.name = name
        self.size = size
        self.url_open = url_open


# Called directly by Silverback
def init():
    log.info("Initializing Maps...")

    core.CommandExec('createObject pinetree_old 0 0 0 0 0 0 0 0')
    core.CommandExec('createObject pinetree_light_xr 0 0 0 0 0 0 0 0')
    core.CommandExec('createObject pinetree_dark_xr 0 0 0 0 0 0 0 0')
    core.CommandExec('createObject pinetree_dead_xr 0 0 0 0 0 0 0 0')
    log.info("Pinetree has been fixed")

    # Register some Console Commands
    core.RegisterCmd("mapsList", "sv_maps", "cmd_list")
    core.RegisterCmd("mapCheckVersion", "sv_maps", "cmd_check_version")

    # Get list of Maps on this Server
    file_list = [f for f in os.listdir(MapSettings.WORLD_FOLDER)]
    MapSettings.map_name = [os.path.splitext(f)[0] for f in file_list if
                            os.path.splitext(f)[1] == MapSettings.S2Z_EXTENSION]
    MapSettings.map_name = [f for f in MapSettings.map_name if MapSettings.map_filter.count(f) == 0]


def select_map_by_game_type(game_type):
    random_map_list = list()
    for _map in MapSettings.map_name:
        if game_type == 'RTSS' and not _map.lower().startswith(('duel_', 'ig_', 'benchmark', '_undo_',
                                                                'xr_tutorial_b1', 'xr_tutorial_h1', 'tutorial',
                                                                'xr_duel_tutor2', 'xr_duel')):
            random_map_list.append(_map)
        if game_type == 'DUEL' and _map.lower().startswith('duel_'):
            random_map_list.append(_map)
        if game_type == 'INSTAGIB' and _map.lower().startswith('ig_'):
            random_map_list.append(_map)

    log.info(f'sv_maps game_type: {game_type}, random_map_list size: {len(random_map_list)}')
    return random.choice(random_map_list)


# Called directly by Silverback
def nextmap():
    if MapSettings.IS_WORLD_LIST_ENABLED:
        map_list = []
        try:
            with open(MapSettings.WORLD_LIST_FILE_NAME) as f:
                unfiltered = [c.strip() for c in f.readlines()]
            for c in unfiltered:
                if c != '' and not c.startswith(('#', ';')):
                    map_list.append(c)
            next_map = map_list[random.randint(0, len(map_list) - 1)]
            core.CvarSetString('sv_nextMap', next_map)

            log.info(f"Next map is: {next_map}")
        except:
            sh_custom_utils.get_and_log_exception_info()
            core.CvarSetString('sv_nextMap', str(core.CvarGetString('default_world')))
    else:
        current_game_type = core.CvarGetString('sv_map_gametype')
        next_map = select_map_by_game_type(current_game_type)
        core.CvarSetString('sv_nextMap', next_map)

        log.info(f"Next map is: {next_map}")


# Called directly by Silverback
@log.log_debug_info
def callvote(client_index, map_name):
    log.info(f"Callvote: {map_name}")
    for mf in MapSettings.map_filter:
        if map_name.lower() in mf:
            log.info(f"Callvote: {map_name} -> [FORBIDDEN]")
            return MapSettings.VOTE_FORBIDDEN

    if MapSettings.last_called_map != map_name:
        MapSettings.last_called_map = map_name
    else:
        server.Notify(client_index, f'^yVoting ^yfor ^g{map_name} '
                                    f'^yis ^900forbidden ^ysince ^yit ^ywas ^ycalled ^yin ^ythe ^yprevious ^yvote.')
        log.info(f"Callvote: {map_name} -> [FORBIDDEN]")
        return MapSettings.VOTE_FORBIDDEN
    return MapSettings.VOTE_ALLOWED


# Called directly by Silverback
def cmd_list():
    # todo remove
    log.info("deprecated")
    return

    # Display Map List in Console
    map_list = ""
    map_counter = 0
    map_total = len(MapSettings.map_name)
    for index in range(0, map_total):
        # Concatenate String
        map_list = map_list + MapSettings.map_name[index]

        # Display in Console?
        map_counter += 1
        if map_counter > 5 or index == map_total - 1:
            map_list = map_list + "\n"
            log.info(map_list)
            map_counter = 0
            map_list = ""
        else:
            map_list = map_list + ", "


def cmd_check_version(map_name, load=0):
    if MapSettings.SKIP_MAP_CHECK:
        log.info(f"Skipping map check for {map_name}\n", True)
        core.CommandBuffer(f'world "{map_name}" 0')
    else:
        # blocking future.result() callback
        sh_executor.submit_task(cmd_check_version_thread, map_name, int(load)).result()


# Only a server updates its map calling this method
def cmd_check_version_thread(map_name, load=0):
    log.info(f"Checking version of the map: {map_name}", True)
    # checking the map file
    _check_file(MapSettings.map_to_s2z(map_name))
    # checking the overhead file
    _check_file(MapSettings.map_to_overhead(map_name))
    # Call this world?
    if load == 1:
        core.CommandBuffer(f'world "{map_name}" 0')


def notify_map_status(client_index, map_name):
    if map_name in MapSettings.map_name:
        server.Notify(client_index, f'^g{map_name} ^yis ^yonline')
    else:
        server.Notify(client_index, f'^g{map_name} ^yis ^900not ^900present')


# todo: check the hash of the remote file instead of the size
def _check_file(file_name):
    # Get size on local disk
    try:
        local_size = os.path.getsize(f'{MapSettings.WORLD_FOLDER}{file_name}')
    except:
        log.info(f'Local map "{file_name}" was not found')
        local_size = 0

    # Get size on map repo
    remote_check = _check_remote_file(file_name, core.CvarGetString('svr_mapurl'))

    # Compare and update if necessary
    if remote_check.size == 0:
        log.error(f'Could not update "{file_name}"')
    elif local_size != remote_check.size:
        _update_file(remote_check.url_open, file_name)
    else:
        log.info(f'File "{file_name}" is already up-to-date')


def _update_file(url_open, file_name):
    log.info(f'Downloading latest version of "{file_name}" from map repository')
    # Updating the map
    f = open(f'{MapSettings.WORLD_FOLDER}{file_name}', 'wb')
    f.write(url_open.read())
    f.close()
    _close_urlopen(url_open)


def _check_remote_file(file_name, url):
    # Get size of remote file
    remote = None
    path = f'{url}{file_name}'
    try:
        log.info(f'Checking: {path}')
        remote = req.urlopen(str(path), timeout=3)
    except Exception:
        log.info(f"Error on update for {path}")
        return RemoteFile(file_name, 0, remote)

    if remote.getcode() == 200:
        return RemoteFile(file_name, int(remote.getheader("Content-Length")), remote)
    else:
        log.info(f"File was not found. Code: {remote.getcode()}")
        return RemoteFile(file_name, -1, remote)


def _close_urlopen(url_open: req):
    try:
        url_open.close()
    except:
        log.error("Error while closing remote connection.")
        sh_custom_utils.get_and_log_exception_info()
