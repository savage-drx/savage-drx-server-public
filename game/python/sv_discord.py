# -------------------------------------------------------------------------------------------------------
#          Name: sv_discord.py
#   Description: Communication between chat and discord channel
#
#   SSL:
#   https://stackoverflow.com/questions/55012726/discord-py-unable-to-get-certificate
#
#   lib version: discord.py 1.2.5
#   docs: https://discordpy.readthedocs.io
#
#   discord.Message:      author|content|channel|mention_everyone|mentions|id|attachments|raw_mentions|clean_content
#   discord.Client:       guilds|activity|users|get_channel(id)|get_guild(id)|get_user(id)
#                         get_all_channels()|get_all_members()
#   discord.User:         name|id|discriminator|avatar|bot|mention ex: "<@358270891299307521>"
#   discord.TextChannel:  name|guild|id|category_id|topic|position
#   discord.Guild:        name|id|description|channels|members|get_member(user_id)|
#                         get_member_named(name)
#   discord.Member:       id|activity|nick|status|mobile_status|desktop_status|web_status|is_on_mobile()
#   discord.Embed:        title|type|description|url|colour|footer|set_footer()|image|set_image()|
#                         thumbnail|set_thumbnail
#
#   support.discordapp.com/hc/en-us/articles/210298617-Markdown-Text-101-Chat-Formatting-Bold-Italic-Underline)?page=6
#   Code Formatting:      *Italics* or _Italics_
#                         **bold**
#                         ***bold italics***
#                         __underline__
#                         __*underline italics*__
#                         __**underline bold**__
#                         __***underline bold italics***__
#                          ~~Strikethrough~~
#                         `one line code blocks`
#                         ```multiple
#                               line code blocks```
#                         ```css
#                            multiple line code blocks with stated language```
#                         [text with links](http://url)
#                         [links references][1]  [1]: http://url
#                         Block Quotes is > or >>> followed by a space
# -------------------------------------------------------------------------------------------------------


import discord
import asyncio

import threading
import time
import re
import difflib as diff

import server
import core
import sv_defs
import sv_messaging
import sh_custom_utils
import sh_executor
import sh_logger as log
import sh_io
import emoji
import datetime
from sv_permissions import PermissionsContext as pc


# fix for: 'unknown encoding: idna'
import encodings.idna

# Global scope
discord_loop = asyncio.get_event_loop()
channel = None
users_cache = None
message_controller = None
last_message_id = None

client = discord.Client(loop=discord_loop, heartbeat_timeout=20, intents=discord.Intents.all())


class DiscordSettings:
    DISCORD_IS_ENABLED = python_config.getboolean('Python_Discord', 'DISCORD_IS_ENABLED', fallback=0)

    DISCORD_TOKEN = python_config.get('Credentials', 'DISCORD_TOKEN', fallback='')
    DISCORD_CHANNEL = python_config.getint('Python_Discord', 'DISCORD_CHANNEL', fallback='')
    DISCORD_GUILD_ID = python_config.getint('Python_Discord', 'DISCORD_GUILD_ID', fallback='')

    ADMIN_ID = python_config.getint('Python_Discord', 'DISCORD_ADMIN_ID', fallback=-1)

    DISCORD_USERNAME_REGEX = '^([0-9A-Za-z\-_ ()$.\[\]|!#])+$'
    DISCORD_MESSAGE_LIMIT_SIZE = 64
    DISCORD_MESSAGE_REGEX = '[^0-9A-Za-z\-_()$.,\'\"\[\]|!?@:/# ]'
    DISCORD_MESSAGE_REPLACE_BY = '*'
    DISCORD_MSG_DATE_FORMAT = "%a %H:%M:%S"
    DISCORD_INVALID_USER_NAME = "unknown"
    DISCORD_BOT_MESSAGE_FILTER = ["http", "https", "www", "//", ":/", "://"]

    GAME_MESSAGE_TIMEOUT = 5
    GAME_MESSAGE_DIFF_RATIO = 0.75
    GAME_CLAN_REGEX = "\^clan (\d+)\^"
    GAME_ANNOYING_ORANGE = " :annoyingOrange: "
    GAME_SERVER_CHAT_TEMPLATE = "chat ^clan 2^^222Discord^w^clan 2^> ^156{}: ^w{}"
    DISCORD_FOUND_USERS_LIMIT = 5
    LOG_DATE_FORMAT = "%Y.%m.%d - %H:%M:%S"


