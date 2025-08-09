# ---------------------------------------------------------------------------
#           Name: sv_defs.py
#         Author: Anthony Beaucamp (aka Mohican)
#    Description: Server-side Global Definitions
# ---------------------------------------------------------------------------

import builtins

# System Information
global gameTime

# Object Data Lists (see server.GetObjectList())
global objectList_Active    # Is Object active?
global objectList_Team      # Which Team does the Object belong to?
global objectList_Type      # What Type of Object? (see OBJTYPE_***)
global objectList_Name      # Name of Object (ex: 'human_nomad')
global objectList_Health    # Object's Health Point
global objectList_MaxHealth # Object's Max Health Point
global objectList_Construct # Is Object under construction? (only applies to Buildings)
global objectList_Last      # Index of last Object

# Client Data Lists (also correspond to index 0-127 of object list above, see server.GetClientList())
global clientList_Active     # Is Client Active? (Different than objectList_Active above)
global clientList_Bot        # Is Client a Bot?
global clientList_Team       # Client's Team
global clientList_Officer    # Is Client an Officer?
global clientList_Squad      # Squad that Client belongs to
global clientList_Charge     # Client's Weapon Charge Status (%)
global clientList_Mana       # Client's Mana Points
global clientList_MaxMana    # Client's Max Mana Points
global clientList_Health     # Client's Health Points
global clientList_MaxHealth  # Client's Max Health Points
global clientList_Stamina    # Client's Stamina Points
global clientList_MaxStamina # Client's Max Stamina Points

# Team Data Lists (see server.GetTeamList())
global teamList_Base      # Index of Team's Base (Stronghold/Lair)
global teamList_Commander # Index of Team's Commander
global teamList_RaceName  # Team's Race Name (ex: human)
global teamList_RaceDesc  # Team's Race Description (ex: The Beast Horde)
global teamList_Missions  # Squad Missions of each Team
global teamList_Last      # Index of last Team

# Game Information Types (see server.GetGameInfo())
builtins.GAME_TIME = 0       # Game Time (in msec)
builtins.GAME_STATE = 1      # Game State (see sv_events.py)
builtins.GAME_WINTEAM = 2    # Last Winner Team

# Client Information Types (see server.GetClientInfo())
builtins.INFO_ACTIVE = 0       # Is Client active?
builtins.INFO_TEAM = 1         # Client's Team
builtins.INFO_NAME = 2         # Client's Name
builtins.INFO_UID = 3          # Client's UID
builtins.INFO_GUID = 4         # Client's GUID (deprecated)
builtins.INFO_CLANID = 5       # Client's CLANID
builtins.INFO_STATUS = 6       # Client's status
builtins.INFO_TYPING = 7       # Is Client typing?
builtins.INFO_REFEREE = 8      # Is Client referee?
builtins.STAT_DEATHS = 9       # Client's deaths
builtins.STAT_KILLS = 10       # Client's kills
builtins.STAT_KILLSTREAK = 11  # Client's kill steak
builtins.STAT_BLOCKS = 12      # Client's succesfull blocks
builtins.STAT_JUMPS = 13       # Client's jumps
builtins.STAT_CARNHP = 14      # Client's HP earned with Carn
builtins.STAT_NPCDMG = 15      # Client's NPC damage
builtins.STAT_NPCKILL = 16     # Client's NPC kills
builtins.STAT_PEONDMG = 17     # Client's Peon damage
builtins.STAT_PEONKILL = 18    # Client's Peon kills
builtins.STAT_BUILDDMG = 19    # Client's Building damage
builtins.STAT_BUILDKILL = 20   # Client's Building kills
builtins.STAT_OUTPOSTDMG = 21  # Client's Outpost damage
builtins.STAT_CLIENTDMG = 22   # Damage caused to other Clients
builtins.STAT_MELEEKILL = 23   # Melee kills
builtins.STAT_RANGEDKILL = 24  # Ranged kills
builtins.STAT_SIEGEKILL = 25   # Siege Units killed by Client
builtins.STAT_MINE = 26        # Mining XP
builtins.STAT_HEAL = 27        # Healing XP
builtins.STAT_BUILD = 28       # Building XP
builtins.STAT_MONEYGAIN = 29   # Money earned
builtins.STAT_MONEYSPEND = 30  # Money spent
builtins.STAT_ORDERGIVE = 31   # Orders given by Client
builtins.STAT_ORDEROBEY = 32   # Orders obeyed by Client
builtins.STAT_EXPERIENCE = 33  # Total XP gained by Client
builtins.STAT_AUTOBUFF = 34    # Auto-buffs used by Client
builtins.STAT_SACRIFICE = 35   # Sacrifices used by Client
builtins.STAT_FLAGCAPTURE = 36 # Flags captured by Client
builtins.STAT_CONNECTTIME = 37 # Time connected to server
builtins.STAT_ONTEAMTIME = 38  # Time spent playing
builtins.INFO_CANCOMMTIME = 39 # Time after the Client can command again
builtins.INFO_REFSTATUS = 40   # 'none', 'guest', 'normal' or 'god'
builtins.INFO_CLANABBREV = 41  # Client's Clan's ABBREVIATION/TAG
builtins.INFO_CLIENTIP = 42  # Client's ip[18]


