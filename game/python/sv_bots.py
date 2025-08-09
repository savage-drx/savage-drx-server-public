# ---------------------------------------------------------------------------
#           Name: sv_bots.py
#         Author: Anthony Beaucamp (aka Mohican), Clemens Kremser
#  Last Modified: 20/09/2013
#    Description: Basic implementation of Bots in Python (for demonstration) & Advanced Duel Bots
# ---------------------------------------------------------------------------

# Savage API
import bot
import core

# Savage Modules
import sv_defs
import sv_utils
import sh_logger as log

# Python Modules
import math

import random

random.seed()

# 3rd Party Modules
from euclid import *

# Shared Bot Info
global botIndex
global botGoal
global botOrder
global botState
global botPos

# Shared Target Info
global tgtIndex
global tgtPos
global tgtDir
global tgtDist

# Shared Waypoint Info
global wayPos
global wayDir
global wayDist

# Bot Stats Records
global lastDibs
global lastCheckGoal
global lastCheckEnemy
global lastCheckDodge
global immobilizedTime

# Timers
global blockTimer, blocked
global waitLeapTimer, waitedBeforeLeap
global attackDelay, attackDelayTimer
global leapDelay, leapDelayTimer
global leapBackDelay, leapBackDelayTimer
global waitMove, waitMoveTimer
global jumped, jumpDelay, jumpDelayTimer
global disableNav, disableNavTimer

# Resets
global stopShooting

# Special Settings
global isSaccing
global maxHits
global skillLevel, lastType
global sprinting
global boolean1

# Bob's Super Secret Special Variables For Very Specific Personal Usage Only
global bobbotTimer

# Talk Stuff
global randomTauntTimer
global targetDiedTalk
global happiness

# Dibbing Record
global objDibber

# Register some Cvars
core.CvarSetValue('sv_botAutoSpawn', 1)  # Allow Bots to spawn automatically
core.CvarSetValue('sv_botAutoEquip', 1)  # Allow Bots to purchase units/weapons/items automatically
core.CvarSetValue('sv_botAutoGoals', 1)  # Allow Bots to automatically decide their next action when idle
core.CvarSetValue('sv_botAutoGoodie', 1)  # Allow Bots to collect goodie nags automatically

core.CvarSetValue('sv_botCheckGoalFreq', 1500)  # Frequency (msec) at which Bots reassess their current Goal
core.CvarSetValue('sv_botCheckEnemyFreq', 500)  # Frequency (msec) at which Bots look for ennemy objects
core.CvarSetValue('sv_botCheckEnemyRange', 1000)  # Maximum range where Bots look for enemy objects
core.CvarSetValue('sv_botCheckGoodieRange', 200)  # Maximum range where Bots look for goodie bags
core.CvarSetValue('sv_botCheckCritterGold', 7500)  # Money threshhold above which Bots stop farming npcs
core.CvarSetValue('sv_botCheckCritterRange', 500)  # Maximum range where Bots look for npcs to farm
core.CvarSetValue('sv_botCheckConstructRange', 500)  # Maximum range where Bots look for buildings under construction
core.CvarSetValue('sv_botCheckRepairRange', 500)  # Maximum range where Bots look for buildings to repair

core.CvarSetValue('sv_botCheckDodgeFreq', 500)  # Frequency (msec) at which Bots decide whether to walk sideways
core.CvarSetValue('sv_botCheckDodgeChance', 0.2)  # Percentage chance that a Bot decides to walk sideway (value:0-1)
core.CvarSetValue('sv_botCheckDodgeRangeMin',
                  200)  # When fighting another client, Bots dodge continuously if they are further from target than this value
core.CvarSetValue('sv_botCheckDodgeRangeMax',
                  900)  # When fighting another client, Bots dodge continuously if they are closer from target than this value

core.CvarSetValue('sv_botWeaponRangeMin', 100)  # Minimum Distance to Target at which Ranged Weapons can be used
core.CvarSetValue('sv_botWeaponAccuracyAng',
                  5)  # Angular accuracy (degs) of ranged weapon shots (the lower the more accurate)
core.CvarSetValue('sv_botHumanDisruptorDist', 550)  # Min. Distance to Enemy Building before using Disruptor
core.CvarSetValue('sv_botHumanDisruptorDelay',
                  2500)  # Delay (msec) before bot starts moving again after throwing Disruptor
core.CvarSetValue('sv_botHumanDemoPackDist', 40)  # Min. Distance to Enemy Building before using Demolition Pack
core.CvarSetValue('sv_botBeastProtectDist', 600)  # Min. Distance to Enemy Building before using Protect
core.CvarSetValue('sv_botBeastSacrificeDist', 1000)  # Min. Distance to Enemy Building before using Sacrifice

core.CvarSetValue('sv_botStaminaCostPercent',
                  25)  # Stamina cost percentage (integer) stamina -= staminaCost * percent / 100
core.CvarSetValue('sv_botHumanBlockDelay', 30)  # Delay between block spam (in bot-frames)
core.CvarSetValue('sv_botTalk', 0)  # Allow Bots to talk
core.CvarSetValue('sv_botTalkFreq', 5)  # Percentage chance that a Bot decides to talk
core.CvarSetValue('sv_botRandomTauntFreq', 1500)  # Interval between Bot's random taunting

core.CvarSetValue('sv_botDuelTier', 3)  # The Tier of Unit Bots shall use on a Duel Server
core.CvarSetValue('sv_botPersonaName',
                  0)  # True/False to determine if a Bot should use a real name or a Persona Level name

core.CvarSetValue('sv_botRandomPersona',
                  1)  # Randomize Bot Persona at join/add - 0 = off, 1 = on, 2 = selected pool (TODO)
core.CvarSetValue('sv_botHumanType', 0)  # Human Bot's Persona at join/add (ignored if sv_botRandomPersona is on)
core.CvarSetValue('sv_botBeastType', 0)  # Beast Bot's Persona at join/add (ignored if sv_botRandomPersona is on)
core.CvarSetValue('sv_botHardcoreMode', 0)  # Elec buff for bots


# -------------------------------
# Called directly by Silverback
# -------------------------------
def init():
    log.info("Initializing Bots...")

    try:
        # Initialize Bot Stats
        global lastDibs
        global lastCheckGoal
        global lastCheckEnemy
        global lastCheckDodge
        global immobilizedTime
        lastDibs = list(-1 for n in range(0, MAX_CLIENTS))
        lastCheckGoal = list(0 for n in range(0, MAX_CLIENTS))
        lastCheckEnemy = list(0 for n in range(0, MAX_CLIENTS))
        lastCheckDodge = list(0 for n in range(0, MAX_CLIENTS))
        immobilizedTime = list(0 for n in range(0, MAX_CLIENTS))

        # Create Objects Info Record
        global objDibber
        objDibber = list(-1 for n in range(0, MAX_OBJECTS))

    except:
        log.error("Initialization FAILED!")


# -------------------------------
# Called directly by Silverback
# -------------------------------
def add(botIndex, botTeam, botRaceDesc):
    log.info("Allocating Bot Information...")

    try:
        global skillLevel
        # Set Bot's Name
        if botRaceDesc == 'The Legion of Man':
            botName = BOT_NAMES_LEGION[botIndex % 16]
            if core.CvarGetValue('sv_botRandomPersona') == 1:
                skillLevel = random.randint(6, 12)
            elif core.CvarGetValue('sv_botRandomPersona') == 2:
                skillLevel = random.randint(0, 3)
            else:
                skillLevel = core.CvarGetValue('sv_botHumanType')
        elif botRaceDesc == 'The Beast Horde':
            botName = BOT_NAMES_BEAST[botIndex % 16]
            if core.CvarGetValue('sv_botRandomPersona') == 1:
                skillLevel = random.randint(10, 20)
            elif core.CvarGetValue('sv_botRandomPersona') == 2:
                skillLevel = random.randint(0, 3)
            else:
                skillLevel = core.CvarGetValue('sv_botBeastType')
        else:
            botName = BOT_NAMES_SAMURAI[botIndex % 16]
            skillLevel = 0

        if core.CvarGetValue('sv_botPersonaName') == 1:
            newSkillName(botIndex, skillLevel)
        else:
            # debugging version: botName = 'bot' + str(botIndex) + '-' + botName
            bot.SetName(botIndex, botName)

        # Randomize check times to avoid spikes on CPU processing
        global lastDibs
        global lastCheckGoal
        global lastCheckEnemy
        global lastCheckDodge
        global immobilizedTime
        lastDibs[botIndex] = 0
        lastCheckGoal[botIndex] = sv_defs.gameTime + random.randint(0, int(core.CvarGetValue('sv_botCheckGoalFreq')))
        lastCheckEnemy[botIndex] = sv_defs.gameTime + random.randint(0, int(core.CvarGetValue('sv_botCheckEnemyFreq')))
        lastCheckDodge[botIndex] = sv_defs.gameTime + random.randint(0, int(core.CvarGetValue('sv_botCheckDodgeFreq')))
        immobilizedTime[botIndex] = 0

        # Timers
        global blockTimer
        blockTimer = -1
        global blocked
        blocked = 0
        global waitLeapTimer
        waitLeapTimer = -1
        global waitedBeforeLeap
        waitedBeforeLeap = 0
        global attackDelay
        attackDelay = 0
        global attackDelayTimer
        attackDelayTimer = 0
        global leapDelay
        leapDelay = 0
        global leapDelayTimer
        leapDelayTimer = 0
        global leapBackDelay
        leapBackDelay = 0
        global leapBackDelayTimer
        leapBackDelayTimer = 0
        global waitMove
        waitMove = 0
        global waitMoveTimer
        waitMoveTimer = 0
        global jumped
        jumped = 0
        global jumpDelay
        jumpDelay = 0
        global jumpDelayTimer
        jumpDelayTimer = 0
        global disableNav
        disableNav = 0
        global disableNavTimer
        disableNavTimer = 0

        # Resets
        global stopShooting
        stopShooting = 0

        # Special states
        global isSaccing
        isSaccing = 0
        global maxHits
        maxHits = 3
        global lastType
        lastType = 0
        global sprinting
        sprinting = 0
        global boolean1
        boolean1 = 0

        # Bob's Super Secret Special Variables For Very Specific Personal Usage Only
        global bobbotTimer
        bobbotTimer = 0

        # Talk Stuff
        global randomTauntTimer
        randomTauntTimer = 0
        global targetDiedTalk
        targetDiedTalk = 0
        global happiness
        happiness = 5

    except:
        log.error("Allocation FAILED!")


# -------------------------------
# Called directly by Silverback
# -------------------------------
def wounded(botIndex, attackerIndex, weapon, damage):
    try:
        # React only to attacks by Clients (unless currently Idle)
        if attackerIndex < MAX_CLIENTS or bot.NavGetGoal(botIndex) == GOAL_IDLE:
            bot.NavSetTargetObj(botIndex, attackerIndex, ORDER_ATTACK)

    except:
        pass


def death(botIndex, killerIndex, weapon):
    # Reset
    global isSaccing
    isSaccing = 0
    global sprinting
    sprinting = 0
    global skillLevel
    global lastType

    if skillLevel < 0:
        raceDesc = sv_defs.teamList_RaceDesc[sv_defs.clientList_Team[botIndex]]
        if raceDesc == 'The Legion of Man':
            lastType = random.randint(0, 7)
        elif raceDesc == 'The Beast Horde':
            lastType = random.randint(0, 13)

    global happiness

    if core.CvarGetValue('sv_botHardcoreMode') == 1:
        command = 'givestate ' + str(botIndex) + ' electrify -1'
        core.CommandExec(command)

    if core.CvarGetValue('sv_botTalk'):
        happiness -= 1
        if int(core.CvarGetValue('sv_botTalkFreq')) > 0:
            rnd = random.randint(0, 100)
            if rnd <= int(core.CvarGetValue('sv_botTalkFreq')):
                deathTaunt(botIndex)
                randomTauntTimer = 0


# -------------------------------
# Called directly by Silverback
# -------------------------------
def frame():
    try:
        # Process Active Bots
        global botIndex
        for botIndex in range(0, MAX_CLIENTS):
            # Only active Bots		
            if not sv_defs.clientList_Bot[botIndex]:
                continue

            # Process relevant Frame type
            status = bot.GetStatus(botIndex)
            if status == 1:
                frame_loadout()
            elif status == 2:
                frame_playing()
            elif status == 3:
                frame_dead()

    except:
        pass