def init():
    try:
        log.info("Initializing Discord...")

        asyncio.get_child_watcher()

        global discord_loop
        discord_loop = asyncio.get_event_loop()

        thread = threading.Thread(target=discord_loop.run_forever)
        thread.start()

        asyncio.run_coroutine_threadsafe(client.connect(reconnect=True), discord_loop)
        asyncio.run_coroutine_threadsafe(client.login(token=DiscordSettings.DISCORD_TOKEN, bot=True), discord_loop)
    except:
        sh_custom_utils.get_and_log_exception_info()


def stop():
    log.info("Discord is stopping...")
    asyncio.run_coroutine_threadsafe(client.logout(), discord_loop)
    discord_loop.call_soon_threadsafe(discord_loop.stop)
    log.info("Discord has been successfully stopped")


def reconnect():
    log.info("Reconnecting discord...")
    client.clear()
    asyncio.run_coroutine_threadsafe(client.connect(reconnect=True), discord_loop)
    log.info("Discord reconnected.")


@client.event
async def on_ready():
    try:
        log.info("Discord bot has logged in as: %s, id: %s" % (client.user.name, client.user.id))

        global channel
        channel = client.get_channel(DiscordSettings.DISCORD_CHANNEL)

        global users_cache
        users_cache = DiscordUsersCache(client.users, DiscordSettings)
        log.info("Discord found %s users" % len(client.users))

        global message_controller
        message_controller = MessageController(DiscordSettings)

    except:
        sh_custom_utils.get_and_log_exception_info()

    log.info("Discord %s is ready: %s" % (discord.__version__, client.is_ready()))


@client.event
async def on_member_join(member):
    try:
        log.info("New user has joined discord: %s" % member.name)
        global users_cache
        users_cache = DiscordUsersCache(client.users, DiscordSettings)
    except:
        sh_custom_utils.get_and_log_exception_info()


@client.event
async def on_member_remove(member):
    try:
        log.info("User has been removed from discord: %s" % member.name)
        global users_cache
        users_cache = DiscordUsersCache(client.users, DiscordSettings)
    except:
        sh_custom_utils.get_and_log_exception_info()


@client.event
async def on_member_update(before, after):
    try:
        global users_cache
        users_cache = DiscordUsersCache(client.users, DiscordSettings)
    except:
        sh_custom_utils.get_and_log_exception_info()


@client.event
async def on_message(message):
    try:
        # bot must not reply to itself
        if not client.is_ready() or message.author == client.user:
            return

        # In case when we receive two same messages
        global last_message_id
        if last_message_id == message.id:
            last_message_id = message.id
            return
        last_message_id = message.id

        if message.channel.id == DiscordSettings.DISCORD_CHANNEL and DiscordSettings.DISCORD_IS_ENABLED\
                and message.clean_content:
            receive_message_from_discord(message)

            sh_io.save_to_file("from_discord", '[DISCORD] [%s]   %s: %s' %
                               (time.strftime(DiscordSettings.LOG_DATE_FORMAT, time.localtime()),
                                message.author.name, message.clean_content))

    except:
        sh_custom_utils.get_and_log_exception_info()


@client.event
async def on_message_delete(message):
    pass


@client.event
async def on_raw_message_delete(payload):
    pass


@client.event
async def on_message_edit(before, after):
    pass


@client.event
async def on_raw_message_edit(payload):
    pass


def send_message_to_discord(message):
    try:
        if client.is_ready():
            asyncio.run_coroutine_threadsafe(channel.send(message), discord_loop)
    except:
        sh_custom_utils.get_and_log_exception_info()


def send_embed_to_discord(embed):
    try:
        if client.is_ready():
            asyncio.run_coroutine_threadsafe(channel.send(embed=embed), discord_loop)
    except:
        sh_custom_utils.get_and_log_exception_info()


