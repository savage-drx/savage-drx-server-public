# ---------------------------------------------------------------------------
#           Name: sv_messaging.py
#    Description: Processing messages from sv_events
# ---------------------------------------------------------------------------

import json
# External modules
import os
import re
import shutil
from time import strftime, localtime

import core
# Savage API
import server

import sh_custom_utils
import sh_executor
import sh_io
import sh_logger as log
import sv_bans
import sv_discord
import sv_maps
import sv_module_reloading
import sv_utils
import sv_votes_processor
from sv_permissions import PermissionsContext as pc


class MessageSettings:
    # Accessible UIDS for admin stuff
    PYTHON_ADMIN_IDS = list(
        [int(i) for i in json.loads(python_config.get('Python_Referees', 'PYTHON_ADMIN_IDS'))])
    # Accessible UIDS for 3rd party REF stuff
    PYTHON_REF_IDS = list([int(i) for i in json.loads(python_config.get('Python_Referees', 'PYTHON_REF_IDS'))])
    # Will replace all symbols from the input string that are not: ':.?!0-9A-Za-z-_() /'
    REGEX_FOR_INPUT = '[^:.?!0-9A-Za-z\-_()@ /]'
    # Will replace all symbols from the name that are not: '0-9A-Za-z-_() '
    REGEX_FOR_NAME = '[^0-9A-Za-z\-_()# ]'
    # Requests that are like !help. Skips single and multiple "!" symbols
    REGEX_FOR_REQUEST = "^(![a-zA-Z0-9 ._()#-]+)$"
    # Date format
    DATE_FORMAT = "%Y.%m.%d - %H:%M:%S"

    MSG_TYPE_GLOBAL = "global"
    MSG_TYPE_TEAM = "team"
    MSG_TYPE_SQUAD = "squad"
    MSG_TYPE_SELECTED = "selected"

    SERVER_URL = python_config.get('Python_General', 'SERVER_URL')
    DISCORD_URL = python_config.get('Python_General', 'DISCORD_URL')
    IS_CHAT_BAN_ENABLED = python_config.getboolean('Python_Bans', 'IS_CHAT_BAN_ENABLED')

    ALLOWED = 1
    FORBIDDEN = 0

    @staticmethod
    def init_banned_words() -> set:
        lines = set()
        if python_config.getboolean('Python_Bans', 'IS_CHAT_BAN_ENABLED', fallback=False):
            banned_words_file_name = python_config.get('Python_Bans', 'BANNED_WORDS_FILE_NAME')
            initial_file_path = f"./config/{banned_words_file_name}"
            persistent_file_path = f"{core.CvarGetString('homedir')}/data/{banned_words_file_name}"

            # check if it's a first run and there is no banned_words.cfg inside the HOST folder then copy it
            if os.path.isfile(initial_file_path) and not os.path.isfile(persistent_file_path):
                shutil.copyfile(initial_file_path, os.path.join(persistent_file_path))

            with open(persistent_file_path) as f:
                for line in set([c.strip() for c in f.readlines()]):
                    if line != '' and not line.startswith(('#', ';')):
                        lines.add(line)
        return lines

    BANNED_WORDS = init_banned_words.__func__()