def frame_loadout():
    # ---------------------
    # Automated Purchase?
    if core.CvarGetValue('sv_botAutoEquip'):

        # Need to know the Race first
        raceDesc = sv_defs.teamList_RaceDesc[sv_defs.clientList_Team[botIndex]]

        noWeapon = 0
        if raceDesc == 'The Legion of Man':

            # Request enough money for any basic weapon
            if bot.GetMoney(botIndex) < 500:
                bot.RequestMoney(botIndex, 500)
            # Randomize weapon choice from preset preferences
            rnd = random.randint(0, 10)
            if rnd > 7:  # Battle - Coil > Flux > Repeater
                if not bot.RequestItem(botIndex, 'human_coilrifle'):
                    if not bot.RequestItem(botIndex, 'human_fluxgun'):
                        if not bot.RequestItem(botIndex, 'human_repeater'):
                            if not bot.RequestItem(botIndex, 'human_launcher'):
                                if not bot.RequestItem(botIndex, 'human_mortar'):
                                    noWeapon = 1
            elif rnd > 4:  # Battle - Coil > Repeater > Flux
                if not bot.RequestItem(botIndex, 'human_coilrifle'):
                    if not bot.RequestItem(botIndex, 'human_repeater'):
                        if not bot.RequestItem(botIndex, 'human_fluxgun'):
                            if not bot.RequestItem(botIndex, 'human_launcher'):
                                if not bot.RequestItem(botIndex, 'human_mortar'):
                                    noWeapon = 1
            elif rnd > 3:  # Battle - Flux > Repeater
                if not bot.RequestItem(botIndex, 'human_fluxgun'):
                    if not bot.RequestItem(botIndex, 'human_repeater'):
                        if not bot.RequestItem(botIndex, 'human_launcher'):
                            if not bot.RequestItem(botIndex, 'human_mortar'):
                                noWeapon = 1
            elif rnd > 2:  # Battle - Repeater > Flux
                if not bot.RequestItem(botIndex, 'human_repeater'):
                    if not bot.RequestItem(botIndex, 'human_fluxgun'):
                        if not bot.RequestItem(botIndex, 'human_launcher'):
                            if not bot.RequestItem(botIndex, 'human_mortar'):
                                noWeapon = 1
            elif rnd > 0:  # Battle - Pulse > Launcher > Mortar > Coil > Repeater > Flux
                if not bot.RequestItem(botIndex, 'human_pulsegun'):
                    if not bot.RequestItem(botIndex, 'human_launcher'):
                        if not bot.RequestItem(botIndex, 'human_mortar'):
                            if not bot.RequestItem(botIndex, 'human_coilrifle'):
                                if not bot.RequestItem(botIndex, 'human_repeater'):
                                    if not bot.RequestItem(botIndex, 'human_fluxgun'):
                                        if not bot.RequestItem(botIndex, 'human_launcher'):
                                            if not bot.RequestItem(botIndex, 'human_mortar'):
                                                noWeapon = 1
            # Default: go through the full list
            else:
                if not bot.RequestItem(botIndex, 'human_coilrifle'):
                    if not bot.RequestItem(botIndex, 'human_pulsegun'):
                        if not bot.RequestItem(botIndex, 'human_fluxgun'):
                            if not bot.RequestItem(botIndex, 'human_repeater'):
                                if not bot.RequestItem(botIndex, 'human_scattergun'):
                                    if not bot.RequestItem(botIndex, 'human_discharger'):
                                        if not bot.RequestItem(botIndex, 'human_launcher'):
                                            if not bot.RequestItem(botIndex, 'human_mortar'):
                                                if not bot.RequestItem(botIndex, 'human_incinerator'):
                                                    if not bot.RequestItem(botIndex, 'human_crossbow'):
                                                        bot.RequestItem(botIndex, 'human_bow')

            if noWeapon == 1:
                rnd = random.randint(0, 5)
                if rnd == 0 or rnd == 1:  # Scattergun
                    if not bot.RequestItem(botIndex, 'human_scattergun'):
                        if not bot.RequestItem(botIndex, 'human_discharger'):
                            if not bot.RequestItem(botIndex, 'human_incinerator'):
                                if not bot.RequestItem(botIndex, 'human_crossbow'):
                                    bot.RequestItem(botIndex, 'human_bow')
                elif rnd == 2 or rnd == 3:  # Discharger
                    if not bot.RequestItem(botIndex, 'human_discharger'):
                        if not bot.RequestItem(botIndex, 'human_scattergun'):
                            if not bot.RequestItem(botIndex, 'human_incinerator'):
                                if not bot.RequestItem(botIndex, 'human_crossbow'):
                                    bot.RequestItem(botIndex, 'human_bow')
                elif rnd == 4:  # Incinerator > Discharger
                    if not bot.RequestItem(botIndex, 'human_incinerator'):
                        if not bot.RequestItem(botIndex, 'human_discharger'):
                            if not bot.RequestItem(botIndex, 'human_scattergun'):
                                if not bot.RequestItem(botIndex, 'human_crossbow'):
                                    bot.RequestItem(botIndex, 'human_bow')
                elif rnd == 5:  # Incinerator > Scattergun
                    if not bot.RequestItem(botIndex, 'human_incinerator'):
                        if not bot.RequestItem(botIndex, 'human_scattergun'):
                            if not bot.RequestItem(botIndex, 'human_discharger'):
                                if not bot.RequestItem(botIndex, 'human_crossbow'):
                                    bot.RequestItem(botIndex, 'human_bow')
                else:  # Just-in-case default
                    if not bot.RequestItem(botIndex, 'human_crossbow'):
                        bot.RequestItem(botIndex, 'human_bow')

            # Try to purhcase at least 1 medkit
            if bot.GetMoney(botIndex) < 500:
                bot.RequestMoney(botIndex, 500)
            bot.RequestItem(botIndex, 'human_medkit')

            # Request the difference towards Legionnaire
            if bot.GetMoney(botIndex) < 4500:
                bot.RequestMoney(botIndex, 4500 - bot.GetMoney(botIndex))
            # Try to upgrade Unit
            bot.RequestUnit(botIndex, 'human_savage')
            bot.RequestUnit(botIndex, 'human_legionnaire')

            # Try to pruchase some more Medkits
            if bot.GetMoney(botIndex) < 500:
                bot.RequestMoney(botIndex, 500)
            bot.RequestItem(botIndex, 'human_medkit')
            if bot.GetMoney(botIndex) < 500:
                bot.RequestMoney(botIndex, 500)
            bot.RequestItem(botIndex, 'human_medkit')

            # If Bot has any leftover funds, try get some luxury items

            # Try for an AmmoPack
            bot.RequestItem(botIndex, 'human_ammo_pack')

            # Try for a DemoPack
            if bot.GetMoney(botIndex) < 1000:
                bot.RequestMoney(botIndex, 1000)
            bot.RequestItem(botIndex, 'human_demo_pack')

            # Try for a Disruptor
            if bot.GetMoney(botIndex) < 500:
                bot.RequestMoney(botIndex, 500)
            bot.RequestItem(botIndex, 'human_disruptor')

            # Try for a single Landmine
            # bot.RequestItem(boxIndex,'human_landmine') #TODO: Fix

            if core.CvarGetValue('sv_duelserver'):
                bot.RequestMoney(botIndex, 8000)
                bot.RequestItem(botIndex, 'human_medkit')
                bot.RequestItem(botIndex, 'human_medkit')
                bot.RequestItem(botIndex, 'human_medkit')
                if core.CvarGetValue('sv_botDuelTier') == 1:
                    bot.RequestUnit(botIndex, 'human_nomad')
                elif core.CvarGetValue('sv_botDuelTier') == 2:
                    bot.RequestUnit(botIndex, 'human_savage')
                elif core.CvarGetValue('sv_botDuelTier') == 3:
                    bot.RequestUnit(botIndex, 'human_legionnaire')


        elif raceDesc == 'The Beast Horde':

            # Request enough money for any basic weapon
            if bot.GetMoney(botIndex) < 500:
                bot.RequestMoney(botIndex, 500)
            # Randomize weapon choice from preset preferences
            rnd = random.randint(0, 16)
            if rnd > 13:  # Battle - Strata > Blaze > Surge
                if not bot.RequestItem(botIndex, 'beast_strata2'):
                    if not bot.RequestItem(botIndex, 'beast_fire2'):
                        if not bot.RequestItem(botIndex, 'beast_entropy2'):
                            noWeapon = 1
            elif rnd > 10:  # Battle - Blaze > Strata > Surge
                if not bot.RequestItem(botIndex, 'beast_fire2'):
                    if not bot.RequestItem(botIndex, 'beast_strata2'):
                        if not bot.RequestItem(botIndex, 'beast_entropy2'):
                            noWeapon = 1
            elif rnd > 9:  # Battle - Surge > Strata > Blaze
                if not bot.RequestItem(botIndex, 'beast_entropy2'):
                    if not bot.RequestItem(botIndex, 'beast_strata2'):
                        if not bot.RequestItem(botIndex, 'beast_fire2'):
                            noWeapon = 1
            elif rnd > 8:  # Battle - Surge > Blaze > Strata
                if not bot.RequestItem(botIndex, 'beast_entropy2'):
                    if not bot.RequestItem(botIndex, 'beast_fire2'):
                        if not bot.RequestItem(botIndex, 'beast_strata2'):
                            noWeapon = 1
            elif rnd > 7:  # Battle - Rupture
                if not bot.RequestItem(botIndex, 'beast_entropy3'):
                    if not bot.RequestItem(botIndex, 'beast_entropy2'):
                        if not bot.RequestItem(botIndex, 'beast_strata2'):
                            if not bot.RequestItem(botIndex, 'beast_fire2'):
                                noWeapon = 1
            elif rnd > 6:  # Battle - Fireball
                if not bot.RequestItem(botIndex, 'beast_fire3'):
                    if not bot.RequestItem(botIndex, 'beast_fire2'):
                        if not bot.RequestItem(botIndex, 'beast_strata2'):
                            if not bot.RequestItem(botIndex, 'beast_entropy2'):
                                noWeapon = 1
            elif rnd > 5:  # Battle - Lightning
                if not bot.RequestItem(botIndex, 'beast_strata3'):
                    if not bot.RequestItem(botIndex, 'beast_strata2'):
                        if not bot.RequestItem(botIndex, 'beast_fire2'):
                            if not bot.RequestItem(botIndex, 'beast_entropy2'):
                                noWeapon = 1
            elif rnd > 0:  # Battle - Melee
                if not bot.RequestItem(botIndex, 'beast_vampire'):
                    if not bot.RequestItem(botIndex, 'beast_rabid'):
                        if not bot.RequestItem(botIndex, 'beast_poison'):
                            if not bot.RequestItem(botIndex, 'beast_strata2'):
                                if not bot.RequestItem(botIndex, 'beast_fire2'):
                                    if not bot.RequestItem(botIndex, 'beast_entropy2'):
                                        noWeapon = 1
            # Default: go through the full list
            else:
                if not bot.RequestItem(botIndex, 'beast_strata2'):
                    if not bot.RequestItem(botIndex, 'beast_entropy3'):
                        if not bot.RequestItem(botIndex, 'beast_fire3'):
                            if not bot.RequestItem(botIndex, 'beast_entropy2'):
                                if not bot.RequestItem(botIndex, 'beast_fire2'):
                                    if not bot.RequestItem(botIndex, 'beast_fire1'):
                                        if not bot.RequestItem(botIndex, 'beast_strata1'):
                                            if not bot.RequestItem(botIndex, 'beast_entropy1'):
                                                if not bot.RequestItem(botIndex, 'beast_vampire'):
                                                    if not bot.RequestItem(botIndex, 'beast_rabid'):
                                                        bot.RequestItem(botIndex, 'beast_poison')

            if noWeapon == 1:
                rnd = random.randint(0, 5)
                if rnd == 0 or rnd == 1:  # Ember
                    if not bot.RequestItem(botIndex, 'beast_fire1'):
                        if not bot.RequestItem(botIndex, 'beast_strata1'):
                            if not bot.RequestItem(botIndex, 'beast_entropy1'):
                                if not bot.RequestItem(botIndex, 'beast_vampire'):
                                    if not bot.RequestItem(botIndex, 'beast_rabid'):
                                        bot.RequestItem(botIndex, 'beast_poison')
                elif rnd == 2 or rnd == 3:  # Frostbolts
                    if not bot.RequestItem(botIndex, 'beast_strata1'):
                        if not bot.RequestItem(botIndex, 'beast_fire1'):
                            if not bot.RequestItem(botIndex, 'beast_entropy1'):
                                if not bot.RequestItem(botIndex, 'beast_vampire'):
                                    if not bot.RequestItem(botIndex, 'beast_rabid'):
                                        bot.RequestItem(botIndex, 'beast_poison')
                elif rnd == 4:  # Chaosbolt > Ember
                    if not bot.RequestItem(botIndex, 'beast_entropy1'):
                        if not bot.RequestItem(botIndex, 'beast_fire1'):
                            if not bot.RequestItem(botIndex, 'beast_strata1'):
                                if not bot.RequestItem(botIndex, 'beast_vampire'):
                                    if not bot.RequestItem(botIndex, 'beast_rabid'):
                                        bot.RequestItem(botIndex, 'beast_poison')
                elif rnd == 5:  # Chaosbolt > Frostbolts
                    if not bot.RequestItem(botIndex, 'beast_entropy1'):
                        if not bot.RequestItem(botIndex, 'beast_strata1'):
                            if not bot.RequestItem(botIndex, 'beast_fire1'):
                                if not bot.RequestItem(botIndex, 'beast_vampire'):
                                    if not bot.RequestItem(botIndex, 'beast_rabid'):
                                        bot.RequestItem(botIndex, 'beast_poison')
                else:  # Just-in-case default
                    bot.RequestItem(botIndex, 'beast_poison')

            # Request the difference towards Predator
            if bot.GetMoney(botIndex) < 4500:
                bot.RequestMoney(botIndex, 4500 - bot.GetMoney(botIndex))
            # Finally, try to upgrade Unit
            bot.RequestUnit(botIndex, 'beast_stalker')
            bot.RequestUnit(botIndex, 'beast_predator')

            # Try to get Money for Sacrifice
            if bot.GetMoney(botIndex) < 1000:
                bot.RequestMoney(botIndex, 1000)
            bot.RequestItem(botIndex, 'beast_immolate')

            # Try to get Money for Windshield
            if bot.GetMoney(botIndex) < 500:
                bot.RequestMoney(botIndex, 500)
            bot.RequestItem(botIndex, 'beast_protect')

            # Try to purchase Mana and Camouflage
            bot.RequestItem(botIndex, 'beast_mana_stone')
            bot.RequestItem(botIndex, 'beast_camouflage')

            if core.CvarGetValue('sv_duelserver'):
                bot.RequestMoney(botIndex, 7000)
                bot.RequestItem(botIndex, 'beast_rabid')
                if core.CvarGetValue('sv_botDuelTier') == 1:
                    bot.RequestUnit(botIndex, 'beast_scavenger')
                elif core.CvarGetValue('sv_botDuelTier') == 2:
                    bot.RequestUnit(botIndex, 'beast_stalker')
                elif core.CvarGetValue('sv_botDuelTier') == 3:
                    bot.RequestUnit(botIndex, 'beast_predator')

        elif raceDesc == 'Shogunate':

            # Choose Unit Type Randomly
            unitType = random.randint(1, 3)
            if unitType == 1:
                # Request Ranged Unit (in order of preference)
                if not bot.RequestUnit(botIndex, 'human_musketeer'):
                    if not bot.RequestUnit(botIndex, 'human_archer'):
                        bot.RequestUnit(botIndex, 'human_kyudoist')

                # Request Weapon and Ammo
                bot.RequestItem(botIndex, 'human_bow')
                bot.RequestItem(botIndex, 'human_ammo_pack')

            elif unitType == 2:
                # Request Sword Unit (in order of preference)
                if bot.RequestUnit(botIndex, 'human_kensai'):
                    unitName = 'human_kensai'
                elif bot.RequestUnit(botIndex, 'human_kengou'):
                    unitName = 'human_kengou'
                else:
                    unitName = 'human_samurai'

                # Request Sword Weapon (in order of preference)
                if bot.RequestItem(botIndex, 'human_tachi'):
                    fullName = unitName + '_human_tachi'
                elif bot.RequestItem(botIndex, 'human_nodachi'):
                    fullName = unitName + '_human_nodachi'
                else:
                    fullName = unitName + '_human_katana'

                # Request "Unit_Weapon" Type (because of SW melee 'hack')
                bot.RequestUnit(botIndex, fullName)

            elif unitType == 3:
                # Request Pole Unit (in order of preference)
                if bot.RequestUnit(botIndex, 'human_sohei'):
                    unitName = 'human_sohei'
                elif bot.RequestUnit(botIndex, 'human_yarisamurai'):
                    unitName = 'human_yarisamurai'
                else:
                    unitName = 'human_ashigaru'

                # Request Pole Weapon (in order of preference)
                if bot.RequestItem(botIndex, 'human_naginata'):
                    fullName = unitName + '_human_naginata'
                elif bot.RequestItem(botIndex, 'human_yari'):
                    fullName = unitName + '_human_yari'
                else:
                    fullName = unitName + '_human_bo'

                # Request "Unit+Weapon" Type (SW 'hack' for varied melee)
                bot.RequestUnit(botIndex, fullName)

            # Try to get Money for Explosives
            if bot.GetMoney(botIndex) < 1000:
                bot.RequestMoney(botIndex, 1000)
            bot.RequestItem(botIndex, 'human_explosives')

            # Try to get Money for Medkits
            if bot.GetMoney(botIndex) < 500:
                bot.RequestMoney(botIndex, 500)
            bot.RequestItem(botIndex, 'human_medkit')
            bot.RequestItem(botIndex, 'human_medkit')
            bot.RequestItem(botIndex, 'human_medkit')

    # ---------------------


    # Automated Spawning?
    if core.CvarGetValue('sv_botAutoSpawn'):
        # Default spawnpoint is Base
        spawnIndex = 0

        botTeam = sv_defs.clientList_Team[botIndex]
        botSquad = sv_defs.clientList_Squad[botIndex]
        botMission = sv_defs.teamList_Missions[botTeam * MAX_SQUADS + botSquad]
        # If return to base, or need more gold, or need more stone -> spawn at base
        if botMission == 2 or botMission == 4 or botMission == 5:
            spawnIndex = 0
        else:
            # Is Navigating?
            if not bot.NavGetGoal(botIndex) == GOAL_IDLE:
                # Then find spawnpoint nearest to target
                [x, y, z] = bot.NavGetTargetPos(botIndex)
                targetPos = Point3(x, y, z)
                spawnIndex = sv_utils.find_best_spawnpoint(botIndex, targetPos)

        bot.NavSetTargetObj(botIndex, -1, ORDER_NONE)

        # Execute spawn command
        command = 'botspawn ' + str(botIndex) + ' ' + str(spawnIndex)
        core.CommandExec(command)


# -------------------------------
def frame_playing():
    # Get Navigation Info
    global botGoal
    global botOrder
    global botState
    botGoal = bot.NavGetGoal(botIndex)
    botOrder = bot.NavGetOrder(botIndex)
    botState = bot.NavGetState(botIndex)

    # Check Navigation State
    frame_playing_checkNav()

    # Check Finite-State-Machine
    frame_playing_checkFSM()

    # Advance Bot Navigation
    bot.NavUpdate(botIndex)

    # Process Player Input
    frame_playing_checkInput()

    # Check if Items can be used
    frame_playing_checkItems()


# -------------------------------
def frame_playing_checkNav():
    # Has Bot already got an Order?
    if botOrder == ORDER_NONE:
        return

    # Is Bot Idle? (may have just respawned)
    if not botGoal == GOAL_IDLE:
        # Then try re-assigning Order
        if bot.NavGetType(botIndex) == 1:
            targetObj = bot.NavGetTargetObj(botIndex)
            bot.NavSetTargetObj(botIndex, targetObj, botOrder)
        else:
            [x, y, z] = bot.NavGetTargetPos(botIndex)
            bot.NavSetTargetPos(botIndex, x, y, botOrder)


# -------------------------------
def frame_playing_checkFSM():
    global isSaccing
    global tgtIndex
    tgtIndex = bot.NavGetTargetObj(botIndex)

    # Follow commander's order
    if botOrder != ORDER_NONE:
        return

    # Do not disturb combat...
    if botGoal == GOAL_ATTACKMELEE:
        # ...against clients or buildings
        if tgtIndex < MAX_CLIENTS or (sv_utils.is_building(tgtIndex) and isSaccing == 1):
            return

    # -----------------------------------------
    # Is it Time for Enemy Check? (basic FSM)
    if sv_defs.gameTime < (lastCheckEnemy[botIndex] + core.CvarGetValue('sv_botCheckEnemyFreq')):
        return
    lastCheckEnemy[botIndex] = sv_defs.gameTime

    # Then look for Enemy Players
    enemyIndex = sv_utils.find_nearest_enemy(botIndex, core.CvarGetValue('sv_botCheckEnemyRange'))
    if enemyIndex > -1:
        bot.NavSetTargetObj(botIndex, enemyIndex, ORDER_ATTACK)
        return

    # Look for Goodies
    if core.CvarGetValue('sv_botAutoGoodie'):
        goodieIndex = sv_utils.find_nearest_goodie(botIndex, core.CvarGetValue('sv_botCheckGoodieRange'), objDibber)
        if goodieIndex > -1:
            # Dibs on that Goodie!
            set_dibs(botIndex, goodieIndex)
            goodiePos = sv_utils.get_point3(goodieIndex)
            bot.NavSetTargetPos(botIndex, goodiePos.x, goodiePos.y, ORDER_REACH)
            return

    # -------------------------------------------
    # Is it Time for Goal Check? (advanced FSM)
    if not core.CvarGetValue('sv_botAutoGoals'):
        return
    if sv_defs.gameTime < (lastCheckGoal[botIndex] + core.CvarGetValue('sv_botCheckGoalFreq')):
        return
    lastCheckGoal[botIndex] = sv_defs.gameTime

    # Process Bot's Squad Mission
    botTeam = sv_defs.clientList_Team[botIndex]
    botSquad = sv_defs.clientList_Squad[botIndex]
    botMission = sv_defs.teamList_Missions[botTeam * MAX_SQUADS + botSquad]

    if botMission == 0:  # Destroy the enemy base
        baseIndex = sv_defs.teamList_Base[3 - botTeam]  # Only works for 2-Team games, needs fixing... X-)
        bot.NavSetTargetObj(botIndex, baseIndex, ORDER_ATTACK)

    elif botMission == 2:  # Return to base
        baseIndex = sv_defs.teamList_Base[botTeam]
        bot.NavSetTargetObj(botIndex, baseIndex, ORDER_DEFEND)

    elif botMission == 4:  # We need more gold
        log.custom("BOT", "We need more gold")
        # Try to look for Critters (fast money, look as far as 2x the distance normally allowed)
        critterIndex = sv_utils.find_nearest_critter(botIndex, 2 * core.CvarGetValue('sv_botCheckCritterRange'),
                                                     objDibber)
        if critterIndex > -1:
            log.custom("BOT", "Found critter")
            # Dibs on that Critter!
            set_dibs(botIndex, critterIndex)
            bot.NavSetTargetObj(botIndex, critterIndex, ORDER_ATTACK)
        # Otherwise find nearest Gold Mine (unless bot is already mining)
        elif not botOrder == ORDER_MINE and not botOrder == ORDER_DROPOFF:
            mineIndex = sv_utils.find_nearest_mine(botIndex, MINETYPE_GOLD)
            if mineIndex > -1:
                bot.NavSetTargetObj(botIndex, mineIndex, ORDER_MINE)

    elif botMission == 5:  # We need more redstone
        # Find nearest Stone Mine (unless bot is already mining)
        if not botOrder == ORDER_MINE and not botOrder == ORDER_DROPOFF:
            mineIndex = sv_utils.find_nearest_mine(botIndex, MINETYPE_STONE)
            if mineIndex > -1:
                bot.NavSetTargetObj(botIndex, mineIndex, ORDER_MINE)

    elif botMission == 9:  # Wait for my command
        # Stay put, do nothing
        stayput = 1

    elif botOrder == ORDER_NONE:  # Free-Styler!
        # Any Enemy building/item/worker nearby?
        targetIndex = sv_utils.find_nearest_enemy_object(botIndex, core.CvarGetValue('sv_botCheckEnemyRange'))
        if targetIndex > -1:
            bot.NavSetTargetObj(botIndex, targetIndex, ORDER_ATTACK)
            return
        else:
            baseIndex = sv_defs.teamList_Base[3 - botTeam]  # Only works for 2-Team games, needs fixing... X-)
            bot.NavSetTargetObj(botIndex, baseIndex, ORDER_ATTACK)

        # Any Building under construction nearby?
        targetIndex = sv_utils.find_nearest_construct(botIndex, core.CvarGetValue('sv_botCheckConstructRange'))
        if targetIndex > -1:
            bot.NavSetTargetObj(botIndex, targetIndex, ORDER_CONSTRUCT)
            return

        # Any Building in need of repair nearby?
        targetIndex = sv_utils.find_nearest_repair(botIndex, core.CvarGetValue('sv_botCheckRepairRange'))
        if targetIndex > -1:
            bot.NavSetTargetObj(botIndex, targetIndex, ORDER_CONSTRUCT)
            return

        # Look for Critters nearby?
        botMoney = bot.GetMoney(botIndex)
        if botMoney < core.CvarGetValue('sv_botCheckCritterGold'):
            critterIndex = sv_utils.find_nearest_critter(botIndex, core.CvarGetValue('sv_botCheckCritterRange'),
                                                         objDibber)
            if critterIndex > -1:
                # Dibs on that Critter!
                set_dibs(botIndex, critterIndex)
                bot.NavSetTargetObj(botIndex, critterIndex, ORDER_ATTACK)
                return