def receive_message_from_discord(message):
    try:
        if not client.is_ready() or MessageController.is_message_from_bot(message, DiscordSettings):
            return

        request = DiscordCommandRequest(message)
        if request.is_request():
            request.process_request()
            return

        formatted_messages = MessageController.format_discord_message(message, DiscordSettings)

        log_msg = '[DISCORD]  [%s]   %s: %s' % (time.strftime(DiscordSettings.LOG_DATE_FORMAT, time.localtime()),
                                                MessageController.get_name_from_message(message), message.clean_content)
        sh_io.save_to_file("general_chat", log_msg)

        for x in formatted_messages:
            server.Chat(x)

        log.chat("(discord): %s: %s" % (MessageController.get_name_from_message(message), message.clean_content))
    except:
        sh_custom_utils.get_and_log_exception_info()


def check_and_send_message_to_discord(uid, author, message):
    try:
        if not client.is_ready():
            return

        log.debug(uid)

        if DiscordSettings.DISCORD_IS_ENABLED and message_controller.is_message_valid_from_game(uid, message):
            message = message_controller.format_game_message(author, message, users_cache, uid)
            send_message_to_discord(message)
    except:
        sh_custom_utils.get_and_log_exception_info()


class MessageController:
    class User:
        def __init__(self, uid, message):
            self.uid = uid
            self.message = message
            self.time_sent = int(round(time.time()))

    def __init__(self, discord_settings):
        self.messaging = {}
        self.ds = discord_settings
        self.timeout_sec = self.ds.GAME_MESSAGE_TIMEOUT
        self.diff_ratio = self.ds.GAME_MESSAGE_DIFF_RATIO

    def is_message_valid_from_game(self, uid, message):
        message = message.strip().lower()
        # Reject empty messages
        if not message:
            return False

        if uid in self.messaging:
            now = int(round(time.time()))
            then = self.messaging[uid].time_sent

            diff_ratio = diff.SequenceMatcher(None, message, self.messaging[uid].message).ratio()
            diff_ratio = round(diff_ratio, 2)

            # updating latest message params
            self.messaging[uid].time_sent = now
            self.messaging[uid].message = message

            if diff_ratio >= self.diff_ratio:
                if now - then < self.timeout_sec:
                    return False

            return True

        else:
            self.messaging[uid] = self.User(uid, message)
            return True

    def reset(self):
        self.messaging = {}

    @staticmethod
    def format_discord_message(message, ds):
        formatted_message = re.sub(ds.DISCORD_MESSAGE_REGEX, ds.DISCORD_MESSAGE_REPLACE_BY,
                                   emoji.demojize(message.clean_content))
        formatted_message = SmilesFormatter.format_to_game(formatted_message)

        author_name = ds.DISCORD_INVALID_USER_NAME
        if message.author in users_cache.valid_users:
            author_name = MessageController.get_name_from_message(message)

        messages = [formatted_message[i:i + ds.DISCORD_MESSAGE_LIMIT_SIZE] for i in
                    range(0, len(formatted_message), ds.DISCORD_MESSAGE_LIMIT_SIZE)]

        if len(messages) > 1:
            messages = messages[:2]

        messages = list(map(lambda msg: ds.GAME_SERVER_CHAT_TEMPLATE.format(author_name, msg), messages))

        return messages

    @staticmethod
    def is_message_from_bot(message, ds):
        return any(word in message.content for word in ds.DISCORD_BOT_MESSAGE_FILTER)

    @staticmethod
    def format_game_message(author, message, discord_users_cache, uid):
        message = MessageController.clear_clans_and_colors(message)
        message = SmilesFormatter.format_from_game(message)

        header = "`%s` **%s**:" % (get_current_utc_timestamp(), author)
        content = message.split(" ")
        for idx, word in enumerate(content):
            if word.startswith("@") and len(word) > 1:
                if pc.has_privilege('CAN_CHAT_DISCORD', uid):
                    content[idx] = MessageController.format_mentioned_user(word, discord_users_cache)

        return "%s %s" % (header, " ".join(content))

    @staticmethod
    def format_mentioned_user(mentioned_user, discord_users_cache):
        # return substring without first symbol "@"
        substring = mentioned_user[1:]
        found = discord_users_cache.find_mentioned_users(substring)
        if len(found) == 1:
            return found[0].mention
        else:
            return mentioned_user

    @staticmethod
    def clear_clans_and_colors(body):
        body = re.sub("\^clan [0-9]{0,10}\^", " :smiley: ", body)
        body = re.sub("\^[a-z|A-Z]", "", body)
        body = re.sub("\^[0-9]{3}", "", body)
        body = body.strip()
        return body

    @staticmethod
    def get_name_from_message(message):
        name = str(message.author.name)
        nm = re.search(r'\d+$', name)
        if nm is not None:
            name = name.replace(nm.group(), '')
        return name