# message_type: global, team, squad, selected
def process_chat_message(client_index, message_type, message):
    uid = server.GetClientInfo(client_index, INFO_UID)
    client_name = server.GetClientInfo(client_index, INFO_NAME)
    team = int(server.GetClientInfo(client_index, INFO_TEAM))

    try:
        # Logging a message to the file
        client_name = re.sub(MessageSettings.REGEX_FOR_NAME, '', client_name)
        client_message = sh_custom_utils.clear_clans_and_colors(message)

        # Remove spaces from the end of the string
        message = message.rstrip()

        if message == "Reason:":
            return MessageSettings.ALLOWED
        if '^clan' in message and not pc.has_privilege('CAN_CHAT_WITH_ICONS', uid):
            return MessageSettings.FORBIDDEN

        # Prettify log messages:
        message_type = message_type.lower()

        msg_type = "[?] "
        if message_type == MessageSettings.MSG_TYPE_GLOBAL:
            if not pc.has_privilege('CAN_CHAT_GLOBAL', uid):
                return MessageSettings.FORBIDDEN
            msg_type = f"[{MessageSettings.MSG_TYPE_GLOBAL.upper()}]  "

        if message_type == MessageSettings.MSG_TYPE_TEAM:
            if team > 0 and not pc.has_privilege('CAN_CHAT_GLOBAL', uid):
                return MessageSettings.FORBIDDEN
            if team == 0 and not pc.has_privilege('CAN_CHAT_SPECS', uid):
                return MessageSettings.FORBIDDEN
            msg_type = f"[{MessageSettings.MSG_TYPE_TEAM.upper()}]    "

        if message_type == MessageSettings.MSG_TYPE_SQUAD:
            if not pc.has_privilege('CAN_CHAT_GLOBAL', uid):
                return MessageSettings.FORBIDDEN
            msg_type = f"[{MessageSettings.MSG_TYPE_SQUAD.upper()}]   "

        if message_type == MessageSettings.MSG_TYPE_SELECTED:
            if not pc.has_privilege('CAN_CHAT_GLOBAL', uid):
                return MessageSettings.FORBIDDEN
            msg_type = f"[{MessageSettings.MSG_TYPE_SELECTED.upper()}]"

        msg_sub = re.sub(MessageSettings.REGEX_FOR_INPUT, '', client_message)
        if msg_sub:
            msg = f'{msg_type} [{strftime(MessageSettings.DATE_FORMAT, localtime())}]   {client_name}: {msg_sub}'
            sh_io.save_to_file("general_chat", msg)
            log.chat(f"({message_type}) {client_name}: {msg_sub}")
    except:
        sh_custom_utils.get_and_log_exception_info()

    request = GameCommandRequest(client_index, uid, client_name, message)

    if request.is_request():
        sh_io.save_to_file("requests", request.message_for_log)
        sh_executor.submit_task(request.process_request)
        return MessageSettings.FORBIDDEN

    # send discord messages only from global chat
    if message_type == MessageSettings.MSG_TYPE_GLOBAL and sv_discord.DiscordSettings.DISCORD_IS_ENABLED:
        if not pc.has_privilege('CAN_CHAT_DISCORD', uid):
            return MessageSettings.FORBIDDEN
        sv_discord.check_and_send_message_to_discord(uid, client_name, message)

    # processing of the BANNED_WORDS should not interrupt logging and publishing of the messages
    process_banned_words(client_index, client_name, message)

    return MessageSettings.ALLOWED


def process_private_message(sender_idx, receiver_idx, message):
    uid = server.GetClientInfo(sender_idx, INFO_UID)
    if not pc.has_privilege('CAN_CHAT_PRIVATE', uid):
        return MessageSettings.FORBIDDEN

    try:
        # Logging a message to the file
        sender_name = re.sub(MessageSettings.REGEX_FOR_NAME, '', server.GetClientInfo(sender_idx, INFO_NAME))
        receiver_name = re.sub(MessageSettings.REGEX_FOR_NAME, '', server.GetClientInfo(receiver_idx, INFO_NAME))
        logged_message = sh_custom_utils.clear_clans_and_colors(message)

        msg_sub = re.sub(MessageSettings.REGEX_FOR_INPUT, '', logged_message)
        msg = '[PRIVATE] [%s]   %s --> %s: %s' % (
            strftime(MessageSettings.DATE_FORMAT, localtime()), sender_name, receiver_name, msg_sub)
        sh_io.save_to_file("private_chat", msg)
        log.chat("%s  %s --> %s: %s" % ("(msg)", sender_name, receiver_name, msg_sub))

        process_banned_words(sender_idx, sender_name, message)
    except:
        sh_custom_utils.get_and_log_exception_info()

    return MessageSettings.ALLOWED


