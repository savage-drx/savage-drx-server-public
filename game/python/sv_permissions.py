import base64
import json
import ssl
import urllib.request
from dataclasses import dataclass
from typing import List, Set

import core
import server
import sh_custom_utils
import sh_logger as log


@dataclass
class ARData(object):
    def __init__(self, role: str, privileges: List[str], users: Set[int]):
        self.role = role
        self.privileges = privileges
        self.users = users

    role: str
    privileges: List[str]
    users: Set[int]

    def __str__(self):
        return str(self.__dict__)


@dataclass
class AuthRequest(object):
    def __init__(self, version: int, data):
        self.version = version
        self.data = [ARData(**d) for d in data]

    version: int
    data: List[ARData]

    def __str__(self):
        return str(self.__dict__)


class GamePrivilege:
    def __init__(self, users: Set[int], enabled: bool = True, notify_user: bool = True,
                 notification: str = ""):
        self.users = users
        self.enabled = enabled
        self.notify_user = notify_user
        self.notification = " ".join(f'^g{str(item)}' for item in notification.split())

    def __str__(self):
        return str(self.__dict__)


class PermissionsContext:
    GAME_PRIVILEGES_ARE_ENABLED = python_config.getboolean('Python_General', 'GAME_PRIVILEGES_ARE_ENABLED', fallback=0)
    URL_AUTHORITIES_VERSION = core.CvarGetString('sv_authserver') + "server/authorities/version"
    URL_AUTHORITIES_USERS = core.CvarGetString('sv_authserver') + "server/authorities/users"
    AUTH_SERVER_ID = core.CvarGetString('sv_authid')
    AUTH_SERVER_TOKEN = core.CvarGetString('sv_authtoken')
    AUTH_SERVER_CREDENTIALS = None
    PRIVILEGES_EXCLUDE_PREFIX = "EXCLUDE_"
    PRIVILEGES_VERSION = 0

    # Contains data redundancy to make access faster
    # ex.: if user in PermissionsContext.GAME_PRIVILEGES[p].users
    GAME_PRIVILEGES = {
        'CAN_CONNECT'
        : GamePrivilege(users=set(), notification="You are forbidden to join this server", enabled=False),
        'CAN_SPECTATE'
        : GamePrivilege(users=set(), notification="You are not allowed to join Spectators", enabled=False),
        'CAN_JOIN_TEAM'
        : GamePrivilege(users=set(), notification="You are not allowed to join any team", notify_user=False),
        'CAN_COMMAND'
        : GamePrivilege(users=set(), notification="You are not allowed to command", notify_user=False),
        'CAN_DO_BUILD_REQUEST'
        : GamePrivilege(users=set(), notification="You are not allowed to send a build request", enabled=False),
        'CAN_DO_MONEY_REQUEST'
        : GamePrivilege(users=set(), notification="You are not allowed to send a money request", enabled=False),
        'CAN_DO_POWERUP_REQUEST'
        : GamePrivilege(users=set(), notification="You are not allowed to send a powerup request", enabled=False),
        'CAN_USE_SIEGE_UNIT'
        : GamePrivilege(users=set(), notification="You are not allowed to take a siege unit", enabled=False),
        'CAN_USE_ANY_NICKNAME'
        : GamePrivilege(users=set(), notify_user=False),
        'CAN_USE_VOICE_COMMANDS'
        : GamePrivilege(users=set(), notification="You are not allowed to use any voice commands"),

        'CAN_CHAT_SPECS'
        : GamePrivilege(users=set(), notification="You are not allowed to chat in Spectators"),
        'CAN_CHAT_PRIVATE'
        : GamePrivilege(users=set(), notification="You are not allowed to send private chat"),
        'CAN_CHAT_GLOBAL'
        : GamePrivilege(users=set(), notification="You are not allowed to use the global chat"),
        'CAN_CHAT_DISCORD'
        : GamePrivilege(users=set(), notification="You are not allowed to use the discord chat"),
        'CAN_CHAT_WITH_ICONS'
        : GamePrivilege(users=set(), notification="You are not allowed to use icons in chat"),

        'CAN_VOTE_CUSTOM'
        : GamePrivilege(users=set(), notification="You are not allowed to use a custom vote"),
        'CAN_VOTE_MESSAGE'
        : GamePrivilege(users=set(), notification="You are not allowed to start a message vote"),
        'CAN_VOTE_ELECT'
        : GamePrivilege(users=set(), notification="You are not allowed to start an elect vote"),
        'CAN_VOTE_IMPEACH'
        : GamePrivilege(users=set(), notification="You are not allowed to start an impeach vote"),
        'CAN_VOTE_KICK'
        : GamePrivilege(users=set(), notification="You are not allowed to start a kick vote"),
        'CAN_VOTE_LOCK_SPEC'
        : GamePrivilege(users=set(), notification="You are not allowed to start a lockspec vote"),
        'CAN_VOTE_CONCEDE'
        : GamePrivilege(users=set(), notification="You are not allowed to start a concede vote"),
        'CAN_VOTE_MUTE'
        : GamePrivilege(users=set(), notification="You are not allowed to start a mute vote"),
        'CAN_VOTE_NEXT_MAP'
        : GamePrivilege(users=set(), notification="You are not allowed to start a nextmap vote"),
        'CAN_VOTE_MAP'
        : GamePrivilege(users=set(), notification="You are not allowed to start a map vote"),
        'CAN_VOTE_RESTART'
        : GamePrivilege(users=set(), notification="You are not allowed to start a restart vote"),
        'CAN_VOTE_DRAW'
        : GamePrivilege(users=set(), notification="You are not allowed to start a draw vote"),
        'CAN_VOTE_SHUFFLE'
        : GamePrivilege(users=set(), notification="You are not allowed to start a shuffle vote"),
        'CAN_VOTE_SWAP_BASE'
        : GamePrivilege(users=set(), notification="You are not allowed to start a swapbase vote"),
        'CAN_VOTE_EVEN'
        : GamePrivilege(users=set(), notification="You are not allowed to start an even vote"),
        'CAN_VOTE_SWITCH_TEAM'
        : GamePrivilege(users=set(), notification="You are not allowed to start a switchteam vote"),
        'CAN_VOTE_MOVE_SPEC'
        : GamePrivilege(users=set(), notification="You are not allowed to start a movespec vote"),
        'CAN_VOTE_NO_COMM'
        : GamePrivilege(users=set(), notification="You are not allowed to start a nocomm vote"),
        'CAN_VOTE_COMMLESS_MODE'
        : GamePrivilege(users=set(), notification="You are not allowed to start a commless vote"),
        'CAN_VOTE_RULESET'
        : GamePrivilege(users=set(), notification="You are not allowed to start a ruleset vote"),

        'CAN_JOIN_CLAN'
        : GamePrivilege(users=set(), notification="You are not allowed to join a clan"),
        'CAN_MANAGE_CLAN'
        : GamePrivilege(users=set(), notification="You are not allowed to manage a clan"),
        'CAN_LEAVE_CLAN'
        : GamePrivilege(users=set(), notification="You are not allowed to leave from a clan"),
    }

    @staticmethod
    def init_credentials():
        PermissionsContext.AUTH_SERVER_CREDENTIALS = f"Basic %s" % str(base64.b64encode(
            bytes(PermissionsContext.AUTH_SERVER_ID + ':' + str(PermissionsContext.AUTH_SERVER_TOKEN), 'utf-8')),
            'utf-8')
        PermissionsContext.update_privileges()

    # todo: Sync updating of the Roles using api-callback (svr_apiToken)
    #       currently update happens only during the change of the map
    @staticmethod
    def update_privileges():
        version = PermissionsContext.get_remote_privileges_version()
        log.info(f"Privileges is sync required: {version != PermissionsContext.PRIVILEGES_VERSION}; "
                 f"local-id: {PermissionsContext.PRIVILEGES_VERSION}, remote-id: {version}")
        if version != PermissionsContext.PRIVILEGES_VERSION:
            ar = PermissionsContext.get_authorities()
            if ar is not None:
                PermissionsContext.reset_game_privileges()
                PermissionsContext.PRIVILEGES_VERSION = version

                for p, gp in PermissionsContext.GAME_PRIVILEGES.items():
                    for data in ar.data:
                        if data.role.startswith(PermissionsContext.PRIVILEGES_EXCLUDE_PREFIX):
                            continue
                        for privilege in data.privileges:
                            if p == privilege:
                                gp.users = gp.users.union(data.users)

                # apply EXCLUDE
                for data in ar.data:
                    if data.role.startswith(PermissionsContext.PRIVILEGES_EXCLUDE_PREFIX):
                        privilege = data.role.replace(PermissionsContext.PRIVILEGES_EXCLUDE_PREFIX, '')
                        if privilege in PermissionsContext.GAME_PRIVILEGES:
                            PermissionsContext.GAME_PRIVILEGES[privilege].users \
                                = PermissionsContext.GAME_PRIVILEGES[privilege].users - data.users

                log.info(f"Privileges are synchronized: "
                         f"local-id: {PermissionsContext.PRIVILEGES_VERSION}, remote-id: {version}")

    @staticmethod
    def get_remote_privileges_version() -> int:
        request = urllib.request.Request(PermissionsContext.URL_AUTHORITIES_VERSION)
        request.add_header('Content-Type', 'application/json')
        request.add_header('Authorization', PermissionsContext.AUTH_SERVER_CREDENTIALS)
        try:
            response = urllib.request.urlopen(request, context=ssl.create_default_context())
            resp_data = json.loads(response.read())
            return int(resp_data['version'])
        except:
            sh_custom_utils.get_and_log_exception_info()

    @staticmethod
    def get_authorities() -> AuthRequest:
        request = urllib.request.Request(PermissionsContext.URL_AUTHORITIES_USERS)
        request.add_header('Content-Type', 'application/json')
        request.add_header('Authorization', PermissionsContext.AUTH_SERVER_CREDENTIALS)
        try:
            response = urllib.request.urlopen(request, context=ssl.create_default_context())
            return AuthRequest(**json.loads(response.read()))
        except:
            sh_custom_utils.get_and_log_exception_info()

    @staticmethod
    def reset_game_privileges():
        for p, gp in PermissionsContext.GAME_PRIVILEGES.items():
            gp.users = set()

    @staticmethod
    def has_privilege(privilege: str, uid: int) -> bool:
        debug_template = f"sv_permissions -> has_privilege(privilege='{privilege}', uid={uid}) -> "

        if not PermissionsContext.GAME_PRIVILEGES_ARE_ENABLED:
            log.debug(f'{debug_template}[{True}]')
            return True

        gp = PermissionsContext.GAME_PRIVILEGES[privilege]
        if not gp.enabled:
            log.debug(f'{debug_template}[{True}]')
            return True

        if uid in gp.users:
            log.debug(f'{debug_template}[{True}]')
            return True
        else:
            if gp.notify_user:
                client_index = server.GetIndexFromUID(uid)
                server.Notify(client_index, gp.notification)
            log.debug(f'{debug_template}[{False}]')
            return False

    # Temp API for the testing period
    @staticmethod
    def disable_privileges():
        PermissionsContext.GAME_PRIVILEGES_ARE_ENABLED = False

    @staticmethod
    def enable_privileges():
        PermissionsContext.GAME_PRIVILEGES_ARE_ENABLED = True

    @staticmethod
    def get_roles(client_index: int, uid: int):
        server.Notify(client_index, f'^gList ^gof ^gRoles ^gfor ^y{uid}\n')
        for privilege_name, gp in PermissionsContext.GAME_PRIVILEGES.items():
            privilege = '^gON' if int(uid) in gp.users else '^900OFF'
            server.Notify(client_index, f'^c{privilege_name}: {privilege}\n')