# -------------------------------
def frame_playing_checkInput():
    global botPos
    global tgtIndex
    botPos = sv_utils.get_point3(botIndex)
    tgtIndex = bot.NavGetTargetObj(botIndex)

    # Need to know the Race first
    raceDesc = sv_defs.teamList_RaceDesc[sv_defs.clientList_Team[botIndex]]

    # Compute direction & distance to Target
    global tgtPos
    global tgtDir
    global tgtDist
    if not botGoal == GOAL_IDLE:
        [x, y, z] = bot.NavGetTargetPos(botIndex)
        tgtPos = Point3(x, y, z)
    else:
        tgtPos = botPos
    tgtVec = tgtPos - botPos
    tgtDir = tgtVec.normalized()
    tgtDist = tgtVec.magnitude()

    # Compute direction & distance to next Waypoint
    global wayPos
    global wayDir
    global wayDist
    if not botGoal == GOAL_IDLE:
        [x, y, z] = bot.NavGetWayPoint(botIndex)
        wayPos = Point3(x, y, z)
    else:
        wayPos = botPos
    wayVec = wayPos - botPos
    wayDir = wayVec.normalized()
    wayDist = wayVec.magnitude()

    # Also compute 2D projection
    tgtVec2D = Point2(tgtVec[0], tgtVec[1])
    wayVec2D = Point2(wayVec[0], wayVec[1])
    tgtDir2D = tgtVec2D.normalized()
    wayDir2D = wayVec2D.normalized()

    # Timers
    global blockTimer, blocked
    global waitLeapTimer, waitedBeforeLeap
    global attackDelay, attackDelayTimer
    global leapDelay, leapDelayTimer
    global leapBackDelay, leapBackDelayTimer
    global waitMove, waitMoveTimer
    global jumped, jumpDelay, jumpDelayTimer
    global disableNav, disableNavTimer
    if blocked == 1:
        blockTimer += 1
    if waitedBeforeLeap == 1:
        waitLeapTimer += 1
    if attackDelay == 1:
        attackDelayTimer += 1
    if leapDelay == 1:
        leapDelayTimer += 1
    if leapBackDelay == 1:
        leapBackDelayTimer += 1
    if waitMove == 1:
        waitMoveTimer += 1
    if jumpDelay == 1:
        jumpDelayTimer += 1

    # Resets
    global stopShooting

    # Special Settings
    global maxHits
    global sprinting

    # Talk Stuff
    global randomTauntTimer
    global targetDiedTalk
    global happiness

    # Check unit; special units get special settings
    unitType = sv_defs.objectList_Name[botIndex]
    if unitType == 'human_legionnaire':
        maxHits = 2
    elif unitType == 'beast_predator':
        maxHits = 2
    else:
        maxHits = 3

    # ---------------------
    if disableNav == 0:
        # Process Unit Motion
        if botState == STATE_MOVING and sv_defs.gameTime > immobilizedTime[botIndex]:
            if tgtIndex > -1 and (
                    tgtDist <= 2.5 * bot.GetInventRange(botIndex, 0) or core.CvarGetValue('sv_duelserver')):
                angle = math.atan2(-tgtDir[0], tgtDir[1]) * 180.0 / 3.1415
            else:
                # Move toward WayPoint
                angle = math.atan2(-wayDir[0], wayDir[1]) * 180.0 / 3.1415
            bot.SetAngle(botIndex, ANGLE_YAW, angle)
            bot.SetMotion(botIndex, MOVE_FORWARD, 1)
            frame_playing_checkDodge()

            # NEVER sprint near WayPoint!
            if wayDist > 100:
                # Check Stamina Levels  - ToDo: Implement Leap for Beasts
                stamina = float(sv_defs.clientList_Stamina[botIndex]) / float(sv_defs.clientList_MaxStamina[botIndex])
                if stamina > 0.95:
                    bot.SetButton(botIndex, BUTTON_SPRINT, 1)
                if stamina < 0.70:
                    bot.SetButton(botIndex, BUTTON_SPRINT, 0)

            if sprinting == 1:
                bot.SetButton(botIndex, BUTTON_SPRINT, 1)

            # Do not affect navigation mesh
            bot.NavMeshSubtract(botIndex, 0)

        else:
            # Remain idle and face Target
            if tgtIndex > -1:
                angle = math.atan2(-tgtDir[0], tgtDir[1]) * 180.0 / 3.1415
                bot.SetAngle(botIndex, ANGLE_YAW, angle)
            bot.SetMotion(botIndex, MOVE_STOP, 1)

            # Create no-go area on navigation mesh
            bot.NavMeshSubtract(botIndex, 1)
    else:
        bot.SetMotion(botIndex, MOVE_FORWARD, 0)
        bot.SetMotion(botIndex, MOVE_BACKWARD, 0)
        bot.SetMotion(botIndex, MOVE_LEFT, 0)
        bot.SetMotion(botIndex, MOVE_RIGHT, 0)
        disableNavTimer += 1
        if disableNavTimer >= 10:
            disableNav = 0
            disableNavTimer = 0

    # -----------------------
    # Process Weapons Usage        
    bot.SetInventSel(botIndex, 0)  # Select Melee by default
    bot.SetButton(botIndex, BUTTON_WORK, 0)  # Not working by default

    # Own hit combo awareness
    botWState = bot.NavGetBotWState(botIndex)

    # Objective: Mine or Build
    if botGoal == GOAL_MINE or botGoal == GOAL_CONSTRUCT:
        # Ready to Work?
        if not botState == STATE_MOVING:
            bot.SetButton(botIndex, BUTTON_WORK, 1)
            bot.SwitchButton(botIndex, BUTTON_ATTACK)

    # Objective: Attack Something
    elif botGoal == GOAL_ATTACKMELEE:
        if tgtIndex > -1:
            # Is target a building (including base/outpost)?
            if sv_utils.is_building(tgtIndex):
                # Attack with Melee once in visible range
                if bot.NavTargetVisible(botIndex, 15.0):
                    bot.SwitchButton(botIndex, BUTTON_ATTACK)

            # Is target a client?                    
            elif sv_utils.is_client(tgtIndex):

                targetWState = bot.NavGetTargetWState(botIndex)
                if targetWState == 99:  # Being ressurected
                    # TODO: find new goal
                    if targetDiedTalk == 0:
                        happiness += 1
                        if core.CvarGetValue('sv_botTalk'):
                            if int(core.CvarGetValue('sv_botTalkFreq')) > 0:
                                rnd = random.randint(0, 100)
                                if rnd <= int(core.CvarGetValue('sv_botTalkFreq')):
                                    killTaunt(botIndex)
                            targetDiedTalk = 1
                            randomTauntTimer = 0
                    return
                else:
                    if targetDiedTalk == 1:
                        targetDiedTalk = 0

                # Far enough for Ranged Weapon? & Ranged Weapon Available and Ready?
                if tgtDist >= core.CvarGetValue('sv_botWeaponRangeMin') and bot.GetInventType(botIndex,
                                                                                              1) == INVTYPE_RANGED and bot.GetInventReady(
                        botIndex, 1):
                    # Select Ranged Weapon
                    bot.SetInventSel(botIndex, 1)

                    # Close enough to start Firing?
                    if tgtDist <= bot.GetInventRange(botIndex, 1):
                        # Does Weapon need charging?
                        if bot.GetInventCharge(botIndex, 1):
                            # Point 1deg above target
                            angle = 1.0 + math.asin(tgtDir[2]) * 180.0 / 3.1415
                            bot.SetAngle(botIndex, ANGLE_PITCH, angle)

                            # Start charging?
                            if not bot.GetButton(botIndex, BUTTON_ATTACK):
                                bot.SetButton(botIndex, BUTTON_ATTACK, 1)
                                stopShooting = 1
                            else:
                                # Are we fully charged up?
                                if sv_defs.clientList_Charge[botIndex] < 1.0:
                                    bot.SetButton(botIndex, BUTTON_ATTACK, 1)
                                else:
                                    # Is target within reasonable angle delta?
                                    delta = math.acos(wayDir2D.dot(tgtDir2D)) * 180.0 / 3.1415
                                    if delta > core.CvarGetValue('sv_botWeaponAccuracyAng'):
                                        bot.SetButton(botIndex, BUTTON_ATTACK, 1)
                                        stopShooting = 1
                                    else:
                                        # Let it rip!!!
                                        bot.SetButton(botIndex, BUTTON_ATTACK, 0)

                        # Otherwise shoot on sight!
                        else:
                            # Point straight at target
                            angle = math.asin(tgtDir[2]) * 180.0 / 3.1415
                            bot.SetAngle(botIndex, ANGLE_PITCH, angle)

                            # Is target within reasonable angle delta?
                            delta = math.acos(wayDir2D.dot(tgtDir2D)) * 180.0 / 3.1415
                            if delta > core.CvarGetValue('sv_botWeaponAccuracyAng'):
                                bot.SetButton(botIndex, BUTTON_ATTACK, 0)
                            else:
                                # Let it rip!!!
                                bot.SetButton(botIndex, BUTTON_ATTACK, 1)
                                stopShooting = 1

                # Use Melee once in Range
                else:
                    if core.CvarGetValue('sv_botTalk'):
                        randomTauntTimer += 1
                        if randomTauntTimer >= int(core.CvarGetValue('sv_botRandomTauntFreq')):
                            if int(core.CvarGetValue('sv_botTalkFreq')) > 0:
                                rnd = random.randint(0, 100)
                                if rnd <= int(core.CvarGetValue('sv_botTalkFreq')):
                                    randomTaunt(botIndex)
                                    randomTauntTimer = 0 - random.randint(0, int(
                                        core.CvarGetValue('sv_botRandomTauntFreq') / 3))

                    if stopShooting == 1:
                        stopShooting = 0
                        bot.SetInventSel(botIndex, 0)
                        bot.SetButton(botIndex, BUTTON_ATTACK, 0)
                        return

                    if botWState == -1:
                        return
                    # else: #failsafe experiment
                    #    if not bot.GetInventSel(botIndex) == 0:
                    #        stopShooting == 1
                    #        return
                    # Moved to beginning of combat -> targetWState = bot.NavGetTargetWState(botIndex)
                    # Moved to beginning of combat -> botWState = bot.NavGetBotWState(botIndex)
                    health = float(sv_defs.clientList_Health[botIndex]) / float(sv_defs.clientList_MaxHealth[botIndex])
                    targetHealth = float(sv_defs.clientList_Health[tgtIndex]) / float(
                        sv_defs.clientList_MaxHealth[tgtIndex])
                    stamina = sv_defs.clientList_Stamina[botIndex]  # /float(sv_defs.clientList_MaxStamina[botIndex])

                    # if targetWState == 99: #Being ressurected
                    #    return

                    sprinting = 0

                    if raceDesc == 'The Legion of Man':

                        if blocked == 1:
                            bot.SetMotion(botIndex, MOVE_LEFT, 0)
                            bot.SetMotion(botIndex, MOVE_RIGHT, 0)
                            if jumpDelay == 1 or jumped == 1:
                                jumpDelay = 0
                                jumpDelayTimer = 0
                                jumped = 0
                                bot.SetMotion(botIndex, MOVE_JUMP, 0)
                            if blockTimer >= core.CvarGetValue('sv_botHumanBlockDelay') or targetWState == -1:
                                bot.SetButton(botIndex, BUTTON_BLOCK, 0)
                                bot.SetButton(botIndex, BUTTON_ATTACK, 0)
                                blocked = 0
                                blockTimer = -1
                            return

                        if health < 0.6:
                            if botWState != 0:
                                if skillLevel == 0 or skillLevel == 1 or skillLevel == 8 or skillLevel == 9 or skillLevel == 10 or skillLevel == 11 or skillLevel == 12 or skillLevel == 13 or skillLevel == 14 or skillLevel == 15:
                                    if blocked == 0:
                                        bot.SetButton(botIndex, BUTTON_BLOCK, 1)
                                        blocked = 1
                                        blockTimer = 1000
                                    return
                            if blockTimer == -1 or targetWState == 0:
                                if targetWState != -1:
                                    slot = bot.SearchInvent(botIndex, 'human_medkit')
                                    if slot >= 0:
                                        activate_item(botIndex, slot)
                                        blockTimer = 0
                                        return
                            if health < 0.4:
                                if botWState == 0:
                                    slot = bot.SearchInvent(botIndex, 'human_medkit')
                                    if slot >= 0:
                                        activate_item(botIndex, slot)
                                        blockTimer = 0
                                        return
                                else:
                                    blocked = 0
                                    blockTimer = 0
                                    bot.SetButton(botIndex, BUTTON_BLOCK, 0)
                                    bot.SetButton(botIndex, BUTTON_ATTACK, 0)
                                    return

                        if jumpDelay == 1 and jumpDelayTimer >= 41:
                            jumpDelay = 0
                            jumpDelayTimer = 0
                            jumped = 1
                            bot.SetMotion(botIndex, MOVE_LEFT, 0)
                            bot.SetMotion(botIndex, MOVE_RIGHT, 0)
                            bot.SetMotion(botIndex, MOVE_JUMP, 1)
                            return

                        if jumped == 1:
                            jumpDelay = 0
                            jumpDelayTimer = 0
                            jumped = 0
                            bot.SetMotion(botIndex, MOVE_JUMP, 0)
                            return

                        type = skillLevel
                        if type == 0:
                            human_skilled(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
                        elif type == 1:
                            human_block_skilled(botIndex, targetWState, botWState, health, targetHealth, stamina,
                                                tgtDist)
                        elif type == 2:
                            human_block_noob(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
                        elif type == 3:
                            human_random_noob(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
                        elif type == 4:
                            human_noob(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
                        elif type == 5:
                            human_newbie(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
                        elif type == 6:
                            human_random_newbie(botIndex, targetWState, botWState, health, targetHealth, stamina,
                                                tgtDist)
                        elif type == 7:
                            human_slow_newbie(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
                        elif type == 8:
                            human_random_skilled(botIndex, targetWState, botWState, health, targetHealth, stamina,
                                                 tgtDist)
                        elif type == 9:
                            human_new(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
                        elif type == 10:
                            human_new_whirly(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
                        elif type == 11:
                            human_spammer(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
                        elif type == 12:
                            human_pro(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
                        elif type == 13:
                            human_random_pro(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
                        elif type == 14:
                            human_delayed_skilled(botIndex, targetWState, botWState, health, targetHealth, stamina,
                                                  tgtDist)
                        elif type == 15:
                            human_skilled_old(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
                        elif type == 16:
                            human_random(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
                        elif type == 17:
                            human_delayed_block_skilled(botIndex, targetWState, botWState, health, targetHealth,
                                                        stamina, tgtDist)
                        elif type < 0:
                            human_switch(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
                        else:
                            human_daebot(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
                    elif raceDesc == 'The Beast Horde':

                        type = skillLevel
                        if type == 0:
                            beast_cautious_skilled(botIndex, targetWState, botWState, health, targetHealth, stamina,
                                                   tgtDist)
                        elif type == 1:
                            beast_reckless_skilled(botIndex, targetWState, botWState, health, targetHealth, stamina,
                                                   tgtDist)
                        elif type == 2:
                            beast_newbie(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
                        elif type == 3:
                            beast_slow_newbie(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
                        elif type == 4:
                            beast_random_newbie(botIndex, targetWState, botWState, health, targetHealth, stamina,
                                                tgtDist)
                        elif type == 5:
                            beast_reckless_newbie(botIndex, targetWState, botWState, health, targetHealth, stamina,
                                                  tgtDist)
                        elif type == 6:
                            beast_cautious_newbie(botIndex, targetWState, botWState, health, targetHealth, stamina,
                                                  tgtDist)
                        elif type == 7:
                            beast_cautious_noob(botIndex, targetWState, botWState, health, targetHealth, stamina,
                                                tgtDist)
                        elif type == 8:
                            beast_reckless_noob(botIndex, targetWState, botWState, health, targetHealth, stamina,
                                                tgtDist)
                        elif type == 9:
                            beast_skilled_plus(botIndex, targetWState, botWState, health, targetHealth, stamina,
                                               tgtDist)
                        elif type == 10:
                            beast_reckless_plus(botIndex, targetWState, botWState, health, targetHealth, stamina,
                                                tgtDist)
                        elif type == 11:
                            beast_aim_test(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
                        elif type == 12:
                            beast_new(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
                        elif type == 13:
                            beast_unfair(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
                        elif type == 14:
                            beast_chaos(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
                        elif type == 15:
                            beast_cautious_chaos(botIndex, targetWState, botWState, health, targetHealth, stamina,
                                                 tgtDist)
                        elif type == 16:
                            beast_close_chaos(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
                        elif type == 17:
                            beast_chaos_plus(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
                        elif type == 18:
                            beast_timed_chaos(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
                        elif type == 19:
                            beast_bobbot(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
                        elif type == 20:
                            beast_bobbot_slow(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
                        elif type == 21:
                            beast_aim(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
                        elif type == 22:
                            beast_pro(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
                        elif type == 23:
                            beast_random(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
                        elif type < 0:
                            beast_switch(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
                        else:
                            beast_daebot(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)

                        if leapDelay == 1:
                            if leapDelayTimer >= 20:
                                bot.SetMotion(botIndex, MOVE_FORWARD, 1)
                                bot.SetMotion(botIndex, MOVE_BACKWARD, 0)
                                bot.SetMotion(botIndex, MOVE_STOP, 0)
                                bot.SwitchButton(botIndex, BUTTON_BLOCK)
                                if leapDelayTimer >= 40:
                                    leapDelay = 0
                                    leapDelayTimer = 0
                                    bot.SetButton(botIndex, BUTTON_BLOCK, 0)

                        if leapBackDelay == 1:
                            if leapBackDelayTimer >= 20:
                                bot.SetMotion(botIndex, MOVE_FORWARD, 0)
                                bot.SetMotion(botIndex, MOVE_BACKWARD, 1)
                                bot.SetMotion(botIndex, MOVE_STOP, 0)
                                bot.SwitchButton(botIndex, BUTTON_BLOCK)
                                if leapBackDelayTimer >= 40:
                                    leapBackDelay = 0
                                    leapBackDelayTimer = 0
                                    bot.SetButton(botIndex, BUTTON_BLOCK, 0)

            # Attack anything else with Melee
            else:
                # Close enough to start Hacking?
                if tgtDist <= 2.0 * bot.GetInventRange(botIndex, 0):
                    bot.SwitchButton(botIndex, BUTTON_ATTACK)

                    # Otherwise stay put
    else:
        bot.SetButton(botIndex, BUTTON_ATTACK, 0)
        bot.SetButton(botIndex, BUTTON_BLOCK, 0)
        bot.SetMotion(botIndex, MOVE_BACKWARD, 0)


# -------------------------------
def frame_playing_checkDodge():
    # botCheckDodgeRangeMin = 0
    # Need to know the Race first
    raceDesc = sv_defs.teamList_RaceDesc[sv_defs.clientList_Team[botIndex]]
    if raceDesc == 'The Legion of Man':
        botCheckDodgeRangeMin = 0
    else:
        botCheckDodgeRangeMin = core.CvarGetValue('sv_botCheckDodgeRangeMin')

    # NO dodging near waypoints!!
    if wayDist <= botCheckDodgeRangeMin:
        bot.SetMotion(botIndex, MOVE_LEFT, 0)
        bot.SetMotion(botIndex, MOVE_RIGHT, 0)
        return

    # NO dodging while bridging!!
    if bot.NavIsBridging(botIndex):
        bot.SetMotion(botIndex, MOVE_LEFT, 0)
        bot.SetMotion(botIndex, MOVE_RIGHT, 0)
        return

        # Check Dodge Time (prevents becoming a sitting duck!)
    global lastCheckDodge
    if lastCheckDodge[botIndex] + core.CvarGetValue('sv_botCheckDodgeFreq') < sv_defs.gameTime:
        lastCheckDodge[botIndex] = sv_defs.gameTime
        bot.SetMotion(botIndex, MOVE_LEFT, 0)
        bot.SetMotion(botIndex, MOVE_RIGHT, 0)

        # When fighting clients, dodge continuously...
        if botGoal == GOAL_ATTACKMELEE and tgtIndex > -1 and sv_utils.is_client(
                tgtIndex) and tgtDist < core.CvarGetValue('sv_botCheckDodgeRangeMax'):
            if tgtDist > botCheckDodgeRangeMin:
                rnd = random.randint(0, 2)
                if rnd == 0:
                    bot.SetMotion(botIndex, MOVE_LEFT, 1)
                if rnd == 1:
                    bot.SetMotion(botIndex, MOVE_RIGHT, 1)
        # Otherwise check dodge chance
        elif random.random() < core.CvarGetValue('sv_botCheckDodgeChance'):
            if random.randint(0, 1) == 0:
                bot.SetMotion(botIndex, MOVE_LEFT, 1)
            else:
                bot.SetMotion(botIndex, MOVE_RIGHT, 1)


# -------------------------------
def frame_playing_checkItems():
    global isSaccing

    # Need to know the Race first
    raceDesc = sv_defs.teamList_RaceDesc[sv_defs.clientList_Team[botIndex]]

    # Process Items Usage (in order of importance)
    if raceDesc == 'The Legion of Man':

        # Need Medkit boost?
        slot = bot.SearchInvent(botIndex, 'human_medkit')
        if slot >= 0 and (
            float(sv_defs.clientList_Health[botIndex]) / float(sv_defs.clientList_MaxHealth[botIndex])) < 0.6 and \
                (botGoal != GOAL_ATTACKMELEE or tgtDist > core.CvarGetValue('sv_botWeaponRangeMin')):
            activate_item(botIndex, slot)

        # Need Target for Items below
        if tgtIndex < 0:
            return

        # Try to drop Demolition Pack near Buildings
        slot = bot.SearchInvent(botIndex, 'human_demo_pack')
        demoDist = core.CvarGetValue('sv_botHumanDemoPackDist')
        if slot >= 0 and botGoal == GOAL_ATTACKMELEE and sv_utils.is_building(tgtIndex) and bot.NavTargetVisible(
                botIndex, demoDist):
            activate_item(botIndex, slot)

        # Try to use Disruptor on Spires
        global immobilizedTime
        slot = bot.SearchInvent(botIndex, 'human_disruptor')
        if slot >= 0 and botGoal == GOAL_ATTACKMELEE and tgtDist < core.CvarGetValue('sv_botHumanDisruptorDist') and \
                        sv_defs.objectList_Name[tgtIndex] == 'beast_fire_spire':
            # Point 15deg above target & immobilize client
            angle = 15.0 + math.asin(tgtDir[2]) * 180.0 / 3.1415
            bot.SetAngle(botIndex, ANGLE_PITCH, angle)
            immobilizedTime[botIndex] = sv_defs.gameTime + int(core.CvarGetValue('sv_botHumanDisruptorDelay'))
            activate_item(botIndex, slot)

    elif raceDesc == 'The Beast Horde':

        # Need Target for Items below
        if tgtIndex < 0:
            return

        # Try using Invisibility when fighting Clients
        slot = bot.SearchInvent(botIndex, 'beast_camouflage')
        if slot >= 0 and botGoal == GOAL_ATTACKMELEE and sv_utils.is_client(tgtIndex):
            activate_item(botIndex, slot)

        # Try using Wind Shield near Buildings
        slot = bot.SearchInvent(botIndex, 'beast_protect')
        if slot >= 0 and botGoal == GOAL_ATTACKMELEE and sv_utils.is_building(tgtIndex) and tgtDist < core.CvarGetValue(
                'sv_botBeastProtectDist'):
            activate_item(botIndex, slot)

        # Try using Sacrifice near Buildings
        slot = bot.SearchInvent(botIndex, 'beast_immolate')
        if slot >= 0 and botGoal == GOAL_ATTACKMELEE and sv_utils.is_building(tgtIndex) and tgtDist < core.CvarGetValue(
                'sv_botBeastSacrificeDist'):
            isSaccing = 1
            activate_item(botIndex, slot)

    elif raceDesc == 'Shogunate':

        # Need Medkit boost?
        slot = bot.SearchInvent(botIndex, 'human_medkit')
        if slot >= 0 and (
            float(sv_defs.clientList_Health[botIndex]) / float(sv_defs.clientList_MaxHealth[botIndex])) < 0.6 and \
                (botGoal != GOAL_ATTACKMELEE or tgtDist > core.CvarGetValue('sv_botWeaponRangeMin')):
            activate_item(botIndex, slot)

        # Need Target for Items below
        if tgtIndex < 0:
            return

            # Try to drop Explosives near Buildings
        slot = bot.SearchInvent(botIndex, 'human_explosives')
        demoDist = core.CvarGetValue('sv_botHumanDemoPackDist')
        if slot >= 0 and botGoal == GOAL_ATTACKMELEE and sv_utils.is_building(tgtIndex) and bot.NavTargetVisible(
                botIndex, demoDist):
            activate_item(botIndex, slot)


# -------------------------------
def frame_dead():
    # Dead Bots do not claim Dibs anymore
    set_dibs(botIndex, -1)

    # Press Attack Button on/off until Load-out
    bot.SwitchButton(botIndex, BUTTON_ATTACK)


# -----------#----------------------#-----------#
# -----------# Some Useful Routines #-----------#
# -----------#----------------------#-----------#

def set_dibs(botIndex, objIndex):
    global lastDibs
    global objDibber

    # Clear existing dib (if any)
    if lastDibs[botIndex] > -1:
        if objDibber[lastDibs[botIndex]] == botIndex:
            objDibber[lastDibs[botIndex]] = -1

    # Set new dib
    lastDibs[botIndex] = objIndex
    if lastDibs[botIndex] > -1:
        objDibber[lastDibs[botIndex]] = botIndex


# -------------------------------
def activate_item(botIndex, slotIndex):
    # Safety Check
    if slotIndex < 0:
        return 0

    # Is item ready?
    if not bot.GetInventReady(botIndex, slotIndex):
        return 0

    # Try selecting this item 
    bot.SetInventSel(botIndex, slotIndex)

    # Is item selected now?
    if slotIndex == bot.GetInventSel(botIndex):
        # Does item need charging?
        if bot.GetInventCharge(botIndex, slotIndex):
            # Are we fully charged up?
            if sv_defs.clientList_Charge[botIndex] < 1.0:
                bot.SetButton(botIndex, BUTTON_ATTACK, 1)
            # Then release item                
            else:
                bot.SetButton(botIndex, BUTTON_ATTACK, 0)

                # Then simply activate item
        else:
            bot.SetButton(botIndex, BUTTON_ATTACK, 1)

    # Otherwise stop using current Weapon
    else:
        bot.SetButton(botIndex, BUTTON_ATTACK, 0)

    return 1


# -----------#----------------------#-----------#
# -----------# AI Styles and Levels #-----------#
# -----------#----------------------#-----------#

# -----------#----------------------#-----------#
# -----------#    HUMAN PERSONAE    #-----------#
# -----------#----------------------#-----------#

# A human bot that adjusts its skill level to the enemy's prowess
def human_daebot(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist):
    global happiness

    if happiness > 0:
        if happiness < 5:
            human_random_noob(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
        elif happiness < 10:
            human_noob(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
        elif happiness < 15:
            human_block_noob(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
        elif happiness < 20:
            human_random_newbie(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
        else:
            human_slow_newbie(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
    elif happiness < 0:
        if happiness > -5:
            human_random_noob(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
        elif happiness > -10:
            human_new(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
        elif happiness > -15:
            human_skilled(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
        elif happiness > -20:
            human_spammer(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
        else:
            human_pro(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
    else:
        human_random_noob(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)


# Block circular, counter and freeswing the best you can!
def human_new_whirly(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist):
    global maxHits
    global blocked
    global blockTimer
    global sprinting

    if tgtDist <= 2.0 * bot.GetInventRange(botIndex, 0):
        if targetWState == 17:
            rnd = random.randint(0, 3)
            if rnd < 3 or botWState >= maxHits:
                Hblock_whirly(botIndex)
            else:
                Hattack_B(botIndex)
        elif targetWState >= 1 and targetWState <= 4:
            if botWState == maxHits and targetHealth < 0.3:
                Hattack_F(botIndex)
            else:
                Hblock_whirly(botIndex)
        elif targetWState == -1:
            if blocked == 1:
                bot.SetButton(botIndex, BUTTON_BLOCK, 0)
                blocked = 0
                blockTimer = -1
                return
            if tgtDist <= 1.5 * bot.GetInventRange(botIndex, 0):
                Hattack_F(botIndex)
        else:
            if botWState < maxHits:
                Hattack_F(botIndex)
    else:
        Hattack_F(botIndex)


# Block, counter and freeswing the best you can!
def human_new(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist):
    global maxHits
    global blocked
    global blockTimer
    global sprinting

    if tgtDist <= 2.0 * bot.GetInventRange(botIndex, 0):
        if targetWState == 17:
            rnd = random.randint(0, 3)
            if rnd < 3 or botWState >= maxHits:
                Hblock(botIndex)
            else:
                Hattack_B(botIndex)
        elif targetWState >= 1 and targetWState <= 4:
            if botWState == maxHits and targetHealth < 0.3:

                Hattack_F(botIndex)
            else:
                Hblock(botIndex)
        elif targetWState == -1:
            if blocked == 1:
                bot.SetButton(botIndex, BUTTON_BLOCK, 0)
                blocked = 0
                blockTimer = -1
                return
            if tgtDist <= 1.5 * bot.GetInventRange(botIndex, 0):
                Hattack_F(botIndex)
        else:
            if botWState < maxHits:
                Hattack_F(botIndex)
    else:
        Hattack_F(botIndex)


# Block, counter and freeswing the best you can! + sprint jump
def human_skilled(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist):
    global maxHits
    global blocked
    global blockTimer
    global sprinting
    global jumpDelay

    if tgtDist <= 3.0 * bot.GetInventRange(botIndex, 0):
        if targetWState == 17:
            rnd = random.randint(0, 3)
            if rnd < 3 or botWState >= maxHits:
                Hblock(botIndex)
            else:
                Hattack_B(botIndex)
        elif targetWState >= 1 and targetWState <= 4:
            if botWState == 1 and tgtDist <= 1.5 * bot.GetInventRange(botIndex, 0) and health > 0.4:
                Hattack_F(botIndex)
            else:
                if botWState == maxHits and tgtDist <= 1.3 * bot.GetInventRange(botIndex, 0) and targetHealth < 0.3:
                    Hattack_F(botIndex)
                else:
                    Hblock(botIndex)
        elif targetWState == -1:
            if blocked == 1:
                bot.SetButton(botIndex, BUTTON_BLOCK, 0)
                blocked = 0
                blockTimer = -1
                return
            if tgtDist <= 1.5 * bot.GetInventRange(botIndex, 0):
                sprinting = 1
                jumpDelay = 1
                Hattack_F(botIndex)
        else:
            if botWState < maxHits:
                Hattack_F(botIndex)


# Block, counter and freeswing the best you can! (before sprint jump)
def human_skilled_old(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist):
    global maxHits
    global blocked
    global blockTimer
    global sprinting
    global jumpDelay

    if tgtDist <= 3.0 * bot.GetInventRange(botIndex, 0):
        if targetWState == 17:
            rnd = random.randint(0, 3)
            if rnd < 3 or botWState >= maxHits:
                Hblock(botIndex)
            else:
                Hattack_B(botIndex)
        elif targetWState >= 1 and targetWState <= 4:
            if botWState == 1 and tgtDist <= 1.5 * bot.GetInventRange(botIndex, 0) and health > 0.4:
                Hattack_F(botIndex)
            else:
                if botWState == maxHits and tgtDist <= 1.3 * bot.GetInventRange(botIndex, 0) and targetHealth < 0.3:
                    Hattack_F(botIndex)
                else:
                    Hblock(botIndex)
        elif targetWState == -1:
            if botWState < maxHits:
                Hattack_F(botIndex)
        else:
            if botWState < maxHits:
                Hattack_F(botIndex)


# Block, counter and freeswing averagely...
def human_delayed_skilled(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist):
    global maxHits
    global blocked
    global blockTimer
    global sprinting
    global jumpDelay
    global waitMove
    global waitMoveTimer
    global disableNav
    global disableNavTimer

    if waitMove == 1:
        if waitMoveTimer >= 20:
            waitMove = 0
            waitMoveTimer = 0
        if disableNav == 0:
            if targetWState > 0 and targetWState < 5:
                disableNav = 1
                disableNavTimer = -10  # random.randint(-20,-10)
        return

    if tgtDist <= 3.0 * bot.GetInventRange(botIndex, 0):
        if targetWState == 17:
            rnd = random.randint(0, 3)
            if rnd < 3 or botWState >= maxHits:
                Hblock(botIndex)
            else:
                Hattack_B(botIndex)
        elif targetWState >= 1 and targetWState <= 4:
            if botWState == 1 and tgtDist <= 1.5 * bot.GetInventRange(botIndex, 0) and health > 0.4:
                Hattack_F(botIndex)
            else:
                if botWState == maxHits and tgtDist <= 1.3 * bot.GetInventRange(botIndex, 0) and targetHealth < 0.3:
                    Hattack_F(botIndex)
                else:
                    Hblock(botIndex)
        elif targetWState == -1:
            if blocked == 1:
                bot.SetButton(botIndex, BUTTON_BLOCK, 0)
                blocked = 0
                blockTimer = -1
                return
            if tgtDist <= 1.5 * bot.GetInventRange(botIndex, 0):
                sprinting = 1
                jumpDelay = 1
                Hattack_F(botIndex)
        else:
            if botWState < maxHits:
                Hattack_F(botIndex)

    waitMove = 1


# Pro. Nuff said.
def human_pro(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist):
    global maxHits
    global blocked
    global blockTimer
    global sprinting
    global jumpDelay
    global jumpDelayTimer
    global waitMove
    global waitMoveTimer

    bot.SetMotion(botIndex, MOVE_BACKWARD, 0)

    if tgtDist <= 2.0 * bot.GetInventRange(botIndex, 0):
        if targetWState == 17:
            rnd = random.randint(0, 3)
            if rnd < 3 or botWState >= maxHits:
                Hblock(botIndex)
            else:
                Hattack_B(botIndex)
        elif targetWState >= 1 and targetWState <= 4:
            if botWState == 1 and tgtDist <= 1.5 * bot.GetInventRange(botIndex, 0) and health > 0.4:
                Hattack_F(botIndex)
            else:
                if botWState == maxHits and tgtDist <= 1.3 * bot.GetInventRange(botIndex, 0) and targetHealth < 0.3:
                    Hattack_F(botIndex)
                else:
                    Hblock(botIndex)
        elif targetWState == -1:
            if waitMove == 1 and waitMoveTimer >= 40:
                waitMove = 0
                waitMoveTimer = 0
            if blocked == 1:
                bot.SetButton(botIndex, BUTTON_BLOCK, 0)
                blocked = 0
                blockTimer = -1
                return
            if waitMove == 0:
                if tgtDist <= 1.0 * bot.GetInventRange(botIndex, 0):
                    sprinting = 1
                    Hattack_F(botIndex)
                elif tgtDist <= 1.1 * bot.GetInventRange(botIndex, 0):
                    sprinting = 1
                    jumpDelay = 1
                    Hattack_F(botIndex)
                elif tgtDist <= 1.6 * bot.GetInventRange(botIndex, 0):
                    jumpDelay = 1
                    sprinting = 1
                else:
                    waitMove = 1
                    jumpDelay = 0
                    jumpDelayTimer = 0
                    bot.SetMotion(botIndex, MOVE_FORWARD, 0)
            else:
                sprinting = 1
                jumpDelay = 0
                jumpDelayTimer = 0
                bot.SetMotion(botIndex, MOVE_FORWARD, 1)
        else:
            if tgtDist <= 0.5 * bot.GetInventRange(botIndex, 0):
                sprinting = 1
                Hattack_F(botIndex)
            elif tgtDist <= 1.0 * bot.GetInventRange(botIndex, 0):
                if botWState < maxHits and health > 0.4:
                    sprinting = 1
                    Hattack_F(botIndex)
                elif targetHealth < 0.3:
                    sprinting = 1
                    Hattack_F(botIndex)
            elif botWState != 0:
                sprinting = 1


# Pro-ish...sometimes
def human_random_pro(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist):
    global maxHits
    global blocked
    global blockTimer
    global attackDelay
    global attackDelayTimer
    global sprinting
    global jumpDelay
    global jumpDelayTimer

    if tgtDist <= 3.0 * bot.GetInventRange(botIndex, 0):
        if targetWState == 17:
            rnd = random.randint(0, 3)
            if rnd < 3 or botWState >= maxHits:
                Hblock(botIndex)
            else:
                Hattack_B(botIndex)
        elif targetWState >= 1 and targetWState <= 4:
            rnd = random.randint(0, 4)
            if rnd == 0:
                if tgtDist <= 1.5 * bot.GetInventRange(botIndex, 0):
                    attackDelay = 1
                    if attackDelayTimer >= 20:
                        Hattack_F(botIndex)
                        rnd = random.randint(0, 30)
                        attackDelayTimer = -10 + rnd
                elif tgtDist >= 3.5 * bot.GetInventRange(botIndex, 0):
                    attackDelay = 0
                    rnd = random.randint(0, 30)
                    attackDelayTimer = -10 + rnd
            else:
                Hblock(botIndex)
        elif targetWState == -1:
            if blocked == 1:
                bot.SetButton(botIndex, BUTTON_BLOCK, 0)
                blocked = 0
                blockTimer = -1
                return
            if tgtDist <= 0.9 * bot.GetInventRange(botIndex, 0):
                sprinting = 1
                Hattack_F(botIndex)
            elif tgtDist <= 1.3 * bot.GetInventRange(botIndex, 0):
                sprinting = 1
                jumpDelay = 1
                Hattack_F(botIndex)
            elif tgtDist <= 1.7 * bot.GetInventRange(botIndex, 0):
                sprinting = 1
                jumpDelay = 1
            else:
                jumpDelay = 0
                jumpDelayTimer = 0
                bot.SetMotion(botIndex, MOVE_FORWARD, 0)
                bot.SetMotion(botIndex, MOVE_BACKWARD, 1)
        else:
            if botWState < maxHits:
                Hattack_F(botIndex)


# Block, counter and freeswing ...semi-randomly!
def human_random_skilled(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist):
    global maxHits
    global blocked
    global blockTimer
    global attackDelay
    global attackDelayTimer
    global sprinting
    global jumpDelay

    if tgtDist <= 3.0 * bot.GetInventRange(botIndex, 0):
        if targetWState == 17:
            rnd = random.randint(0, 3)
            if rnd < 3 or botWState >= maxHits:
                Hblock(botIndex)
            else:
                Hattack_B(botIndex)
        elif targetWState >= 1 and targetWState <= 4:
            rnd = random.randint(0, 4)
            if rnd == 0:
                if tgtDist <= 1.5 * bot.GetInventRange(botIndex, 0):
                    attackDelay = 1
                    if attackDelayTimer >= 20:
                        Hattack_F(botIndex)
                        rnd = random.randint(0, 30)
                        attackDelayTimer = -10 + rnd
                elif tgtDist >= 3.5 * bot.GetInventRange(botIndex, 0):
                    attackDelay = 0
                    rnd = random.randint(0, 30)
                    attackDelayTimer = -10 + rnd
            else:
                Hblock(botIndex)
        elif targetWState == -1:
            if blocked == 1:
                bot.SetButton(botIndex, BUTTON_BLOCK, 0)
                blocked = 0
                blockTimer = -1
                return
            if tgtDist <= 1.5 * bot.GetInventRange(botIndex, 0):
                sprinting = 1
                jumpDelay = 1
                Hattack_F(botIndex)
        else:
            if botWState < maxHits:
                Hattack_F(botIndex)


# Only attack after blocking + sprint jump
def human_block_skilled(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist):
    global maxHits
    global blocked
    global blockTimer
    global sprinting
    global jumpDelay

    if tgtDist <= 3.0 * bot.GetInventRange(botIndex, 0):
        if targetWState == -1:
            if blocked == 1:
                bot.SetButton(botIndex, BUTTON_BLOCK, 0)
                blocked = 0
                blockTimer = -1
                return
            if tgtDist <= 1.5 * bot.GetInventRange(botIndex, 0):
                sprinting = 1
                jumpDelay = 1
                Hattack_F(botIndex)
        else:
            Hblock(botIndex)


# Only attack after blocking + sprint jump (averagely...)
def human_delayed_block_skilled(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist):
    global maxHits
    global blocked
    global blockTimer
    global sprinting
    global jumpDelay
    global waitMove
    global waitMoveTimer
    global disableNav
    global disableNavTimer

    if waitMove == 1:
        if waitMoveTimer >= 20:
            waitMove = 0
            waitMoveTimer = 0
        if disableNav == 0:
            if targetWState > 0 and targetWState < 5:
                disableNav = 1
                disableNavTimer = -10  # random.randint(-20,-10)
        return

    if tgtDist <= 3.0 * bot.GetInventRange(botIndex, 0):
        if targetWState == -1:
            if blocked == 1:
                bot.SetButton(botIndex, BUTTON_BLOCK, 0)
                blocked = 0
                blockTimer = -1
                return
            if tgtDist <= 1.5 * bot.GetInventRange(botIndex, 0):
                sprinting = 1
                jumpDelay = 1
                Hattack_F(botIndex)
        else:
            Hblock(botIndex)

    waitMove = 1


# Only attack after blocking
def human_block_noob(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist):
    global maxHits
    global blocked
    global blockTimer
    global sprinting

    if tgtDist <= 3.0 * bot.GetInventRange(botIndex, 0):
        if targetWState == -1:
            if blocked == 1:
                bot.SetButton(botIndex, BUTTON_BLOCK, 0)
                blocked = 0
                blockTimer = -1
                return
            if tgtDist <= 1.5 * bot.GetInventRange(botIndex, 0):
                Hattack_F(botIndex)
        else:
            Hblock(botIndex)


# Randomly (with random delay) attack and block
def human_random_noob(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist):
    global attackDelay
    global attackDelayTimer
    global sprinting

    rnd = random.randint(0, 2)
    if rnd == 0:
        Hblock(botIndex)
    else:
        if tgtDist <= 1.5 * bot.GetInventRange(botIndex, 0):
            attackDelay = 1
            if attackDelayTimer >= 20:
                Hattack_F(botIndex)
                rnd = random.randint(0, 30)
                attackDelayTimer = -10 + rnd
        elif tgtDist >= 3.5 * bot.GetInventRange(botIndex, 0):
            attackDelay = 0
            rnd = random.randint(0, 30)
            attackDelayTimer = -10 + rnd


# Randomly attack and block
def human_noob(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist):
    global sprinting
    global jumped

    rnd = random.randint(0, 2)
    if rnd == 0:
        Hblock(botIndex)
    else:
        if tgtDist <= 1.5 * bot.GetInventRange(botIndex, 0):
            Hattack_F(botIndex)

    rnd = random.randint(0, 3)
    if rnd == 0:
        if jumped == 0:
            jumped = 1
            bot.SetMotion(botIndex, MOVE_JUMP, 1)


# Only attack
def human_newbie(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist):
    global sprinting

    if tgtDist <= 1.5 * bot.GetInventRange(botIndex, 0):
        Hattack_F(botIndex)


# Only attack, but with random delays
def human_random_newbie(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist):
    global attackDelay
    global attackDelayTimer
    global sprinting

    if tgtDist <= 1.5 * bot.GetInventRange(botIndex, 0):
        attackDelay = 1
        if attackDelayTimer >= 40:
            Hattack_F(botIndex)
            rnd = random.randint(0, 20)
            attackDelayTimer = 0 - rnd
    elif tgtDist >= 3.5 * bot.GetInventRange(botIndex, 0):
        attackDelay = 0
        rnd = random.randint(0, 20)
        attackDelayTimer = 0 - rnd


# Only attack, but delayed/slowly
def human_slow_newbie(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist):
    global maxHits
    global blocked
    global blockTimer
    global attackDelay
    global attackDelayTimer
    global sprinting

    if tgtDist <= 1.5 * bot.GetInventRange(botIndex, 0):
        attackDelay = 1
        if attackDelayTimer >= 60:
            Hattack_F(botIndex)
            attackDelayTimer = 0
            attackDelay = 0
    elif tgtDist >= 3.5 * bot.GetInventRange(botIndex, 0):
        attackDelay = 0
        attackDelayTimer = 0


# Block (spam!), counter and freeswing the best you can! + sprint jump
def human_spammer(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist):
    global maxHits
    global blocked
    global blockTimer
    global sprinting
    global jumpDelay

    if tgtDist <= 3.0 * bot.GetInventRange(botIndex, 0):
        if targetWState == 17:
            rnd = random.randint(0, 3)
            if rnd < 3 or botWState >= maxHits:
                Hblock(botIndex)
            else:
                Hattack_B(botIndex)
        elif targetWState >= 1 and targetWState <= 4:
            if botWState == 1 and tgtDist <= 1.5 * bot.GetInventRange(botIndex, 0) and health > 0.4:
                Hattack_F(botIndex)
            else:
                if botWState <= maxHits and tgtDist <= 1.3 * bot.GetInventRange(botIndex, 0) and targetHealth < 0.3:
                    Hattack_F(botIndex)
                else:
                    Hblock(botIndex)
        elif targetWState == -1:
            if blocked == 1:
                bot.SetButton(botIndex, BUTTON_BLOCK, 0)
                blocked = 0
                blockTimer += 30
                return
            if tgtDist <= 1.5 * bot.GetInventRange(botIndex, 0):
                sprinting = 1
                jumpDelay = 1
                Hattack_F(botIndex)
        else:
            if botWState < maxHits:
                Hattack_F(botIndex)


def human_random(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist):
    global lastType
    global bobbotTimer

    bobbotTimer += 1
    if bobbotTimer >= 20:
        lastType = random.randint(0, 14)
        bobbotTimer = 0

    type = lastType
    if type == 0:
        human_skilled(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
    elif type == 1:
        human_block_skilled(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
    elif type == 2:
        human_block_noob(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
    elif type == 3:
        human_random_noob(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
    elif type == 4:
        human_noob(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
    elif type == 5:
        human_newbie(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
    elif type == 6:
        human_random_newbie(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
    elif type == 7:
        human_slow_newbie(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
    elif type == 8:
        human_random_skilled(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
    elif type == 9:
        human_new(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
    elif type == 10:
        human_new_whirly(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
    elif type == 11:
        human_spammer(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
    elif type == 12:
        human_pro(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
    elif type == 13:
        human_random_pro(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
    elif type == 14:
        human_delayed_skilled(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)


def human_switch(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist):
    global lastType

    type = lastType
    if type == 0:  # H0
        human_skilled(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
    elif type == 1:  # H1
        human_block_skilled(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
    elif type == 2:  # H3
        human_random_noob(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
    elif type == 3:  # H5
        human_newbie(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
    elif type == 4:  # H8
        human_random_skilled(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
    elif type == 5:  # H9
        human_new(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
    elif type == 6:  # H12
        human_pro(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
    elif type == 7:  # H13
        human_random_pro(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)


# -----------#----------------------#-----------#
# -----------#     HUMAN MOVES      #-----------#
# -----------#----------------------#-----------#

def Hblock(botIndex):
    global blocked
    global blockTimer
    global jumpDelay
    global jumpDelayTimer
    bot.SetButton(botIndex, BUTTON_BLOCK, 1)
    if blocked == 0:
        blocked = 1
        blockTimer = 0
        jumpDelay = 0
        jumpDelayTimer = 0


def Hblock_whirly(botIndex):
    global blocked
    global blockTimer
    global jumpDelay
    global jumpDelayTimer
    angle = random.randint(-180, 180) + math.atan2(-tgtDir[0], tgtDir[1]) * 180.0 / 3.1415
    bot.SetAngle(botIndex, ANGLE_YAW, angle)
    bot.SetButton(botIndex, BUTTON_BLOCK, 1)
    if blocked == 0:
        blocked = 1
        blockTimer = 0
        jumpDelay = 0
        jumpDelayTimer = 0


def Hattack_F(botIndex):
    bot.SetButton(botIndex, BUTTON_BLOCK, 0)
    bot.SwitchButton(botIndex, BUTTON_ATTACK)
    bot.SetMotion(boxIndex, MOVE_BACKWARD, 0)
    bot.SetMotion(boxIndex, MOVE_FORWARD, 1)


def Hattack_B(botIndex):
    bot.SetButton(botIndex, BUTTON_BLOCK, 0)
    bot.SwitchButton(botIndex, BUTTON_ATTACK)
    bot.SetMotion(boxIndex, MOVE_BACKWARD, 1)
    bot.SetMotion(boxIndex, MOVE_FORWARD, 0)


# -----------#----------------------#-----------#
# -----------#    BEAST PERSONAE    #-----------#
# -----------#----------------------#-----------#

# A beast bot that adjusts its skill level to the enemy's prowess
def beast_daebot(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist):
    global happiness

    if happiness > 0:
        if happiness < 5:
            beast_cautious_noob(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
        elif happiness < 10:
            beast_new(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
        elif happiness < 15:
            beast_cautious_newbie(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
        elif happiness < 20:
            beast_random_newbie(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
        else:
            beast_slow_newbie(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
    elif happiness < 0:
        if happiness > -5:
            beast_chaos(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
        elif happiness > -10:
            beast_cautious_skilled(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
        elif happiness > -15:
            beast_bobbot(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
        elif happiness > -20:
            beast_reckless_skilled(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
        else:
            beast_unfair(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
    else:
        beast_cautious_noob(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)


# Wild leaping beast (best with unlimited stamina)
def beast_unfair(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist):
    if stamina > 1700:
        if botWState < 3:
            bot.SetMotion(botIndex, MOVE_BACKWARD, 0)
            rnd = random.randint(0, 3)
            if rnd == 0:
                Battack_leap_Fangle(botIndex, -50)
            elif rnd == 1:
                Battack_leap_Fangle(botIndex, 50)
            elif rnd == 2:
                Battack_leap_FL(botIndex)
            elif rnd == 3:
                Battack_leap_FR(botIndex)
            else:
                Bleap_B(botIndex)
        elif tgtDist <= 1.2 * bot.GetInventRange(botIndex, 0):
            Bleap_B(botIndex)
    else:
        Bmove_B(botIndex)


# Attacks skillfully with little regard to own safety, though slower than reckless
def beast_new(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist):
    if tgtDist <= 1.0 * bot.GetInventRange(botIndex, 0):
        rnd = random.randint(0, 2)
        if rnd == 0:
            if stamina > 2200:
                Battack_leap_L(botIndex)
            else:
                Bmove_L(botIndex)
        elif rnd == 1:
            if stamina > 2200:
                Battack_leap_B(botIndex)
            else:
                Bmove_B(botIndex)
        elif rnd == 2:
            if stamina > 2200:
                Battack_leap_R(botIndex)
            else:
                Bmove_R(botIndex)
    elif tgtDist <= 2.0 * bot.GetInventRange(botIndex, 0):
        rnd = random.randint(0, 5)
        if rnd == 0:
            if targetWState == 17:
                if stamina > 2200:
                    rnd = random.randint(0, 5)
                    if rnd == 0:
                        Battack_leap_Fangle(botIndex, -50)
                    elif rnd == 1:
                        Battack_leap_Fangle(botIndex, 50)
                    elif rnd == 2:
                        Battack_leap_Fangle(botIndex, -10)
                    elif rnd == 3:
                        Battack_leap_Fangle(botIndex, 10)
                    elif rnd == 4:
                        Battack_leap_FL(botIndex)
                    elif rnd == 5:
                        Battack_leap_FR(botIndex)
                else:
                    Bmove_B(botIndex)
            elif targetWState >= 1 and targetWState <= 4:
                if tgtDist >= bot.GetInventRange(botIndex, 0):
                    if stamina > 2200:
                        Battack_leap_F(botIndex)
                    else:
                        Battack_B(botIndex)
                else:
                    if stamina > 2200:
                        rnd = random.randint(0, 1)
                        if rnd == 0:
                            Battack_leap_FL(botIndex)
                        elif rnd == 1:
                            Battack_leap_FR(botIndex)
                    else:
                        Battack_F(botIndex)
            else:
                if stamina > 2200:
                    rnd = random.randint(0, 1)
                    if rnd == 0:
                        Battack_leap_Fangle(botIndex, -50)
                    elif rnd == 1:
                        Battack_leap_Fangle(botIndex, 50)
                else:
                    Battack_F(botIndex)
        else:
            bot.SetMotion(botIndex, MOVE_BACKWARD, 0)
            bot.SetMotion(botIndex, MOVE_FORWARD, 0)
            bot.SetMotion(botIndex, MOVE_LEFT, 1)
            bot.SetMotion(botIndex, MOVE_RIGHT, 0)
    else:
        rnd = random.randint(0, 5)
        if rnd > 2:
            bot.SetMotion(botIndex, MOVE_BACKWARD, 0)
            bot.SetMotion(botIndex, MOVE_FORWARD, 0)
            bot.SetMotion(botIndex, MOVE_LEFT, 0)
            bot.SetMotion(botIndex, MOVE_RIGHT, 1)


def beast_chaos(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist):
    global leapBackDelay
    global leapBackDelayTimer
    global waitMove
    global waitMoveTimer

    if tgtDist <= 5.0 * bot.GetInventRange(botIndex, 0):
        if tgtDist < 0.6 * bot.GetInventRange(botIndex, 0):
            Battack_leap_Fangle_old(botIndex, 100)
        elif tgtDist < 1.0 * bot.GetInventRange(botIndex, 0):
            if botWState < maxHits + 1:
                waitMove = 1
                waitMoveTimer = 0
                Battack_leap_Fangle(botIndex, 60)
            elif waitMove == 1 and waitMoveTimer < 14:
                Battack_leap_Fangle(botIndex, 60)
            else:
                if leapBackDelay == 0:
                    waitMove = 0
                    leapBackDelayTimer = -10
                leapBackDelay = 1
        elif tgtDist < 1.5 * bot.GetInventRange(botIndex, 0):
            if botWState < maxHits + 1:
                waitMove = 1
                waitMoveTimer = 0
                Battack_leap_Fangle(botIndex, 40)
            elif waitMove == 1 and waitMoveTimer < 14:
                Battack_leap_Fangle(botIndex, 40)
            else:
                if leapBackDelay == 0:
                    waitMove = 0
                    leapBackDelayTimer = -10
                leapBackDelay = 1
        else:
            if botWState < maxHits + 1:
                Bleap_F(botIndex)
    else:
        Bmove_F(botIndex)


def beast_cautious_chaos(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist):
    global leapBackDelay
    global leapBackDelayTimer
    global waitMove
    global waitMoveTimer

    if tgtDist < 1.0 * bot.GetInventRange(botIndex, 0):
        if botWState < maxHits + 1:
            rnd = random.randint(0, 1)
            if rnd == 0:
                Battack_leap_Fangle_old(botIndex, 120)
            elif rnd == 1:
                Battack_leap_Fangle_old(botIndex, -120)
        else:
            Bleap_B(botIndex)
    elif tgtDist <= 2.0 * bot.GetInventRange(botIndex, 0):
        if botWState < maxHits + 1:
            waitMove = 1
            waitMoveTimer = 0
            Battack_leap_Fangle_old(botIndex, 100)
        elif waitMove == 1 and waitMoveTimer < 14:
            Battack_leap_Fangle_old(botIndex, 100)
        else:
            if leapBackDelay == 0:
                waitMove = 0
                leapBackDelayTimer = -10
            leapBackDelay = 1
    elif tgtDist <= 3.5 * bot.GetInventRange(botIndex, 0):
        if botWState < maxHits + 1:
            Bleap_F(botIndex)
    else:
        Bmove_F(botIndex)


def beast_close_chaos(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist):
    global leapBackDelay
    global leapBackDelayTimer
    global waitMove
    global waitMoveTimer

    if tgtDist < 1.0 * bot.GetInventRange(botIndex, 0):
        if botWState < maxHits + 1:
            rnd = random.randint(0, 1)
            if rnd == 0:
                Battack_leap_Fangle_old(botIndex, 120)
            elif rnd == 1:
                Battack_leap_Fangle_old(botIndex, -120)
        else:
            Bleap_B(botIndex)
    elif tgtDist <= 1.5 * bot.GetInventRange(botIndex, 0):
        if botWState == 0:
            Battack_Dleap_Fangle(botIndex, 100, 0)
        elif botWState < maxHits + 1:
            waitMove = 1
            waitMoveTimer = 0
            Battack_leap_Fangle_old(botIndex, 100)
        elif waitMove == 1 and waitMoveTimer < 14:
            Battack_leap_Fangle_old(botIndex, 100)
        else:
            if leapBackDelay == 0:
                waitMove = 0
                leapBackDelayTimer = -10
            leapBackDelay = 1
    elif tgtDist <= 3.5 * bot.GetInventRange(botIndex, 0):
        if botWState < maxHits + 1:
            Bleap_F(botIndex)
    else:
        Bmove_F(botIndex)


def beast_chaos_plus(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist):
    global leapBackDelay
    global leapBackDelayTimer
    global waitMove
    global waitMoveTimer

    if tgtDist < 1.0 * bot.GetInventRange(botIndex, 0):
        if botWState == 0:
            Battack_leap_Fangle_old(botIndex, 100)
        elif botWState < maxHits + 1:
            waitMove = 1
            waitMoveTimer = 0
            Battack_leap_Fangle_old(botIndex, 100)
        elif waitMove == 1 and waitMoveTimer < 14:
            Battack_leap_Fangle_old(botIndex, 100)
        else:
            if leapBackDelay == 0:
                waitMove = 0
                leapBackDelayTimer = -10
            leapBackDelay = 1
    elif tgtDist < 1.5 * bot.GetInventRange(botIndex, 0):
        # if botWState == 0:
        #    rnd = random.randint(0,1)
        #    if rnd == 0:
        #        Battack_leap_Fangle(botIndex, -30)
        #    elif rnd == 1:
        #        Battack_leap_Fangle(botIndex, 30)
        # elif botWState < maxHits+1:
        #    waitMove = 1
        #    waitMoveTimer = 0
        #    rnd = random.randint(0,1)
        #    if rnd == 0:
        #        Battack_leap_Fangle(botIndex, -30)
        #    elif rnd == 1:
        #        Battack_leap_Fangle(botIndex, 30)
        # elif waitMove == 1 and waitMoveTimer < 14:
        #    Battack_leap_Fangle(botIndex, 100)
        # else:
        #    if leapBackDelay == 0:
        #        waitMove = 0
        #        leapBackDelayTimer = -10
        #    leapBackDelay = 1
        if botWState < maxHits + 1:
            rnd = random.randint(0, 1)
            if rnd == 0:
                Bleap_Fangle(botIndex, -30)
            elif rnd == 1:
                Bleap_Fangle(botIndex, 30)
        elif targetWState > 0 and targetWState < 5:
            Bleap_B(botIndex)
    else:
        if botWState < maxHits:
            if botWState == 2:
                rnd = random.randint(0, 1)
                if rnd == 0:
                    Battack_leap_Fangle(botIndex, -15)
                elif rnd == 1:
                    Battack_leap_Fangle(botIndex, 15)
            else:
                if tgtDist > 2.0 * bot.GetInventRange(botIndex, 0):
                    Battack_F(botIndex)
                else:
                    Bmove_F(botIndex)
        else:
            if tgtDist < 2.0 * bot.GetInventRange(botIndex, 0):
                Bmove_B(botIndex)
            elif tgtDist > 3.5 * bot.GetInventRange(botIndex, 0):
                Bleap_F(botIndex)


def beast_timed_chaos(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist):
    global waitMove
    global waitMoveTimer

    if tgtDist < 1.0 * bot.GetInventRange(botIndex, 0):
        if waitMove == 1 and waitMoveTimer > 4:
            Battack_F(botIndex)
            waitMove = 0
            waitMoveTimer = 0
        else:
            if botWState < maxHits + 1:
                if waitMove == 0:
                    waitMove = 1
                    waitMoveTimer = 0
                Bleap_Fangle_old(botIndex, 100)
            else:
                if targetWState > 0 and targetWState < 5:
                    Bleap_B(botIndex)
                    waitMove = 0
                    waitMoveTimer = 0
    elif tgtDist < 2.0 * bot.GetInventRange(botIndex, 0):
        if botWState < maxHits + 1:
            if waitMove == 0:
                waitMove = 1
                waitMoveTimer = 0
            if waitMove == 0:
                Bleap_Fangle(botIndex, 40 - (tgtDist * 10))
            else:
                Bleap_F(botIndex)
    elif tgtDist < 2.5 * bot.GetInventRange(botIndex, 0):
        if botWState < maxHits + 1:
            if waitMove == 0:
                waitMove = 1
                waitMoveTimer = 0
            Bleap_F(botIndex)
    elif tgtDist < 3.0 * bot.GetInventRange(botIndex, 0):
        if waitMove == 0:
            waitMove = 1
            waitMoveTimer = 0
            Bleap_F(botIndex)
        else:
            Bmove_F(botIndex)


def beast_bobbot(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist):
    global leapBackDelay
    global leapBackDelayTimer
    global waitMove
    global waitMoveTimer
    global bobbotTimer

    if not bobbotTimer == 0:
        if bobbotTimer < 80:
            bobbotTimer += 1
        else:
            bobbotTimer = 0

    if tgtDist <= 5.0 * bot.GetInventRange(botIndex, 0):
        if bobbotTimer < 3 and targetWState == 1 and botWState == 0 and tgtDist <= 1.5 * bot.GetInventRange(botIndex,
                                                                                                            0):
            Bleap_B(botIndex)
            bobbotTimer = 1
            return
        if tgtDist < 1.0 * bot.GetInventRange(botIndex, 0):
            if botWState < maxHits + 1:
                waitMove = 1
                waitMoveTimer = 0
                Battack_leap_Fangle_old(botIndex, 100)
            elif waitMove == 1 and waitMoveTimer < 14:
                Battack_leap_Fangle_old(botIndex, 100)
            else:
                if leapBackDelay == 0:
                    waitMove = 0
                    leapBackDelayTimer = -10
                leapBackDelay = 1
        else:
            if botWState < maxHits + 1:
                Bleap_F(botIndex)

    else:
        Bmove_F(botIndex)


def beast_bobbot_slow(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist):
    global leapBackDelay
    global leapBackDelayTimer
    global waitMove
    global waitMoveTimer
    global blockTimer

    if tgtDist <= 5.0 * bot.GetInventRange(botIndex, 0):
        if tgtDist < 1.0 * bot.GetInventRange(botIndex, 0):
            if botWState < maxHits + 1:
                waitMove = 1
                waitMoveTimer = 0
                Battack_leap_Fangle(botIndex, 100)
            elif waitMove == 1 and waitMoveTimer < 14:
                Battack_leap_Fangle(botIndex, 100)
            else:
                if leapBackDelay == 0:
                    waitMove = 0
                    leapBackDelayTimer = -10
                leapBackDelay = 1
        else:
            if botWState == 0:
                Bleap_F(botIndex)
    else:
        Bmove_F(botIndex)


# Tries to dodge and counter; attacks skillfully
def beast_cautious_skilled(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist):
    global maxHits
    global waitLeapTimer
    global waitedBeforeLeap

    if waitedBeforeLeap == 1:
        if waitLeapTimer >= 4:
            waitedBeforeLeap = 0
            waitLeapTimer = -1
            rnd = random.randint(0, 3)
            if rnd == 0:
                Bleap_Fangle(botIndex, -50)
            elif rnd == 1:
                Bleap_Fangle(botIndex, 50)
            elif rnd == 2:
                Bleap_FL(botIndex)
            elif rnd == 3:
                Bleap_FR(botIndex)
        return

    if tgtDist <= 1.0 * bot.GetInventRange(botIndex, 0) and stamina > 2200:
        if botWState < maxHits:
            rnd = random.randint(0, 1)
            if rnd == 0:
                Battack_leap_L(botIndex)
            elif rnd == 1:
                Battack_leap_R(botIndex)
        else:
            Bmove_B(botIndex)
    elif tgtDist <= 2.0 * bot.GetInventRange(botIndex, 0):
        if targetWState == 17:
            if stamina > 2500:
                if botWState < maxHits or health > 0.4:
                    rnd = random.randint(0, 7)
                    if rnd == 0:
                        Battack_leap_Fangle(botIndex, -50)
                    elif rnd == 1:
                        Battack_leap_Fangle(botIndex, 50)
                    elif rnd == 2:
                        Battack_leap_Fangle(botIndex, -25)
                    elif rnd == 3:
                        Battack_leap_Fangle(botIndex, 25)
                    elif rnd == 4:
                        Battack_leap_Fangle(botIndex, -10)
                    elif rnd == 5:
                        Battack_leap_Fangle(botIndex, 10)
                    elif rnd == 6:
                        Battack_leap_FL(botIndex)
                    elif rnd == 7:
                        Battack_leap_FR(botIndex)
                else:
                    Bmove_B(botindex)
            else:
                Bmove_B(botindex)
        elif targetWState >= 1 and targetWState <= 4:
            if botWState > maxHits:
                if tgtDist <= 1.3 * bot.GetInventRange(botIndex, 0):
                    if stamina > 3000:
                        Bleap_B(botIndex)
                    else:
                        Bmove_B(botIndex)
            elif botWState < maxHits or health > 0.4:
                if stamina > 3000:
                    if tgtDist <= 1.5 * bot.GetInventRange(botIndex, 0):
                        rnd = random.randint(0, 7)
                        if rnd == 0:
                            Battack_leap_Fangle(botIndex, -50)
                        elif rnd == 1:
                            Battack_leap_Fangle(botIndex, 50)
                        elif rnd == 2:
                            Battack_leap_Fangle(botIndex, -25)
                        elif rnd == 3:
                            Battack_leap_Fangle(botIndex, 25)
                        elif rnd == 4:
                            Battack_leap_Fangle(botIndex, -10)
                        elif rnd == 5:
                            Battack_leap_Fangle(botIndex, 10)
                        elif rnd == 6:
                            Battack_leap_FL(botIndex)
                        elif rnd == 7:
                            Battack_leap_FR(botIndex)
                        else:
                            waitedBeforeLeap = 1
                else:
                    Battack_F(botIndex)
            else:
                if stamina > 3000:
                    Bleap_B(botIndex)
                else:
                    Bmove_B(botIndex)
        else:
            if botWState < maxHits or health > 0.4:
                if stamina > 3000:
                    if tgtDist <= 1.5 * bot.GetInventRange(botIndex, 0):
                        rnd = random.randint(0, 5)
                        if rnd == 0:
                            Battack_leap_Fangle(botIndex, -20)
                        elif rnd == 1:
                            Battack_leap_Fangle(botIndex, 20)
                        elif rnd == 2:
                            Battack_leap_Fangle(botIndex, -10)
                        elif rnd == 3:
                            Battack_leap_Fangle(botIndex, 10)
                        elif rnd == 4:
                            Battack_leap_FL(botIndex)
                        elif rnd == 5:
                            Battack_leap_FR(botIndex)
                    else:
                        rnd = random.randint(0, 3)
                        if rnd == 0:
                            Battack_leap_Fangle(botIndex, -10)
                        elif rnd == 1:
                            Battack_leap_Fangle(botIndex, 10)
                        elif rnd == 2:
                            Bleap_FL(botIndex)
                        elif rnd == 3:
                            Bleap_FR(botIndex)
                else:
                    Battack_F(botIndex)
            else:
                Bmove_B(botIndex)


# Attacks skillfully with little regard to own safety
def beast_reckless_skilled(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist):
    if tgtDist <= 1.0 * bot.GetInventRange(botIndex, 0):
        rnd = random.randint(0, 2)
        if rnd == 0:
            if stamina > 2200:
                Battack_leap_L(botIndex)
            else:
                Bmove_L(botIndex)
        elif rnd == 1:
            if stamina > 2200:
                Battack_leap_B(botIndex)
            else:
                Bmove_B(botIndex)
        elif rnd == 2:
            if stamina > 2200:
                Battack_leap_R(botIndex)
            else:
                Bmove_R(botIndex)
    elif tgtDist <= 2.0 * bot.GetInventRange(botIndex, 0):
        if targetWState == 17:
            if stamina > 2200:
                rnd = random.randint(0, 5)
                if rnd == 0:
                    Battack_leap_Fangle(botIndex, -50)
                elif rnd == 1:
                    Battack_leap_Fangle(botIndex, 50)
                elif rnd == 2:
                    Battack_leap_Fangle(botIndex, -10)
                elif rnd == 3:
                    Battack_leap_Fangle(botIndex, 10)
                elif rnd == 4:
                    Battack_leap_FL(botIndex)
                elif rnd == 5:
                    Battack_leap_FR(botIndex)
            else:
                Bmove_B(botIndex)
        elif targetWState >= 1 and targetWState <= 4:
            if tgtDist >= bot.GetInventRange(botIndex, 0):
                if stamina > 2200:
                    Battack_leap_F(botIndex)
                else:
                    Battack_B(botIndex)
            else:
                if stamina > 2200:
                    rnd = random.randint(0, 1)
                    if rnd == 0:
                        Battack_leap_FL(botIndex)
                    elif rnd == 1:
                        Battack_leap_FR(botIndex)
                else:
                    Battack_F(botIndex)
        else:
            if stamina > 2200:
                rnd = random.randint(0, 1)
                if rnd == 0:
                    Battack_leap_Fangle(botIndex, -50)
                elif rnd == 1:
                    Battack_leap_Fangle(botIndex, 50)
            else:
                Battack_F(botIndex)


# Just walk towards enemy and attack
def beast_newbie(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist):
    Battack_F(botIndex)
    bot.SetButton(botIndex, BUTTON_SPRINT, 1)


# Just walk towards enemy and attack with a delay
def beast_slow_newbie(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist):
    global attackDelay
    global attackDelayTimer

    attackDelay = 1
    if attackDelayTimer >= 20:
        Battack_F(botIndex)
        attackDelayTimer = 0


# Just run towards enemy and attack with a random delay
def beast_random_newbie(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist):
    global attackDelay
    global attackDelayTimer

    if tgtDist <= 1.5 * bot.GetInventRange(botIndex, 0):
        attackDelay = 1
        if attackDelayTimer >= 20:
            Battack(botIndex)
            if stamina > 1000:
                bot.SetButton(botIndex, BUTTON_SPRINT, 1)
            rnd = random.randint(0, 20)
            attackDelayTimer = 0 - rnd
    elif tgtDist >= 3.5 * bot.GetInventRange(botIndex, 0):
        attackDelay = 0
        rnd = random.randint(0, 20)
        attackDelayTimer = 0 - rnd


# Frontal leaps (out of range) and attacks (in range)
def beast_reckless_newbie(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist):
    if tgtDist >= 1.0 * bot.GetInventRange(botIndex, 0):
        Bleap_F(botIndex)
    else:
        Battack_F(botIndex)


# Only attacks front and once (tries to find an opening); stays at distance else
def beast_cautious_newbie(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist):
    if botWState == 0:
        if targetWState == 17:
            rnd = random.randint(0, 9)
            if rnd == 0:
                Battack_leap_F(botIndex)
            else:
                Bmove_B(botIndex)
        elif targetWState >= 1 and targetWState <= 4:
            rnd = random.randint(0, 9)
            if rnd == 0:
                Battack_leap_F(botIndex)
            else:
                if tgtDist <= 1.1 * bot.GetInventRange(botIndex, 0):
                    if health < 0.4:
                        Bleap_B(botIndex)
                    else:
                        Bmove_B(botIndex)
                else:
                    Battack(botIndex)
        else:
            Battack_leap_F(botIndex)
    else:
        if tgtDist <= 1.1 * bot.GetInventRange(botIndex, 0):
            if health < 0.4:
                Bleap_B(botIndex)
            else:
                Bmove_B(botIndex)


# Only attacks with maxHits (tries to find an opening) and randoms angle (sometimes frontal, sometimes backstab); stays at distance else
def beast_cautious_noob(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist):
    if botWState < maxHits:
        if targetWState == 17:
            rnd = random.randint(0, 9)
            if rnd == 0:
                Battack_leap_F(botIndex)
            else:
                Bmove_B(botIndex)
        elif targetWState >= 1 and targetWState <= 4:
            rnd = random.randint(0, 10)
            if rnd > 6:
                Battack_leap_F(botIndex)
            elif rnd > 3:
                Battack_leap_Fangle(botIndex, -float(random.randint(10, 50)))
            elif rnd > 0:
                Battack_leap_Fangle(botIndex, float(random.randint(10, 50)))
            else:
                if tgtDist <= 1.1 * bot.GetInventRange(botIndex, 0):
                    if health < 0.4:
                        Bleap_B(botIndex)
                    else:
                        Bmove_B(botIndex)
                else:
                    Battack(botIndex)
        else:
            Battack_leap_F(botIndex)
    else:
        if tgtDist <= 1.1 * bot.GetInventRange(botIndex, 0):
            if health < 0.4:
                Bleap_B(botIndex)
            else:
                Bmove_B(botIndex)


# Leaps at different angles (out of range) and attacks (in range)
def beast_reckless_noob(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist):
    if tgtDist >= 1.0 * bot.GetInventRange(botIndex, 0):
        rnd = random.randint(0, 5)
        if rnd == 4:
            Battack_leap_F(botIndex)
        elif rnd == 3:
            Battack_leap_FL(botIndex)
        elif rnd == 2:
            Battack_leap_FR(botIndex)
        elif rnd == 1:
            Battack_leap_Fangle(botIndex, -float(random.randint(10, 50)))
        elif rnd == 0:
            Battack_leap_Fangle(botIndex, float(random.randint(10, 50)))
    else:
        Battack_F(botIndex)


def beast_skilled_plus(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist):
    if targetWState == 17:
        if botWState < maxHits:
            if stamina > 2200:
                if tgtDist <= 1.0 * bot.GetInventRange(botIndex, 0):
                    rnd = random.randint(0, 2)
                    if rnd == 0:
                        Battack_leap_FL(botIndex)
                    else:
                        Battack_leap_FR(botIndex)
                elif tgtDist <= 2.0 * bot.GetInventRange(botIndex, 0):
                    rnd = random.randint(0, 2)
                    if rnd == 0:
                        Battack_leap_Fangle(botIndex, -float(random.randint(30, 40)))
                    elif rnd == 1:
                        Battack_leap_Fangle(botIndex, float(random.randint(30, 40)))
                else:
                    Bmove_B(botIndex)
            else:
                Bmove_B(botIndex)
        else:
            Bmove_B(botIndex)
    elif targetWState >= 1 and targetWState <= 4:
        if stamina > 2200:
            if botWState < maxHits:
                if tgtDist <= 1.0 * bot.GetInventRange(botIndex, 0):
                    rnd = random.randint(0, 2)
                    if rnd == 0:
                        Battack_leap_FL(botIndex)
                    else:
                        Battack_leap_FR(botIndex)
                elif tgtDist <= 2.0 * bot.GetInventRange(botIndex, 0):
                    rnd = random.randint(0, 11)
                    if rnd > 6:
                        Battack_leap_F(botIndex)
                    elif rnd > 3:
                        Battack_leap_Fangle(botIndex, -float(random.randint(10, 20)))
                    elif rnd > 0:
                        Battack_leap_Fangle(botIndex, float(random.randint(10, 20)))
                    else:
                        if tgtDist <= 1.1 * bot.GetInventRange(botIndex, 0):
                            if health < 0.4:
                                Bleap_B(botIndex)
                            else:
                                Bmove_B(botIndex)
                        else:
                            Battack(botIndex)

            else:
                Bleap_B(botIndex)
        else:
            Bmove_B(botIndex)
    else:
        if botWState < maxHits:
            if stamina > 2200:
                if tgtDist <= 1.0 * bot.GetInventRange(botIndex, 0):
                    rnd = random.randint(0, 2)
                    if rnd == 0:
                        Battack_leap_FL(botIndex)
                    else:
                        Battack_leap_FR(botIndex)
                elif tgtDist <= 2.0 * bot.GetInventRange(botIndex, 0):
                    rnd = random.randint(0, 2)
                    if rnd == 0:
                        Battack_leap_Fangle(botIndex, -float(random.randint(30, 40)))
                    elif rnd == 1:
                        Battack_leap_Fangle(botIndex, float(random.randint(30, 40)))
                else:
                    Battack_F(botIndex)
            else:
                Battack_F(botIndex)
        else:
            Bmove_B(botIndex)


def beast_reckless_plus(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist):
    if tgtDist <= 1.0 * bot.GetInventRange(botIndex, 0):
        if stamina > 2200:
            rnd = random.randint(0, 2)
            if rnd == 0:
                Battack_leap_L(botIndex)
            else:
                Battack_leap_R(botIndex)
        else:
            Bmove_B(botIndex)
    elif tgtDist <= 1.5 * bot.GetInventRange(botIndex, 0):
        if stamina > 2200:
            rnd = random.randint(0, 2)
            if rnd == 0:
                Battack_leap_Fangle(botIndex, -50.0)
            else:
                Battack_leap_Fangle(botIndex, 50.0)
        else:
            Bmove_B(botIndex)


def beast_aim_test(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist):
    if tgtDist <= 1.0 * bot.GetInventRange(botIndex, 0):
        if stamina > 2200:
            Bleap_B(botIndex)
        else:
            Bmove_B(botIndex)
    elif tgtDist <= 2.0 * bot.GetInventRange(botIndex, 0):
        Battack_leap_Fangle(botIndex, (45.0 - tgtDist / 20))
    else:
        Bmove_F(botIndex)


def beast_aim(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist):
    global disableNav
    global disableNavTimer
    global waitMove
    global waitMoveTimer
    global maxHits

    dodge = 0

    boolean = 0

    targetAngle = bot.NavGetTargetAng(botIndex, ANGLE_YAW)
    targetAngle += 180
    botAngle = bot.GetAngle(botIndex, ANGLE_YAW)
    botAngle2 = botAngle
    if botAngle < 0:
        botAngle2 += 180
    elif botAngle > 0:
        botAngle2 -= 180
    botAngle += 180
    difAngle = math.fabs(math.fabs(targetAngle - botAngle) - 180.0)
    difAngle2 = (targetAngle - botAngle2) - 180.0

    if targetWState >= 0 and targetWState < 4 and (health > 0.3 and targetHealth < 0.3):
        if tgtDist <= 1.5 * bot.GetInventRange(botIndex, 0):
            if botWState <= maxHits:
                Battack_leap_F(botIndex)
                waitMove = 0
                waitMoveTimer = 0
    elif targetWState == 1:
        if tgtDist <= 1.3 * bot.GetInventRange(botIndex, 0) and botWState == 0:
            Bleap_B(botIndex)
        elif tgtDist <= 1.8 * bot.GetInventRange(botIndex, 0):
            if botWState < maxHits:
                if waitMove == 0:
                    waitMove = 1
                    waitMoveTimer = 0
                elif waitMoveTimer >= 35:
                    Battack_leap_F(botIndex)
                    if waitMoveTimer >= 40:
                        waitMove = 0
            else:
                dodge = 1
    elif targetWState == 2:
        if tgtDist <= 1.3 * bot.GetInventRange(botIndex, 0):
            if difAngle2 < 0:
                Bleap_R(botIndex)
            else:
                Bleap_L(botIndex)
        elif tgtDist <= 1.5 * bot.GetInventRange(botIndex, 0):
            if botWState < maxHits:
                if waitMove == 0:
                    waitMove = 1
                    waitMoveTimer = 0
                elif waitMoveTimer >= 35:
                    Battack_leap_F(botIndex)
                    if waitMoveTimer >= 40:
                        waitMove = 0
            else:
                dodge = 1
    elif targetWState == 3:
        if tgtDist <= 1.3 * bot.GetInventRange(botIndex, 0):
            if difAngle2 < 0:
                Bleap_R(botIndex)
            else:
                Bleap_L(botIndex)
        elif tgtDist <= 1.5 * bot.GetInventRange(botIndex, 0):
            if botWState < maxHits:
                if waitMove == 0:
                    waitMove = 1
                    waitMoveTimer = 0
                elif waitMoveTimer >= 35:
                    Battack_leap_F(botIndex)
                    if waitMoveTimer >= 40:
                        waitMove = 0
            else:
                dodge = 1
    elif targetWState == 17:
        Bmove_L(botIndex)
        if boolean == 1:
            if botWState < maxHits:
                if tgtDist < 0.8 * bot.GetInventRange(botIndex, 0):
                    Bleap_L(botIndex)
                elif tgtDist < 1.5 * bot.GetInventRange(botIndex, 0):
                    Battack_leap_Fangle(botIndex, 75)
                    # Battack_leap_FR(botIndex)
                elif tgtDist < 2.5 * bot.GetInventRange(botIndex, 0):
                    Bleap_F(botIndex)
                else:
                    Bmove_F(botIndex)
    elif targetWState == 0:
        if botWState < maxHits:
            if tgtDist < 1.2 * bot.GetInventRange(botIndex, 0):
                Bmove_B(botIndex)
            elif tgtDist < 1.5 * bot.GetInventRange(botIndex, 0):
                # Battack_leap_Fangle(botIndex, 60)
                Battack_leap_FR(botIndex)
            elif tgtDist < 2.5 * bot.GetInventRange(botIndex, 0):
                Bleap_F(botIndex)
            else:
                Bmove_F(botIndex)
        elif health > 0.3 and targetHealth < 0.3:
            if tgtDist < 1.2 * bot.GetInventRange(botIndex, 0):
                Battack_F(botIndex)
            elif tgtDist < 2.0 * bot.GetInventRange(botIndex, 0):
                Battack_leap_F(botIndex)
    if dodge == 1:
        if tgtDist <= 1.2 * bot.GetInventRange(botIndex, 0):
            if difAngle2 < 0:
                Bleap_BR(botIndex)
            else:
                Bleap_BL(botIndex)

    if targetWState == 17 and botWState > 0 and botWState < maxHits + 2 and difAngle < 110 and tgtDist <= 1.0 * bot.GetInventRange(
            botIndex, 0):
        angle = (math.atan2(-tgtDir[0], tgtDir[1]) * (180.0) / 3.1415) + 110.0
        bot.SetAngle(botIndex, ANGLE_YAW, angle)
        if disableNav == 0:
            disableNav = 1
            disableNavTimer = 10
            #    return
            # else:
            #    angle = math.atan2(-tgtDir[0],tgtDir[1])*(180.0)/3.1415
            #    bot.SetAngle(botIndex,ANGLE_YAW,angle)


# Unfinished
def beast_pro(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist):
    global disableNav
    global disableNavTimer
    global waitMove
    global waitMoveTimer
    global maxHits
    global boolean1
    global bobbotTimer

    bobbotTimer += 1
    if bobbotTimer >= 10:
        bobbotTimer = 0
        boolean1 = random.randint(0, 1)

    dodge = 0
    # Battack_leap_F(botIndex)

    targetAngle = bot.NavGetTargetAng(botIndex, ANGLE_YAW)
    targetAngle += 180
    botAngle = bot.GetAngle(botIndex, ANGLE_YAW)
    botAngle2 = botAngle
    if botAngle < 0:
        botAngle2 += 180
    elif botAngle > 0:
        botAngle2 -= 180
    botAngle += 180
    difAngle = math.fabs(math.fabs(targetAngle - botAngle) - 180.0)
    difAngle2 = (targetAngle - botAngle2) - 180.0

    if targetWState > 0 and targetWState < 5 and health < 1.0:
        if tgtDist <= 1.25 * bot.GetInventRange(botIndex, 0):
            if difAngle2 < 0:
                Battack_leap_R(botIndex)
            else:
                Battack_leap_L(botIndex)
        elif tgtDist <= 1.5 * bot.GetInventRange(botIndex, 0):
            if botWState < maxHits:
                Battack(botIndex)
        else:
            Bmove_F(botIndex)
    else:
        if tgtDist <= 1.3 * bot.GetInventRange(botIndex, 0):
            if botWState < maxHits or (botWState < maxHits + 1 and health > 0.4 and targetHealth < 0.3):
                Battack_leap_F(botIndex)
        elif tgtDist <= 2.5 * bot.GetInventRange(botIndex, 0):
            if botWState < maxHits or (botWState < maxHits + 1 and health > 0.4) or (
                        targetWState == 0 or targetWState == -1 or targetWState == 17):
                Battack_leap_F(botIndex)
            else:
                Bmove_F(botIndex)

    # return

    if targetWState == 17 and botWState > 0 and botWState < maxHits + 2 and difAngle < 110 and tgtDist <= 1.1 * bot.GetInventRange(
            botIndex, 0):
        if boolean1 == 0:
            angle = (math.atan2(-tgtDir[0], tgtDir[1]) * (180.0) / 3.1415) + 110.0
        else:
            angle = (math.atan2(-tgtDir[0], tgtDir[1]) * (180.0) / 3.1415) - 110.0
        bot.SetAngle(botIndex, ANGLE_YAW, angle)
        if disableNav == 0:
            disableNav = 1
            disableNavTimer = -30
    else:
        # if tgtDist <= 1.0 * bot.GetInventRange(botIndex,0):
        #    angle = math.atan2(-tgtDir[0],tgtDir[1])*(180.0)/3.1415
        # else:
        if boolean1 == 0:
            angle = (math.atan2(-tgtDir[0], tgtDir[1]) * (180.0) / 3.1415) - (
            (tgtDist / bot.GetInventRange(botIndex, 0) * 20))
        else:
            angle = (math.atan2(-tgtDir[0], tgtDir[1]) * (180.0) / 3.1415) + (
            (tgtDist / bot.GetInventRange(botIndex, 0) * 20))
        bot.SetAngle(botIndex, ANGLE_YAW, angle)

    return

    if tgtDist <= 0.5 * bot.GetInventRange(botIndex, 0):
        Bleap_B(botIndex)
    elif tgtDist <= 1.0 * bot.GetInventRange(botIndex, 0):
        if botWState < maxHits:
            Battack_leap_Fangle(botIndex, 60)
        else:
            Bmove_F(botIndex)
    elif tgtDist <= 1.5 * bot.GetInventRange(botIndex, 0):
        if botWState < maxHits:
            Battack_leap_Fangle(botIndex, 45)
        else:
            Bmove_F(botIndex)

    return

    if botWState <= maxHits:
        if tgtDist <= 2.5 * bot.GetInventRange(botIndex, 0):
            Battack(botIndex)
            if disableNav == 0:
                disableNav = 1
                disableNavTimer = 0
                return

            if tgtDist <= 0.5 * bot.GetInventRange(botIndex, 0):
                Bleap_B(botIndex)
            elif tgtDist <= 1.0 * bot.GetInventRange(botIndex, 0):
                Battack_leap_Fangle(botIndex, 80)
                Battack_leap_Fangle(botIndex, 80)
            elif tgtDist <= 1.5 * bot.GetInventRange(botIndex, 0):
                Battack_leap_Fangle(botIndex, 45)
                Battack_leap_Fangle(botIndex, 45)
            else:
                Bmove_F(botIndex)
    else:
        if tgtDist <= 1.0 * bot.GetInventRange(botIndex, 0):
            Bleap_B(botIndex)
        else:
            Bmove_B(botIndex)

    if targetWState == 17 and botWState > 0 and botWState < maxHits + 2 and difAngle < 110 and tgtDist <= 1.0 * bot.GetInventRange(
            botIndex, 0):
        angle = (math.atan2(-tgtDir[0], tgtDir[1]) * (180.0) / 3.1415) + 110.0
        bot.SetAngle(botIndex, ANGLE_YAW, angle)
        if disableNav == 0:
            disableNav = 1
            disableNavTimer = 0
            #    return
            # else:
            #    angle = math.atan2(-tgtDir[0],tgtDir[1])*(180.0)/3.1415
            #    bot.SetAngle(botIndex,ANGLE_YAW,angle)


def beast_random(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist):
    global lastType
    global bobbotTimer

    bobbotTimer += 1
    if bobbotTimer >= 20:
        lastType = random.randint(0, 21)
        bobbotTimer = 0

    type = lastType
    if type == 0:
        beast_cautious_skilled(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
    elif type == 1:
        beast_reckless_skilled(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
    elif type == 2:
        beast_newbie(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
    elif type == 3:
        beast_slow_newbie(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
    elif type == 4:
        beast_random_newbie(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
    elif type == 5:
        beast_reckless_newbie(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
    elif type == 6:
        beast_cautious_newbie(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
    elif type == 7:
        beast_cautious_noob(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
    elif type == 8:
        beast_reckless_noob(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
    elif type == 9:
        beast_skilled_plus(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
    elif type == 10:
        beast_reckless_plus(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
    elif type == 11:
        beast_aim_test(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
    elif type == 12:
        beast_new(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
    elif type == 13:
        beast_unfair(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
    elif type == 14:
        beast_chaos(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
    elif type == 15:
        beast_cautious_chaos(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
    elif type == 16:
        beast_close_chaos(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
    elif type == 17:
        beast_chaos_plus(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
    elif type == 18:
        beast_timed_chaos(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
    elif type == 19:
        beast_bobbot(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
    elif type == 20:
        beast_bobbot_slow(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
    elif type == 21:
        beast_aim(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)


def beast_switch(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist):
    global lastType

    type = lastType
    if type == 0:  # B0
        beast_cautious_skilled(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
    elif type == 1:  # B1
        beast_reckless_skilled(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
    elif type == 2:  # B7
        beast_cautious_noob(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
    elif type == 3:  # B8
        beast_reckless_noob(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
    elif type == 4:  # B9
        beast_skilled_plus(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
    elif type == 5:  # B10
        beast_reckless_plus(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
    elif type == 6:  # B12
        beast_new(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
    elif type == 7:  # B13
        beast_unfair(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
    elif type == 8:  # B14
        beast_chaos(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
    elif type == 9:  # B17
        beast_chaos_plus(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
    elif type == 10:  # B19
        beast_bobbot(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
    elif type == 11:  # B20
        beast_bobbot_slow(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
    elif type == 12:  # B21
        beast_aim(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)
    elif type == 13:  # B22
        beast_pro(botIndex, targetWState, botWState, health, targetHealth, stamina, tgtDist)


# -----------#----------------------#-----------#
# -----------#      BEAST MOVES     #-----------#
# -----------#----------------------#-----------#
def Battack(botIndex):
    bot.SetMotion(botIndex, MOVE_BACKWARD, 0)
    bot.SetMotion(botIndex, MOVE_FORWARD, 0)
    bot.SwitchButton(botIndex, BUTTON_ATTACK)
    bot.SetButton(botIndex, BUTTON_BLOCK, 0)


def Battack_F(botIndex):
    bot.SetMotion(botIndex, MOVE_BACKWARD, 0)
    bot.SetMotion(botIndex, MOVE_FORWARD, 1)
    bot.SwitchButton(botIndex, BUTTON_ATTACK)
    bot.SetButton(botIndex, BUTTON_BLOCK, 0)


def Battack_B(botIndex):
    bot.SetMotion(botIndex, MOVE_BACKWARD, 1)
    bot.SetMotion(botIndex, MOVE_FORWARD, 0)
    bot.SwitchButton(botIndex, BUTTON_ATTACK)
    bot.SetButton(botIndex, BUTTON_BLOCK, 0)


def Battack_leap_F(botIndex):
    bot.SetMotion(botIndex, MOVE_BACKWARD, 0)
    bot.SetMotion(botIndex, MOVE_FORWARD, 1)
    bot.SwitchButton(botIndex, BUTTON_ATTACK)
    bot.SwitchButton(botIndex, BUTTON_BLOCK)


def Battack_leap_B(botIndex):
    bot.SetMotion(botIndex, MOVE_BACKWARD, 1)
    bot.SetMotion(botIndex, MOVE_FORWARD, 0)
    bot.SwitchButton(botIndex, BUTTON_ATTACK)
    bot.SwitchButton(botIndex, BUTTON_BLOCK)


def Battack_leap_L(botIndex):
    bot.SetMotion(botIndex, MOVE_BACKWARD, 0)
    bot.SetMotion(botIndex, MOVE_FORWARD, 0)
    bot.SetMotion(botIndex, MOVE_LEFT, 1)
    bot.SetMotion(botIndex, MOVE_RIGHT, 0)
    bot.SwitchButton(botIndex, BUTTON_ATTACK)
    bot.SwitchButton(botIndex, BUTTON_BLOCK)


def Battack_leap_R(botIndex):
    bot.SetMotion(botIndex, MOVE_BACKWARD, 0)
    bot.SetMotion(botIndex, MOVE_FORWARD, 0)
    bot.SetMotion(botIndex, MOVE_LEFT, 0)
    bot.SetMotion(botIndex, MOVE_RIGHT, 1)
    bot.SwitchButton(botIndex, BUTTON_ATTACK)
    bot.SwitchButton(botIndex, BUTTON_BLOCK)


def Battack_leap_FL(botIndex):
    bot.SetMotion(botIndex, MOVE_BACKWARD, 0)
    bot.SetMotion(botIndex, MOVE_FORWARD, 1)
    bot.SetMotion(botIndex, MOVE_LEFT, 1)
    bot.SetMotion(botIndex, MOVE_RIGHT, 0)
    bot.SwitchButton(botIndex, BUTTON_BLOCK)
    bot.SwitchButton(botIndex, BUTTON_ATTACK)


def Battack_leap_FR(botIndex):
    bot.SetMotion(botIndex, MOVE_BACKWARD, 0)
    bot.SetMotion(botIndex, MOVE_FORWARD, 1)
    bot.SetMotion(botIndex, MOVE_LEFT, 0)
    bot.SetMotion(botIndex, MOVE_RIGHT, 1)
    bot.SwitchButton(botIndex, BUTTON_BLOCK)
    bot.SwitchButton(botIndex, BUTTON_ATTACK)


def Battack_leap_L(botIndex):
    bot.SetMotion(botIndex, MOVE_BACKWARD, 0)
    bot.SetMotion(botIndex, MOVE_FORWARD, 0)
    bot.SetMotion(botIndex, MOVE_LEFT, 1)
    bot.SetMotion(botIndex, MOVE_RIGHT, 0)
    bot.SwitchButton(botIndex, BUTTON_BLOCK)
    bot.SwitchButton(botIndex, BUTTON_ATTACK)


def Battack_leap_R(botIndex):
    bot.SetMotion(botIndex, MOVE_BACKWARD, 0)
    bot.SetMotion(botIndex, MOVE_FORWARD, 0)
    bot.SetMotion(botIndex, MOVE_LEFT, 0)
    bot.SetMotion(botIndex, MOVE_RIGHT, 1)
    bot.SwitchButton(botIndex, BUTTON_BLOCK)
    bot.SwitchButton(botIndex, BUTTON_ATTACK)


def Battack_leap_Fangle(botIndex, angle):
    bot.SetMotion(botIndex, MOVE_BACKWARD, 0)
    bot.SetMotion(botIndex, MOVE_FORWARD, 1)
    angle = (math.atan2(-tgtDir[0], tgtDir[1]) * (180.0) / 3.1415) + angle
    bot.SetAngle(botIndex, ANGLE_YAW, angle)
    bot.SetMotion(botIndex, MOVE_LEFT, 0)
    bot.SetMotion(botIndex, MOVE_RIGHT, 0)
    bot.SwitchButton(botIndex, BUTTON_BLOCK)
    bot.SwitchButton(botIndex, BUTTON_ATTACK)


def Battack_leap_Fangle_old(botIndex, angle):
    bot.SetMotion(botIndex, MOVE_BACKWARD, 0)
    bot.SetMotion(botIndex, MOVE_FORWARD, 1)
    angle = (math.atan2(-tgtDir[0], tgtDir[1]) * (180.0 + angle) / 3.1415)
    bot.SetAngle(botIndex, ANGLE_YAW, angle)
    bot.SetMotion(botIndex, MOVE_LEFT, 0)
    bot.SetMotion(botIndex, MOVE_RIGHT, 0)
    bot.SwitchButton(botIndex, BUTTON_BLOCK)
    bot.SwitchButton(botIndex, BUTTON_ATTACK)


def Battack_Dleap_Fangle(botIndex, angle, delay):
    global leapDelay
    global leapDelayTimer
    angle = (math.atan2(-tgtDir[0], tgtDir[1]) * (180.0) / 3.1415) + angle
    bot.SetAngle(botIndex, ANGLE_YAW, angle)
    bot.SetMotion(botIndex, MOVE_LEFT, 0)
    bot.SetMotion(botIndex, MOVE_RIGHT, 0)
    bot.SwitchButton(botIndex, BUTTON_ATTACK)
    if leapDelay == 0:
        leapDelay = 1
        # leapDelayTimer = delay


def Bleap_F(botIndex):
    bot.SetMotion(botIndex, MOVE_FORWARD, 1)
    bot.SetMotion(botIndex, MOVE_BACKWARD, 0)
    bot.SetMotion(botIndex, MOVE_LEFT, 0)
    bot.SetMotion(botIndex, MOVE_RIGHT, 0)
    bot.SwitchButton(botIndex, BUTTON_BLOCK)
    bot.SetButton(botIndex, BUTTON_ATTACK, 0)


def Bleap_FL(botIndex):
    bot.SetMotion(botIndex, MOVE_FORWARD, 1)
    bot.SetMotion(botIndex, MOVE_BACKWARD, 0)
    bot.SetMotion(botIndex, MOVE_LEFT, 1)
    bot.SetMotion(botIndex, MOVE_RIGHT, 0)
    bot.SwitchButton(botIndex, BUTTON_BLOCK)
    bot.SetButton(botIndex, BUTTON_ATTACK, 0)


def Bleap_FR(botIndex):
    bot.SetMotion(botIndex, MOVE_FORWARD, 1)
    bot.SetMotion(botIndex, MOVE_BACKWARD, 0)
    bot.SetMotion(botIndex, MOVE_LEFT, 0)
    bot.SetMotion(botIndex, MOVE_RIGHT, 1)
    bot.SwitchButton(botIndex, BUTTON_BLOCK)
    bot.SetButton(botIndex, BUTTON_ATTACK, 0)


def Bleap_Fangle(botIndex, angle):
    bot.SetMotion(botIndex, MOVE_BACKWARD, 0)
    bot.SetMotion(botIndex, MOVE_FORWARD, 1)
    angle = (math.atan2(-tgtDir[0], tgtDir[1]) * (180.0) / 3.1415) + angle
    bot.SetAngle(botIndex, ANGLE_YAW, angle)
    bot.SetMotion(botIndex, MOVE_LEFT, 0)
    bot.SetMotion(botIndex, MOVE_RIGHT, 0)
    bot.SwitchButton(botIndex, BUTTON_BLOCK)


def Bleap_Fangle_old(botIndex, angle):
    bot.SetMotion(botIndex, MOVE_BACKWARD, 0)
    bot.SetMotion(botIndex, MOVE_FORWARD, 1)
    angle = (math.atan2(-tgtDir[0], tgtDir[1]) * (180.0 + angle) / 3.1415)
    bot.SetAngle(botIndex, ANGLE_YAW, angle)
    bot.SetMotion(botIndex, MOVE_LEFT, 0)
    bot.SetMotion(botIndex, MOVE_RIGHT, 0)
    bot.SwitchButton(botIndex, BUTTON_BLOCK)


def Bleap_L(botIndex):
    bot.SetMotion(botIndex, MOVE_FORWARD, 0)
    bot.SetMotion(botIndex, MOVE_BACKWARD, 0)
    bot.SetMotion(botIndex, MOVE_LEFT, 1)
    bot.SetMotion(botIndex, MOVE_RIGHT, 0)
    bot.SwitchButton(botIndex, BUTTON_BLOCK)
    bot.SetButton(botIndex, BUTTON_ATTACK, 0)


def Bleap_R(botIndex):
    bot.SetMotion(botIndex, MOVE_FORWARD, 0)
    bot.SetMotion(botIndex, MOVE_BACKWARD, 0)
    bot.SetMotion(botIndex, MOVE_LEFT, 0)
    bot.SetMotion(botIndex, MOVE_RIGHT, 1)
    bot.SwitchButton(botIndex, BUTTON_BLOCK)
    bot.SetButton(botIndex, BUTTON_ATTACK, 0)


def Bleap_B(botIndex):
    bot.SetMotion(botIndex, MOVE_FORWARD, 0)
    bot.SetMotion(botIndex, MOVE_BACKWARD, 1)
    bot.SetMotion(botIndex, MOVE_LEFT, 0)
    bot.SetMotion(botIndex, MOVE_RIGHT, 0)
    bot.SwitchButton(botIndex, BUTTON_BLOCK)
    bot.SetButton(botIndex, BUTTON_ATTACK, 0)


def Bleap_BL(botIndex):
    bot.SetMotion(botIndex, MOVE_FORWARD, 0)
    bot.SetMotion(botIndex, MOVE_BACKWARD, 1)
    bot.SetMotion(botIndex, MOVE_LEFT, 1)
    bot.SetMotion(botIndex, MOVE_RIGHT, 0)
    bot.SwitchButton(botIndex, BUTTON_BLOCK)
    bot.SetButton(botIndex, BUTTON_ATTACK, 0)


def Bleap_BR(botIndex):
    bot.SetMotion(botIndex, MOVE_FORWARD, 0)
    bot.SetMotion(botIndex, MOVE_BACKWARD, 1)
    bot.SetMotion(botIndex, MOVE_LEFT, 0)
    bot.SetMotion(botIndex, MOVE_RIGHT, 1)
    bot.SwitchButton(botIndex, BUTTON_BLOCK)
    bot.SetButton(botIndex, BUTTON_ATTACK, 0)


def Bmove_B(botIndex):
    bot.SetMotion(botIndex, MOVE_FORWARD, 0)
    bot.SetMotion(botIndex, MOVE_BACKWARD, 1)
    bot.SetMotion(botIndex, MOVE_LEFT, 0)
    bot.SetMotion(botIndex, MOVE_RIGHT, 0)
    bot.SetButton(botIndex, BUTTON_BLOCK, 0)
    bot.SetButton(botIndex, BUTTON_ATTACK, 0)


def Bmove_L(botIndex):
    bot.SetMotion(botIndex, MOVE_FORWARD, 0)
    bot.SetMotion(botIndex, MOVE_BACKWARD, 0)
    bot.SetMotion(botIndex, MOVE_LEFT, 1)
    bot.SetMotion(botIndex, MOVE_RIGHT, 0)
    bot.SetButton(botIndex, BUTTON_BLOCK, 0)
    bot.SetButton(botIndex, BUTTON_ATTACK, 0)


def Bmove_R(botIndex):
    bot.SetMotion(botIndex, MOVE_FORWARD, 0)
    bot.SetMotion(botIndex, MOVE_BACKWARD, 0)
    bot.SetMotion(botIndex, MOVE_LEFT, 0)
    bot.SetMotion(botIndex, MOVE_RIGHT, 1)
    bot.SetButton(botIndex, BUTTON_BLOCK, 0)
    bot.SetButton(botIndex, BUTTON_ATTACK, 0)


# -----------#----------------------#-----------#
def skill(botIndex, skillIndex):
    global skillLevel
    global lastType
    lastType = skillLevel
    skillLevel = skillIndex
    if core.CvarGetValue('sv_botPersonaName') == 1:
        newSkillName(botIndex, skillIndex)


def newSkillName(botIndex, skillIndex):
    raceDesc = sv_defs.teamList_RaceDesc[sv_defs.clientList_Team[botIndex]]
    if raceDesc == 'The Legion of Man':
        race = 1
    elif raceDesc == 'The Beast Horde':
        race = 2
    else:  # Everything else or at first add
        race = 0

    type = skillLevel
    name = 'Persona ' + str(int(type))
    if race == 1:
        if type > 17:
            name = 'Daebot'
        elif type < 0:
            name = 'Random Bot'
        else:
            name = 'Persona ' + str(int(type))
    elif race == 2:
        if type > 23:
            name = 'Daebot'
        elif type < 0:
            name = 'Random Bot'
        else:
            name = 'Persona ' + str(int(type))
    else:
        name = 'Persona ' + str(int(type))

    bot.SetName(botIndex, name)


def randomTaunt(botIndex):
    # global happiness
    global skillLevel
    global tgtIndex

    if skillLevel == 19 or skillLevel == 20:  # Bobbe's Taunt
        bot.Chatz(botIndex, 'lol')
    else:
        raceDesc = sv_defs.teamList_RaceDesc[sv_defs.clientList_Team[botIndex]]
        if raceDesc == 'The Legion of Man':
            race = 1
        elif raceDesc == 'The Beast Horde':
            race = 2
        else:
            race = 0

        targetRaceDesc = sv_defs.teamList_RaceDesc[sv_defs.clientList_Team[tgtIndex]]
        if targetRaceDesc == 'The Legion of Man':
            targetRace = 1
        elif targetRaceDesc == 'The Beast Horde':
            targetRace = 2
        else:
            targetRace = 0

        rnd = random.randint(0, 17)
        # Clemens' Taunts
        if rnd == 0:
            bot.Chatz(botIndex, 'Show me your moves!')
        elif rnd == 1:
            bot.Chatz(botIndex, 'Come at me, bro!')
        elif rnd == 2:
            bot.Chatz(botIndex, 'Let\'s dance!')
        elif rnd == 3:
            bot.Chatz(botIndex, 'Do you have what it takes?')
        elif rnd == 4:
            bot.Chatz(botIndex, 'Can\'t faze me, bro.')
        elif rnd == 5:
            bot.Chatz(botIndex, 'Be ready for me!')
        elif rnd == 6:
            bot.Chatz(botIndex, 'It pains me having to duel someone like you.')
        elif rnd == 7:
            bot.Chatz(botIndex, 'I am not a Bot. I swear on my motherboard.')
        elif rnd == 8:
            bot.Chatz(botIndex, 'Once I beat you, I will take over your identity.')
        elif rnd == 9:
            bot.Chatz(botIndex, 'Whine less. Duel more.')
        elif rnd == 10:
            bot.Chatz(botIndex, 'Bring it, punk!')
        elif rnd == 11:
            bot.Chatz(botIndex, 'Whine less. Duel more.')
        elif rnd == 12:
            bot.Chatz(botIndex, 'Death awaits you.')
        # Chaotic's (aka Chao) Taunts
        elif rnd == 13:
            bot.Chatz(botIndex, 'Look behind you...there is a Kongor with two heads!!')
        elif rnd == 14:
            if targetRace == 1:
                name = 'Jaraziah'
            elif targetRace == 2:
                name = 'Ophelia'
            else:
                name = 'anyone'
            bot.Chatz(botIndex, 'If you surrender, I won\'t tell ' + name + '.')
        elif rnd == 15:
            if targetRace == 1:
                bot.Chatz(botIndex, 'That axe looks too heavy for you.')
            elif targetRace == 2:
                bot.Chatz(botIndex, 'Your claws look very small for a beast your age.')
            else:
                bot.Chatz(botIndex, 'You look weak.')
        # SAS' Taunt
        elif rnd == 16:
            bot.Chatz(botIndex, 'Should I call my grandpa to play with you?')
        else:
            bot.Chatz(botIndex, 'I can\'t be bothered to come up with a witty line to taunt you with.')


def deathTaunt(botIndex):
    global happiness
    global skillLevel

    if skillLevel == 19 or skillLevel == 20:
        bot.Chatz(botIndex, 'lol')
    else:
        if happiness > 0:
            if happiness < 5:
                bot.Chatz(botIndex, 'I\'ll get you next time! ;)')
            elif happiness < 10:
                bot.Chatz(botIndex, 'Not bad.')
            elif happiness < 15:
                bot.Chatz(botIndex, 'Nice one. :P')
            elif happiness < 20:
                bot.Chatz(botIndex, 'Aahh, you got me. :)')
            else:
                bot.Chatz(botIndex, 'Finally killed me, eh? :)')
        elif happiness < 0:
            if happiness > -5:
                bot.Chatz(botIndex, 'I\'ll give you that one. ;)')
            elif happiness > -10:
                bot.Chatz(botIndex, 'Dammit!')
            elif happiness > -15:
                bot.Chatz(botIndex, 'Cheap annoying style! >:(')
            elif happiness > -20:
                bot.Chatz(botIndex, 'That move is so OP!')
            else:
                bot.Chatz(botIndex, 'Stop killing me. :\'(')
        else:
            bot.Chatz(botIndex, 'Evenly matched.')


def killTaunt(botIndex):
    global happiness
    global skillLevel

    if skillLevel == 19 or skillLevel == 20:
        bot.Chatz(botIndex, 'lol')
    else:
        if happiness > 0:
            if happiness < 5:
                bot.Chatz(botIndex, 'Close one. :P')
            elif happiness < 10:
                bot.Chatz(botIndex, 'Gotcha!')
            elif happiness < 15:
                bot.Chatz(botIndex, 'Winning~')
            elif happiness < 20:
                bot.Chatz(botIndex, 'Another point for the pro!')
            else:
                bot.Chatz(botIndex, 'Who is owning? I am! :D')
        elif happiness < 0:
            if happiness > -5:
                bot.Chatz(botIndex, 'You\'re tough to kill. :P')
            elif happiness > -10:
                bot.Chatz(botIndex, 'Take that!')
            elif happiness > -15:
                bot.Chatz(botIndex, 'And stay dead!')
            elif happiness > -20:
                bot.Chatz(botIndex, 'Killing you is really satisfying...')
            else:
                bot.Chatz(botIndex, 'DIE DIE DIE')
        else:
            bot.Chatz(botIndex, 'Evenly matched.')