class DiscordUsersCache:
    def __init__(self, users, discord_settings):
        self.users = users
        self.ds = discord_settings
        self.requested_users = {}
        self.valid_users = []
        self.invalid_users = []

        name_pattern = re.compile(self.ds.DISCORD_USERNAME_REGEX)
        for user in self.users:
            if name_pattern.match(user.name):
                self.valid_users.append(user)
            else:
                self.invalid_users.append(user)

    def find_mentioned_users(self, substring):
        substring = substring.lower()

        if substring in self.requested_users:
            if self.requested_users[substring] is not None:
                return [self.requested_users[substring]]
            else:
                return []

        found_users = [u for u in self.valid_users if substring.lower() in u.name.lower()]

        if len(found_users) == 1:
            self.requested_users[substring] = found_users[0]
        else:
            self.requested_users[substring] = None

        return found_users

    def __str__(self):
        return "DiscordUsersCache users: %s, " \
               "valid_users: %s, " \
               "invalid_users: %s" \
               % (len(self.users),
                  len(self.valid_users),
                  len(self.invalid_users))


def _get_discord_user_status(user_id):
    guild = client.get_guild(DiscordSettings.DISCORD_GUILD_ID)
    if guild:
        member = guild.get_member(user_id)
        return member.status
    return ""


class DiscordChannelHistoryCache:
    def __init__(self, cached_channel, depth):
        self.cached_channel = cached_channel
        self.depth = depth
        self.messages = []
        self.first_split_message = None

    async def update(self):
        history = await self.cached_channel.history(limit=self.depth).flatten()
        self.messages = []
        for message in history:
            self.messages.append(message.clean_content)
        self.first_split_message = self.messages[0].split("\n")
        self.fix_message_color()
        log.info("DiscordChannelHistoryCache update: %s" % self)

    def fix_message_color(self):
        for idx, val in enumerate(self.first_split_message):
            self.first_split_message[idx] = val.replace(' ', '^y ')
            self.first_split_message[idx] = re.sub("\^.+ \^", '^y%s' % val, val)

            val_split = val.split()
            for split_idx, split_val in enumerate(val_split):
                val_split[split_idx] = '^y' + split_val

            self.first_split_message[idx] = " ".join(val_split)

    def __str__(self):
        return "DiscordChannelHistoryCache channel: %s, " \
               "depth: %s , " \
               "messages: %s, " \
               % (self.cached_channel.id,
                  self.depth,
                  len(self.messages))


class DiscordCommandRequest:
    def __init__(self, message):
        self.name = message.author.name
        self.message = message.content
        self.author_id = message.author.id

        self.REQUEST_PREFIX = "!"
        self.REGEX_FOR_REQUEST = "^(%s[a-zA-Z0-9 ._()#-]+)$" % self.REQUEST_PREFIX
        self.REQUEST_PATTERN = re.compile(self.REGEX_FOR_REQUEST)
        self.REGEX_FOR_INPUT = '[^:.?!0-9A-Za-z\-_()@ ]'
        self.DATE_FORMAT = "%Y.%m.%d - %H:%M:%S"

        self.GLOBAL_COMMANDS = {
            'help': (lambda x: send_help_to_discord()),
            'online': (lambda x: send_online_to_discord(True, 0)),
            'o': (lambda x: send_online_to_discord(True, 0)),
            'status': (lambda x: send_online_to_discord(True, 0))
        }

        self.ADMIN_COMMANDS = {
            'reconnect': (lambda x: reconnect()),
            'custom': (lambda x: exec_custom_command(x)),
            'exec': (lambda x: exec_custom_command(x))
        }

        self.message_for_log = self._set_request_log_message()

    def process_request(self):
        try:
            if self.is_request():
                split = [x.lower() for x in self.message.split()]
                request_command = split[0].replace(self.REQUEST_PREFIX, '')
                request_params = split[1:]

                if request_command in self.GLOBAL_COMMANDS:
                    self.GLOBAL_COMMANDS[request_command](request_params)

                if request_command in self.ADMIN_COMMANDS and self.author_id == DiscordSettings.ADMIN_ID:
                    self.ADMIN_COMMANDS[request_command](request_params)

        except:
            sh_custom_utils.get_and_log_exception_info()

    def is_request(self):
        return self.REQUEST_PATTERN.match(self.message)

    def _set_request_log_message(self):
        filtered_message = re.sub(self.REGEX_FOR_INPUT, '', self.message)
        return '[REQUEST] [%s]   %s: %s' % (time.strftime(self.DATE_FORMAT, time.localtime()), self.name,
                                            filtered_message)