# Max Definitions
builtins.MAX_OBJECTS = 1024
builtins.MAX_CLIENTS = 128
builtins.MAX_SQUADS = 7
builtins.MAX_TEAMS = 9
builtins.MAX_BACKUPS = 127

# Object Types
builtins.OBJTYPE_CLIENT = 0
builtins.OBJTYPE_WORKER = 1
builtins.OBJTYPE_NPC = 2
builtins.OBJTYPE_MINE = 3
builtins.OBJTYPE_BASE = 4
builtins.OBJTYPE_OUTPOST = 5
builtins.OBJTYPE_BUILDING = 6
builtins.OBJTYPE_OTHER = 7

# Mine Types
builtins.MINETYPE_ANY = 0
builtins.MINETYPE_GOLD = 1
builtins.MINETYPE_STONE = 2

# Inventory Types
builtins.INVTYPE_NONE = 0
builtins.INVTYPE_MELEE = 1
builtins.INVTYPE_RANGED = 2
builtins.INVTYPE_ITEM = 3

# Input Angle IDs
builtins.ANGLE_PITCH = 0
builtins.ANGLE_YAW = 1
builtins.ANGLE_ROLL = 2

# Input Motion IDs
builtins.MOVE_FORWARD = 0
builtins.MOVE_BACKWARD = 1
builtins.MOVE_LEFT = 2
builtins.MOVE_RIGHT = 3
builtins.MOVE_JUMP = 4
builtins.MOVE_CROUCH = 5
builtins.MOVE_STOP = 6

# Input Button IDs
builtins.BUTTON_ATTACK = 0
builtins.BUTTON_BLOCK = 1
builtins.BUTTON_USE = 2
builtins.BUTTON_SPRINT = 3
builtins.BUTTON_CHARGE = 4
builtins.BUTTON_WORK = 5

# Navigation Order IDs (GOAL: obj->goal)
builtins.ORDER_NONE = 0
builtins.ORDER_MINE = 1
builtins.ORDER_DROPOFF = 2
builtins.ORDER_ATTACK = 3
builtins.ORDER_DEFEND = 4
builtins.ORDER_FOLLOW = 5
builtins.ORDER_REACH = 6
builtins.ORDER_CONSTRUCT = 7
builtins.ORDER_REPAIR = 8
builtins.ORDER_FLEE = 9
builtins.ORDER_ENTERBUILDING = 10
builtins.ORDER_ENTERTRANSPORT = 11
builtins.ORDER_COMPLETED = 12
builtins.ORDER_ENTERMINE = 13

# Navigation Goal IDs (AIGOAL: obj->ai->goal->aigcs.goal)
builtins.GOAL_IDLE = 0
builtins.GOAL_GOTO = 1
builtins.GOAL_FOLLOW = 2
builtins.GOAL_FLEE = 3
builtins.GOAL_CONSTRUCT = 4
builtins.GOAL_MINE = 5
builtins.GOAL_ATTACKMELEE = 6
builtins.GOAL_ATTACKMISSILE = 7
builtins.GOAL_ATTACKPOUND = 8
builtins.GOAL_ATTACKSUICIDE = 9
builtins.GOAL_ENTERMINE = 10

# Navigation State IDs (TASK: obj->ai->goal->task)
builtins.STATE_NONE = 0
builtins.STATE_MOVING = 1
builtins.STATE_WAITING = 2

# Bot Names (For Samurai Wars: Names from Rurouni Kenshin and Ranma 1/2)
builtins.BOT_NAMES_LEGION = [
    'GoldenBistro',
    'Jewiles',
    'Bobbe',
    'TheBottle',
    'Saruman',
    'Blade',
    'Impossibru',
    'Suaress',
    'SilverMoxy',
    'FakeNecro',
    '3dMeme',
    'ShameShifter',
    'Tina',
    'Kenaj',
    'Poolako',
    'DJCmak'
]

builtins.BOT_NAMES_BEAST = [
    'RealNecro',
    'UnclePhoe',
    'Ghimler',
    'Sosorry',
    'Buss',
    'Haff',
    'Marb',
    'PaulusJr',
    'blume!',
    'Toxeec',
    'C.A.I.',
    'rin',
    '@',
    'DarkAngella',
    'ElendilJr',
    'Botroth'
]

builtins.BOT_NAMES_SAMURAI = [
    'Aoshi',
    'Sanosuke',
    'Kenshin',
    'Yahiko',
    'Shishio',
    'Hajime',
    'Kenshiro',
    'Ryuken',
    'Raoh',
    'Toki',
    'Shin',
    'Ranma',
    'Ryoga',
    'Genma',
    'Kuno',
    'Soun'
]