class GameCommandRequest:
    def __init__(self, client_index, uid, name, message):
        self.client_index = client_index
        self.uid = uid
        self.name = name
        self.message = message

        self.REQUEST_PREFIX = "!"
        self.REGEX_FOR_REQUEST = "^(%s[a-zA-Z0-9 ._()\#\-\!\:\*/]+)$" % self.REQUEST_PREFIX
        self.REQUEST_PATTERN = re.compile(self.REGEX_FOR_REQUEST)
        self.REGEX_FOR_NAME = '[^0-9A-Za-z\-_() ]'
        self.REGEX_FOR_INPUT = '[^:.?!0-9A-Za-z\-_()@ /]'
        self.DATE_FORMAT = "%Y.%m.%d - %H:%M:%S"

        self.REQUEST_PARAM_REQUIRED = True
        self.NO_REQUEST_PARAMS = False

        # todo: old and ugly implementation of the list of arguments but as is...
        # Format: [(lambda), flag for required params]
        self.GLOBAL_COMMANDS = {
            'help': [(lambda arr: notify_help(arr[0], self.uid)), self.NO_REQUEST_PARAMS],
            'discord': [(lambda arr: sv_discord.notify_discord_help(arr[0])), self.NO_REQUEST_PARAMS],
            'find': [(lambda arr: sv_discord.notify_found_discord_users(arr[0], arr[1])), self.REQUEST_PARAM_REQUIRED],
            'map': [(lambda arr: sv_maps.notify_map_status(arr[0], arr[1])), self.REQUEST_PARAM_REQUIRED]
        }

        self.REF_COMMANDS = {
        }

        self.ADMIN_COMMANDS = {
            'reload': [(lambda arr: sh_executor.submit_task(sv_module_reloading.reload_module, arr[0], arr[1])),
                       self.REQUEST_PARAM_REQUIRED],
            'reload-banned': [(lambda arr: sh_executor.submit_task(sv_bans.reload_banned, arr[0])),
                              self.NO_REQUEST_PARAMS],
            'list-banned': [(lambda arr: sh_executor.submit_task(sv_bans.list_banned, arr[0])),
                            self.NO_REQUEST_PARAMS],
            'ban-ip': [(lambda arr: sh_executor.submit_task(sv_bans.ban_ip, arr[0], arr[1])),
                       self.REQUEST_PARAM_REQUIRED],
            'unban-ip': [(lambda arr: sh_executor.submit_task(sv_bans.unban_ip, arr[0], arr[1])),
                         self.REQUEST_PARAM_REQUIRED],
            'camper': [(lambda arr: sv_votes_processor.ban_siege_camper(sv_utils.getIndexFromFullName(str(arr[1])))),
                       self.REQUEST_PARAM_REQUIRED],
            'unban-camper': [
                (lambda arr: sv_votes_processor.unban_siege_for_one(sv_utils.getIndexFromFullName(str(arr[1])))),
                self.REQUEST_PARAM_REQUIRED],
            'client': [(lambda arr: notify_client_info(arr[0], arr[1])), self.REQUEST_PARAM_REQUIRED],
            'set': [(lambda arr: core.CommandExec('set {} {}'.format(arr[1], arr[2]))), self.REQUEST_PARAM_REQUIRED],
            'get': [(lambda arr: server.Notify(self.client_index, f'{arr[1]}: ' + str(core.CvarGetValue(f'{arr[1]}')))),
                    self.REQUEST_PARAM_REQUIRED],
            'roles-reload': [(lambda arr: sh_executor.submit_task(pc.update_privileges)), self.NO_REQUEST_PARAMS],
            'roles-disable': [(lambda arr: sh_executor.submit_task(pc.disable_privileges)), self.NO_REQUEST_PARAMS],
            'roles-enable': [(lambda arr: sh_executor.submit_task(pc.enable_privileges)), self.NO_REQUEST_PARAMS],
            'roles-get': [(lambda arr: sh_executor.submit_task(pc.get_roles, arr[0], arr[1])),
                          self.REQUEST_PARAM_REQUIRED],
        }

        self.MERGED_COMMANDS = {**self.GLOBAL_COMMANDS, **self.REF_COMMANDS, **self.ADMIN_COMMANDS}

        self.message_for_log = self._set_request_log_message()

    def process_request(self):
        try:
            if self.is_request():
                split = [x.lower() for x in self.message.split()]
                request_command = split[0].replace(self.REQUEST_PREFIX, '')
                request_params = [self.client_index] + split[1:]

                if request_command not in self.MERGED_COMMANDS:
                    server.Notify(self.client_index, '^yUnsupported ^yrequest: ^900%s' % request_command)
                    return

                if self.is_param_missing(request_command, request_params):
                    server.Notify(self.client_index, '^yRequest ^yparameter ^900is ^900missing!')
                    return

                if request_command in self.GLOBAL_COMMANDS:
                    self.GLOBAL_COMMANDS[request_command][0](request_params)

                if request_command in self.REF_COMMANDS and \
                        (self.uid in MessageSettings.PYTHON_REF_IDS or
                         self.uid in MessageSettings.PYTHON_ADMIN_IDS):
                    self.REF_COMMANDS[request_command][0](request_params)

                if request_command in self.ADMIN_COMMANDS and self.uid in MessageSettings.PYTHON_ADMIN_IDS:
                    self.ADMIN_COMMANDS[request_command][0](request_params)
        except:
            sh_custom_utils.get_and_log_exception_info()

    def is_request(self):
        return self.REQUEST_PATTERN.match(self.message)

    def is_param_missing(self, command, params):
        return len(params) < 2 and self.MERGED_COMMANDS[command][1]

    def _set_request_log_message(self):
        filtered_player_name = re.sub(self.REGEX_FOR_NAME, '', self.name)
        filtered_message = re.sub(self.REGEX_FOR_INPUT, '', self.message)
        return '[REQUEST] [%s]   %s: %s' % (strftime(self.DATE_FORMAT, localtime()), filtered_player_name,
                                            filtered_message)