def send_online_to_discord(extended, delay):
    if DiscordSettings.DISCORD_IS_ENABLED and client.is_ready():
        time.sleep(delay)
        state = ServerState()
        if extended:
            send_embed_to_discord(state.get_extended_embed_online())
        else:
            send_embed_to_discord(state.get_simple_embed_online())


def send_end_of_game_to_discord():
    if DiscordSettings.DISCORD_IS_ENABLED and client.is_ready():
        state = ServerState()
        send_embed_to_discord(state.get_end_of_game_embed())


def send_nextmap_to_discord(delay):
    if DiscordSettings.DISCORD_IS_ENABLED and client.is_ready():
        time.sleep(delay)
        state = ServerState()
        send_embed_to_discord(state.get_nextmap_embed())


def send_help_to_discord():
    pass


def exec_custom_command(command):
    str_command = "!" + " ".join(command)
    request = sv_messaging.GameCommandRequest(-1, 2, "drk", str_command)
    if request.is_request():
        sh_io.save_to_file("requests", request.message_for_log)
        sh_executor.submit_task(request.process_request)


def exec_core_command(command):
    str_command = " ".join(command)
    core.CommandExec(str_command)


def notify_found_discord_users(client_index, substring):
    if not DiscordSettings.DISCORD_IS_ENABLED and not client.is_ready():
        server.Notify(client_index, "^yDiscord ^yis ^900not ^yworking ^ynow.")
        return

    found_users = users_cache.find_mentioned_users(substring)
    if len(found_users) == 0:
        server.Notify(client_index, f"^gHaven't ^gfound ^gany ^guser ^gby ^g'^156{substring}^g'.")
    elif len(found_users) == 1:
        server.Notify(client_index, f"^gFound: ^g'^156{found_users[0].name}^g', "
                                    f"status: ^y{_get_discord_user_status(found_users[0].id)}")
    elif len(found_users) <= DiscordSettings.DISCORD_FOUND_USERS_LIMIT:
        result = "^gFound ^y%s ^gusers: " % len(found_users)
        for user in found_users:
            result += ", '^156%s' ^w[^y%s^w]" % (user.name, _get_discord_user_status(user.id))
        server.Notify(client_index, result)
    else:
        server.Notify(client_index, "^gFound ^gtoo ^gmuch ^gusers ^gby '^156%s'. ^gPlease ^gspecify ^gyour ^grequest."
                      % substring)


def notify_discord_help(client_index):
    if not DiscordSettings.DISCORD_IS_ENABLED and not client.is_ready():
        server.Notify(client_index, "^yDiscord ^yis ^900not ^yworking ^ynow.")
        return

    server.Notify(client_index, '')
    server.Notify(client_index, '^900|   ^900Discord ^900Information:')
    server.Notify(client_index, '^900|   ^w^clan 87151^^222Discord^w^clan 87151^ ^yURL: ^btinyurl.com/xrdiscord"')
    server.Notify(client_index, '^900|   ^900General ^900messaging:')
    server.Notify(client_index, '^900| ^yAll ^ymessages ^yfrom ^ythe ^gGENERAL ^ychat ^yare '
                                '^ybeing ^ysent ^yto ^ydiscord')
    server.Notify(client_index, '^900| ^yMessages ^yfrom ^gTEAM/SPEC ^ychats ^yare ^gIGNORED')
    server.Notify(client_index, '^900| ^yMessages ^gFROM ^ydiscord ^yare ^ylimited ^yby ^g%s ^ysymbols.'
                  % DiscordSettings.DISCORD_MESSAGE_LIMIT_SIZE)
    server.Notify(client_index, '^900| ^yDiscord ^ynames ^ywith ^ythe ^yforbidden ^ysymbols ^ywill ^ybe ^yprinted ^yas '
                        '^y"unknown"')
    server.Notify(client_index, '^900|   ^900Commands:')
    server.Notify(client_index, '^900| ^yYou ^ycan ^ysend ^ya ^ymessage ^ywith ^ythe ^ymentioned ^gdiscord ^yuser')
    server.Notify(client_index, '^900| ^yType ^g"@user ^gtext" ^yto ^yinclude ^ymentioned ^ydiscord ^yuser')
    server.Notify(client_index, '^900| ^yFind ^ya ^gdiscord ^yuser ^yby ^g"!find ^guser" ^ycommand')
    server.Notify(client_index, '^900| ^gREMEMBER: ^ythere ^yis ^yno ^yneed ^yto ^ytype ^ythe ^ywhole ^gdiscord '
                        '^yusername ^yinside ^g"@name ^gtext".'
                        ' ^yIt ^yis ^yenough ^yto ^yspecify ^gUNIQUE ^ypart ^yof ^ythe ^yname.')
    server.Notify(client_index, '^900| ^yEx.: ^g"@first ^gtext" ^ywill ^ysend ^ythe ^ysame ^yas '
                                '^g"@XR_FirstTimePlayer ^gtext"')
    server.Notify(client_index, '^900| ^yTechnical ^ynotice: ^ycurrent ^ydiscord ^yuserlist '
                                '^yis ^yupdated ^yonce ^ya ^yday')
    server.Notify(client_index, '')


def get_current_utc_timestamp():
    return str(datetime.datetime.now(datetime.timezone.utc).strftime(DiscordSettings.DISCORD_MSG_DATE_FORMAT))


class SmilesFormatter:
    GAME_TO_DISCORD = {
        ":D": ":smiley:",
        "8(": ":flushed:",
        "o_O": ":flushed:",
        "O_o": ":flushed:",
        "o_o": ":flushed:",
        "O_O": ":flushed:",
        ":O": ":dizzy_face:",
        ":P": ":stuck_out_tongue_winking_eye:",
        ":p": ":stuck_out_tongue_winking_eye:",
        ">:)": ":satisfied:",
        ">:D": ":satisfied:",
        "8)": ":sunglasses:",
        ":()": ":monkey_face:",
        ":(": ":frowning:",
        "xD": ":grinning:",
        ":C": ":fearful:",
        ":X": ":no_mouth:",
        ":x": ":no_mouth:",
        ";)": ":wink:",
        ":S": ":confused:",
        ":|": ":neutral_face:",
        ":I": ":neutral_face:",
        ":)": ":slight_smile:"
    }

    DISCORD_TO_GAME = {
        ":grinning:": ":D",
        ":smiley:": ":D",
        ":flushed:": "o_O",
        ":dizzy_face:": ":O",
        ":scream:": ":O",
        ":stuck_out_tongue_winking_eye:": ":P",
        ":satisfied:": ">:)",
        ":sunglasses:": "8)",
        ":monkey_face:": ":()",
        ":anguished:": ":(",
        ":disappointed:": ":(",
        ":frowning:": ":(",
        ":laughing:": "xD",
        ":grinning_face_with_smiling_eyes:": "xD",
        ":fearful:": ":C",
        ":no_mouth:": ":X",
        ":wink:": ";)",
        ":confused:": ":S",
        ":neutral_face:": ":|",
        ":slight_smile:": ":)",
        ":bowtie:": ":|",
        ":kissing_closed_eyes:": ":|",
        ":kissing_smiling_eyes:": ":)",
        ":expressionless:": ":|",
        ":cold_sweat:": ":(",
        ":astonished:": ":O",
        ":rage:": "^y^clan 76891^",
        ":relaxed:": ":)",
        ":stuck_out_tongue:": ":P",
        ":open_mouth:": ":O",
        ":unamused:": ":|",
        ":pensive:": ":(",
        ":persevere:": ":(",
        ":triumph:": ":|",
        ":heart:": "",
        ":smirk:": ":)",
        ":relieved:": ":)",
        ":stuck_out_tongue_closed_eyes:": ":P",
        ":sleeping:": ":)",
        ":grimacing:": "8)",
        ":sweat_smile:": ":D",
        ":cry:": ":C",
        ":neckbeard:": ":)",
        ":sleepy:": ":|",
        ":heart_eyes:": ":D",
        ":worried:": ":(",
        ":sweat:": ":|",
        ":confounded:": ":C",
        ":sob:": ":C",
        ":tired_face:": ":C",
        ":yum:": ":P",
        ":blush:": ":)",
        ":kissing_heart:": ":)",
        ":grin:": "8)",
        ":kissing:": ":)",
        ":hushed:": ":(",
        ":disappointed_relieved:": ":(",
        ":joy:": ":D",
        ":angry:": ":("
    }

    EMOJI_REGEX = ':[A-Za-z_0-9]+:'

    @staticmethod
    def format_to_game(message):
        for i, j in SmilesFormatter.DISCORD_TO_GAME.items():
            message = message.replace(i, j)
        return re.sub(SmilesFormatter.EMOJI_REGEX, ":)", message)

    @staticmethod
    def format_from_game(message):
        for i, j in SmilesFormatter.GAME_TO_DISCORD.items():
            message = message.replace(i, j)
        return message