def process_banned_words(client_index, client_name, message: str):
    if MessageSettings.IS_CHAT_BAN_ENABLED:
        uid = server.GetClientInfo(client_index, INFO_UID)
        message_filtered = message.lower().replace(" ", "").replace("-", "").replace("*", "").replace("_", "")
        for word in MessageSettings.BANNED_WORDS:
            if word.lower() in message_filtered or word.lower() in client_name:
                log.info(f"BAN_WORD: {word}, uid: {uid}, name: {client_name}")
                core.CommandExec(f"kick {client_index} reason offensive")


def notify_client_info(client_index: int, client: str):
    target_index = sv_utils.getIndexFromFullName(client)
    if target_index is None:
        server.Notify(client_index, f'^yNothing ^ywas ^yfound ^yfor ^yclient: ^900{client}')
    ip = server.GetClientInfo(target_index, INFO_CLIENTIP)
    log.info(f"Request client '{client}' ip: {ip}")
    server.Notify(client_index, f'^yClient "^y{client}": ^900{ip}')


def notify_help(client_index: int, uid: int):
    server.Notify(client_index, '')
    server.Notify(client_index, '^900|   ^900Community ^900Server ^900Information:\n')
    server.Notify(client_index, f'^900|   ^c{MessageSettings.SERVER_URL}\n')
    server.Notify(client_index, f'^900|   ^c{MessageSettings.DISCORD_URL}\n')
    server.Notify(client_index, '^900|   ^gPublic ^gcommands:\n')
    server.Notify(client_index, '^900| ^y!help, ^y!discord, ^y!map ^y<name>, ^y!find ^y<name>\n')

    if uid in MessageSettings.PYTHON_REF_IDS:
        server.Notify(client_index, '^900|   ^gRef ^gcommands:\n')
        server.Notify(client_index, '^900| ^y<empty>\n')

    if uid in MessageSettings.PYTHON_ADMIN_IDS:
        server.Notify(client_index, '^900|   ^gAdmin ^gcommands:\n')
        server.Notify(client_index, '^900| ^y!reload, ^y!camper, ^y!unban-camper, '
                                    '^y<msg>, ^y!reload-banned, ^y!ban-ip ^y<ip>, ^y!unban-ip ^y<ip> ^y!list-banned\n')
        server.Notify(client_index, '^900| ^y!set <cvar> <value>, ^y!get <cvar>, ^y!client <id>\n')
        server.Notify(client_index, '^900| ^y!roles-reload, ^y!roles-disable, ^y!roles-enable, ^yroles-get\n')

    server.Notify(client_index, '^900|   ^gCustom ^gvotes:\n')
    server.Notify(client_index, '^900| ^y/callvote ^ycustom ^ycamper ^y<PlayerName> ^y(bans ^yfrom ^yusing ^ysiege)\n')
    server.Notify(client_index, '^900| ^y/callvote ^ycustom ^yunban ^y<PlayerName> ^y(unbans ^yfrom ^yusing ^ysiege)\n')
    server.Notify(client_index, '^900| ^y/callvote ^ycustom ^youtcome ^y(blocks ^ydraw ^yvotes ^yfor ^y5 ^ymins)\n')
    server.Notify(client_index, '^900| ^y/callvote ^ycustom ^yapril-fools enable|disable ^y(toggles ^yboomerang ^yand '
                                '^yskullstack; ^yvote ^yis ^yavailable ^yin ^ythe ^ywarmup)\n')
    server.Notify(client_index, '^900| ^y/callvote ^ycustom ^yelect ^y<1-4> ^y<PlayerName> '
                                '^y(elect ^ya ^ycomm ^yfor ^ya ^yteam ^ynumber ^y(from ^y1 ^yto ^y4))\n')
    server.Notify(client_index, '^900| ^y/callvote ^ycustom ^ydisable-self-buffs ^y(turns ^yoff ^yself '
                                '^ybuffs ^yfor ^yone ^yround)\n')
    server.Notify(client_index, '^900| ^y/callvote ^ycustom ^yenable-self-buffs ^y(turns ^yon ^yself ^ybuffs)\n')
    server.Notify(client_index, '^900| ^y/callvote ^ycustom ^yenable-buff-pools ^y(turns ^yon ^ybuff ^ypools)\n')
    server.Notify(client_index, '^900| ^y/callvote ^ycustom ^ydisable-buff-pools ^y(turns ^yoff ^ybuff ^ypools)\n')
    # server.Notify(client_index, '^900| ^y/callvote ^ycustom ^yenable-bots ^y(turns ^yon ^ybots)')
    # server.Notify(client_index, '^900| ^y/callvote ^ycustom ^ydisable-bots ^y(turns ^yoff ^ybots)')
    server.Notify(client_index, '\n')