class ServerState:
    MAP_THUMBNAIL_URL_BIG_TEMPLATE = "https://savagedrx.com/public/world/%s_overhead.jpg"
    XR_ICON_URL = "https://sav1maps.savagedrx.com/public/savagexr_logos_icons/savagexr_icon_64.png"
    WARNING_ICON_URL = "http://www.stickpng.com/assets/images/5a81af7d9123fa7bcc9b0793.png"
    EMBED_COLOR = 0xe44407
    EMBED_COLOR_START = 0x347013
    EMBED_COLOR_END_GAME = 0xe11107
    EMBED_COLOR_NEXTMAP = 0xe99907

    class Team:
        def __init__(self, team_id):
            self.team_id = team_id
            self.team_name = ""
            self.race = sv_defs.teamList_RaceName[team_id]
            self.players = {}
            self.embed_players = ""
            self.commander = {"name": "---"}
            self.set_team_name()

        def set_team_name(self):
            if self.team_id == 0:
                self.team_name = "Spectators"
            else:
                self.team_name = "Team %s" % self.team_id

        def __str__(self):
            return "Team name: %s, id: %s, race: %s, commander: %s, players: %s" % \
                   (self.team_name, self.team_id, self.race, self.commander, self.players)

    def __init__(self):
        self.server_name = ServerState.clean_game_colors(core.CvarGetString('svr_name'))
        self.map_name = core.CvarGetString('world_name')
        self.map_info = {}
        self.teams = {}
        self.online = 0
        self.commanders = []
        self.winner_team = 0
        self.init_teams()
        self.init_online()
        self.init_map_info()
        self.init_end_of_game_info()

    def init_teams(self):
        for i in range(int(core.CvarGetString('sv_numTeams'))):
            self.teams[i] = ServerState.Team(i)
        # fill teams with players
        for client_index in range(MAX_CLIENTS):
            # Ignore inactive Client Slots and Bots
            if server.GetClientInfo(client_index, INFO_ACTIVE) and not sv_defs.clientList_Bot[client_index]:
                team_id = sv_defs.objectList_Team[client_index]
                # add commander
                if client_index == sv_defs.teamList_Commander[team_id]:
                    self.teams[team_id].commander["client_index"] = client_index
                    self.teams[team_id].commander["name"] = server.GetClientInfo(client_index, INFO_NAME)
                # add player
                self.teams[team_id].players[client_index] = server.GetClientInfo(client_index, INFO_NAME)

    def init_online(self):
        for key, value in self.teams.items():
            self.online += len(value.players)
            if key != 0:
                self.commanders.append(value.commander["name"])
            i = 1
            for k, v in value.players.items():
                if v in self.commanders:
                    value.embed_players += str(i) + ". **[C] " + v + "**\n"
                else:
                    value.embed_players += str(i) + ". " + v + "\n"
                i += 1
            value.embed_players = value.embed_players.rstrip()
            if not value.embed_players:
                value.embed_players = "---"

    def init_map_info(self):
        pass
        # self.map_info = sv_stats.get_map_info_from_cache(self.map_name)

    def init_end_of_game_info(self):
        self.winner_team = server.GetGameInfo(GAME_WINTEAM)

    @staticmethod
    def clean_game_colors(body):
        body = re.sub("\^[a-z|A-Z]", "", body)
        return re.sub("\^[0-9]{3}", "", body)

    def get_simple_embed_online(self):
        embed = discord.Embed()
        embed.color = ServerState.EMBED_COLOR_START

        embed.set_author(name=self.server_name, icon_url=ServerState.XR_ICON_URL)
        embed.set_thumbnail(url=ServerState.MAP_THUMBNAIL_URL_BIG_TEMPLATE % self.map_name)

        embed.description = "```World:  %s" \
                            "\nOnline: %s player(s)" \
                            "\nComms:  %s" \
                            "\nTime:   %s```" % \
                            (self.map_name,
                             self.online,
                             " vs ".join(self.commanders),
                             get_current_utc_timestamp())

        embed.set_footer(text="Type !online (!o) to see actual server status", icon_url=ServerState.WARNING_ICON_URL)
        return embed

    def get_extended_embed_online(self):
        embed = discord.Embed()
        embed.color = ServerState.EMBED_COLOR

        embed.set_author(name=self.server_name, icon_url=ServerState.XR_ICON_URL)
        embed.set_thumbnail(url=ServerState.MAP_THUMBNAIL_URL_BIG_TEMPLATE % self.map_name)

        embed.description = "```World:  %s" \
                            "\nOnline: %s player(s)" \
                            "\nTime:   %s```" % \
                            (self.map_name,
                             self.online,
                             get_current_utc_timestamp())

        embed.add_field(name=self.teams[1].team_name, value=self.teams[1].embed_players, inline=True)
        embed.add_field(name=self.teams[2].team_name, value=self.teams[2].embed_players, inline=True)
        if 3 in self.teams:
            embed.add_field(name=self.teams[3].team_name, value=self.teams[3].embed_players, inline=True)
        if 4 in self.teams:
            embed.add_field(name=self.teams[4].team_name, value=self.teams[4].embed_players, inline=True)
        embed.add_field(name=self.teams[0].team_name, value=self.teams[0].embed_players, inline=True)

        embed.set_footer(text="Type !online (!o) to see actual server status", icon_url=ServerState.WARNING_ICON_URL)

        return embed

    def get_end_of_game_embed(self):
        embed = discord.Embed()
        embed.color = ServerState.EMBED_COLOR_END_GAME

        embed.set_author(name=self.server_name, icon_url=ServerState.XR_ICON_URL)
        embed.set_thumbnail(url=ServerState.MAP_THUMBNAIL_URL_BIG_TEMPLATE % self.map_name)

        winner = "Result: draw"
        if self.winner_team != 0:
            winner = "Result: winner %s" % self.teams[self.winner_team].team_name

        embed.description = "```World:  %s" \
                            "\n%s" \
                            "\nTime:   %s```" % \
                            (self.map_name, winner, get_current_utc_timestamp())

        embed.add_field(name=self.teams[1].team_name, value=self.teams[1].embed_players, inline=True)
        embed.add_field(name=self.teams[2].team_name, value=self.teams[2].embed_players, inline=True)
        if 3 in self.teams:
            embed.add_field(name=self.teams[3].team_name, value=self.teams[3].embed_players, inline=True)
        if 4 in self.teams:
            embed.add_field(name=self.teams[4].team_name, value=self.teams[4].embed_players, inline=True)

        return embed

    def get_nextmap_embed(self):
        embed = discord.Embed()
        embed.color = ServerState.EMBED_COLOR_NEXTMAP

        embed.set_author(name=self.server_name, icon_url=ServerState.XR_ICON_URL)
        embed.set_thumbnail(url=ServerState.MAP_THUMBNAIL_URL_BIG_TEMPLATE % self.map_name)

        embed.description = "```Nextmap: %s" \
                            "\nOnline:  %s player(s)" \
                            "\nTime:    %s```" % \
                            (self.map_name, self.online, get_current_utc_timestamp())

        return embed

    def __str__(self):
        return "Server name: %s , map: %s, online: %s" % (self.server_name, self.map_name, self.online)
