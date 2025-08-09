# ---------------------------------------------------------------------------
#           Name: sv_refs.py
#         Author: CrashDay and Groentjuh
#    Description: Custom Ref Commands ( client syntax: /ref python command ).
# ---------------------------------------------------------------------------

# Savage API
import core
import server

# Savage Modules
import sv_utils
import sh_custom_utils
import sh_logger as log
import json


validStates = ['adrenaline', 'barbequed', 'beast_camouflage', 'beast_immolate', 'beast_protect', 'beast_shield',
               'beast_staminaregen', 'beast_tracking', 'electrify', 'fire_shield', 'human_potion', 'imobilize',
               'infirmary_heal', 'magshield', 'magtowershield', 'object_fire', 'officer', 'officerarea', 'poisoned',
               'pulsed', 'rabid', 'snare', 'spire_healstructures']

validItems = ['ammo_box', 'arrow_tower_weapon', 'ballista_weapon', 'barrel_explode', 'beast_arcana', 'beast_behemoth',
              'beast_behemoth_melee', 'beast_camouflage', 'beast_charmshrine', 'beast_entropy_shrine', 'beast_entropy2',
              'beast_entropy_spire', 'beast_entropy1', 'beast_entropy1b', 'beast_entropy3', 'beast_fire_shield',
              'beast_fire_shrine', 'beast_fire_spire', 'beast_fire_spire_weapon', 'beast_fire_trap', 'beast_fire1',
              'beast_fire2', 'beast_fire3', 'beast_gateway', 'beast_heal', 'beast_immolate', 'beast_lair',
              'beast_lair2', 'beast_lair3', 'beast_mana_stone', 'beast_medic', 'beast_medic_melee', 'beast_nexus',
              'beast_poison', 'beast_predator', 'beast_predator_melee', 'beast_protect', 'beast_rabid',
              'beast_recharge', 'beast_revive', 'beast_sanctuary', 'beast_scavenger', 'beast_scavenger_melee',
              'beast_shield', 'beast_snare', 'beast_spire', 'beast_stalker', 'beast_stalker_melee',
              'beast_stamina_boost', 'beast_strata_shrine', 'beast_strata_spire', 'beast_strata1', 'beast_strata2',
              'beast_strata3', 'beast_sublair', 'beast_summoner', 'beast_summoner_weapon', 'beast_tracking_sense',
              'beast_vampire', 'beast_worker', 'catapult_weapon', 'chem_tower_weapon', 'dyn_barrel', 'dyn_column',
              'dyn_crate', 'dyn_crate_box_plain', 'dyn_crate_open_peaches', 'dyn_crate_open_plain',
              'dyn_crate_rect_plain', 'dyn_ladder', 'dyn_plank_long', 'dyn_plank_short', 'dyn_wood_panel',
              'elec_tower_weapon', 'foundry', 'gold_mine', 'goodiebag', 'human_adrenaline', 'human_ammo_pack',
              'human_arrow_tower', 'human_arsenal', 'human_ballista', 'human_bow', 'human_catapult',
              'human_chemical_factory', 'human_chemical_tower', 'human_coilrifle', 'human_crossbow', 'human_demo_pack',
              'human_discharger', 'human_electric_factory', 'human_electric_tower', 'human_electrify', 'human_fluxgun',
              'human_garrison', 'human_heal', 'human_imobilizer', 'human_incinerator', 'human_landmine',
              'human_launcher', 'human_legionnaire', 'human_legionnaire_melee', 'human_magnetic_factory',
              'human_magnetic_shield', 'human_magnetic_tower', 'human_medic', 'human_medic_melee', 'human_medkit',
              'human_monastery', 'human_mortar', 'human_mortar', 'human_motion_sensor', 'human_nomad',
              'human_nomad_melee', 'human_potion', 'human_pulsegun', 'human_relocater', 'human_relocater_trigger',
              'human_repeater', 'human_research_center', 'human_revive', 'human_savage', 'human_savage_melee',
              'human_scattergun', 'human_siege', 'human_sniperbow', 'human_stronghold', 'human_stronghold2',
              'human_stronghold3', 'human_worker', 'infirmary', 'lumber_pile_2500', 'lumber_pile_2500_stand',
              'lumber_pile_7500', 'lumber_pile_15000_stand', 'mana_stone', 'npc_bearloth', 'npc_berserker',
              'npc_boulder', 'npc_buffalo_plains', 'npc_buffalo_snow', 'npc_buffalo_waypoint', 'npc_chiprel', 'npc_gas',
              'npc_gerkat', 'npc_hornman', 'npc_hunchedbeast', 'npc_kongor', 'npc_lucy', 'npc_macaque', 'npc_mercenary',
              'npc_monkit', 'npc_mudent', 'npc_oschore', 'npc_panda', 'npc_ronin', 'npc_shrull', 'npc_skeleton_guard',
              'npc_skeleton_worker', 'npc_terror', 'npc_zizard', 'pickup_test', 'pot_explode', 'pot_tumble',
              'redstone_mine', 'redstone_mine_small', 'ruins_frontgate', 'sawmill', 'sawmill_small', 'spawnflag',
              'spire_weapon', 'stables', 'wall_prop', 'wiskeygulch_bridge', 'hero_ophelia', 'hero_jeraziah',
              'hero_ophelia_unshield']

# Accessible UID for admin stuff
PYTHON_ADMIN_IDS = list([int(i) for i in json.loads(python_config.get('Python_Referees', 'PYTHON_ADMIN_IDS'))])


# -------------------------------
# Called directly by Silverback
# -------------------------------
def execute(index, cmd):

    try:
        # Deny any other refs execution of the python ref commands
        uid = server.GetClientInfo(index, INFO_UID)
        if uid not in PYTHON_ADMIN_IDS:
            server.Notify(index, '^yYou ^yshall ^ynot ^ypass! ^y(Forbidden)')
            return

        # Log ref command usage
        log.warn("Ref Command: %s (sent by client %i)" % (cmd, index))

        # Check command type
        if cmd.find('help') != -1:
            help(index)

        elif cmd.find('statelist') != -1:
            if server.GetClientInfo(index, INFO_REFSTATUS) == 'god':
                statelist(index)
            else:
                senddenymessage(index)

        elif cmd.find('itemlist') != -1:
            if server.GetClientInfo(index, INFO_REFSTATUS) == 'god':
                itemlist(index)
            else:
                senddenymessage(index)

        elif cmd.find('.') != -1:
            object = formatObject(cmd.split('.')[0])
            method = cmd.split('.')[1].lower()
            if method.find('givestate') != -1:
                if server.GetClientInfo(index, INFO_REFSTATUS) == 'god':
                    method = method.replace('givestate', '')
                    givestate(str(object), str(getArgs(method)[0]).lower(), str(getArgs(method)[1]).lower())
                else:
                    senddenymessage(index)
            if method.find('revive') != -1:
                if server.GetClientInfo(index, INFO_REFSTATUS) == 'god':
                    method = method.replace('revive', '')
                    revive(object)
                else:
                    senddenymessage(index)
            if method.find('givemoney') != -1:
                if server.GetClientInfo(index, INFO_REFSTATUS) == 'god':
                    method = method.replace('givemoney', '')
                    givemoney(str(object), str(getArgs(method)[0]))
                else:
                    senddenymessage(index)
            if method.find('giveresource') != -1:
                if server.GetClientInfo(index, INFO_REFSTATUS) == 'god':
                    method = method.replace('giveresource', '')
                    giveresource(str(object), str(getArgs(method)[0]), str(getArgs(method)[1]))
                else:
                    senddenymessage(index)
            if method.find('removestate') != -1:
                if server.GetClientInfo(index, INFO_REFSTATUS) == 'god':
                    method = method.replace('removestate', '')
                    removestate(str(object), str(getArgs(method)[0]))
                else:
                    senddenymessage(index)
            if method.find('removeallstates') != -1:
                if server.GetClientInfo(index, INFO_REFSTATUS) == 'god':
                    method = method.replace('removeallstates', '')
                    removeallstates(str(object))
                else:
                    senddenymessage(index)
            if method.find('kick') != -1:
                if (server.GetClientInfo(index, INFO_REFSTATUS) == 'normal' and int(
                        core.CvarGetValue('sv_ref_allowkick')) > 0) or (
                            server.GetClientInfo(index, INFO_REFSTATUS) == 'god'):
                    method = method.replace('kick', '')
                    kick(index, str(object))
                else:
                    senddenymessage(index)
            if method.find('mute') != -1:
                if (server.GetClientInfo(index, INFO_REFSTATUS) == 'normal' and int(
                        core.CvarGetValue('sv_ref_allowmute')) > 0) or (
                            server.GetClientInfo(index, INFO_REFSTATUS) == 'god'):
                    method = method.replace('mute', '')
                    mute(index, str(object))
                else:
                    senddenymessage(index)
            if method.find('unmute') != -1:
                if (server.GetClientInfo(index, INFO_REFSTATUS) == 'normal' and int(
                        core.CvarGetValue('sv_ref_allowmute')) > 0) or (
                            server.GetClientInfo(index, INFO_REFSTATUS) == 'god'):
                    method = method.replace('unmute', '')
                    unmute(str(object))
                else:
                    senddenymessage(index)
            if method.find('switchteam') != -1:
                if (server.GetClientInfo(index, INFO_REFSTATUS) == 'guest') or (
                                server.GetClientInfo(index, INFO_REFSTATUS) == 'normal' and int(
                            core.CvarGetValue('sv_ref_allowswitchteam')) > 0) or (
                            server.GetClientInfo(index, INFO_REFSTATUS) == 'god'):
                    method = method.replace('switchteam', '')
                    switchteam(index, str(object), str(getArgs(method)[0]))
                else:
                    senddenymessage(index)
            if method.find('slay') != -1:
                if (server.GetClientInfo(index, INFO_REFSTATUS) == 'normal' and int(
                        core.CvarGetValue('sv_ref_allowslay')) > 0) or (
                            server.GetClientInfo(index, INFO_REFSTATUS) == 'god'):
                    method = method.replace('slay', '')
                    slay(index, str(object))
                else:
                    senddenymessage(index)
            if method.find('changeunit') != -1:
                if server.GetClientInfo(index, INFO_REFSTATUS) == 'god':
                    method = method.replace('changeunit', '')
                    changeunit(str(object), str(getArgs(method)[0]))
                else:
                    senddenymessage(index)
            if method.find('giveitem') != -1:
                if server.GetClientInfo(index, INFO_REFSTATUS) == 'god':
                    method = method.replace('giveitem', '')
                    giveitem(str(object), str(getArgs(method)[0]), str(getArgs(method)[1]), str(getArgs(method)[2]))
                else:
                    senddenymessage(index)
            if method.find('heal') != -1:
                if server.GetClientInfo(index, INFO_REFSTATUS) == 'god':
                    method = method.replace('heal', '')
                    heal(str(object))
                else:
                    senddenymessage(index)
            if method.find('spawn') != -1:
                if server.GetClientInfo(index, INFO_REFSTATUS) == 'god':
                    method = method.replace('spawn', '')
                    spawn(str(object), str(getArgs(method)[0]), str(getArgs(method)[1]))
                else:
                    senddenymessage(index)
            if method.find('teleport') != -1:
                if server.GetClientInfo(index, INFO_REFSTATUS) == 'god':
                    method = method.replace('teleport', '')
                    teleport(str(object), str(getArgs(method)[0]))
                else:
                    senddenymessage(index)
    except:
        sh_custom_utils.get_and_log_exception_info()


def formatObject(object):
    standardObjects = ['all', 'team1', 'team2', 'team3', 'team4']
    object.replace('"', '')
    if object.lower() in standardObjects:
        object = object.lower()
    return object


def getArgs(method):
    badchars = ['"', '(', ')', ' ']
    result = method
    for s in method:
        if s in badchars:
            result = result.replace(s, '')
    return result.split(',')


def givestate(object, state, duration):
    if state in validStates:
        if object == 'all':
            core.CommandExec('givestate -1 %s %s' % (state, duration))
        elif object.find('team') != -1:
            object = object.replace('team', '')
            for index in sv_utils.getIndicesFromTeam(str(object)):
                core.CommandExec('givestate %s %s %s' % (str(index), state, duration))
        else:
            core.CommandExec('givestate %s %s %s' % (str(sv_utils.getIndexFromName(str(object))), state, duration))


def removestate(object, state):
    givestate(object, state, '0')


def removeallstates(object):
    for state in validStates:
        removestate(object, state)


def revive(object):
    if object == 'all':
        for index in sv_utils.getActiveIndices():
            core.CommandExec('revive %s' % (str(index)))
    elif object.find('team') != -1:
        object = object.replace('team', '')
        for index in sv_utils.getIndicesFromTeam(object):
            core.CommandExec('revive %s' % (str(index)))
    else:
        core.CommandExec('revive %s' % (str(sv_utils.getIndexFromName(str(object)))))


def givemoney(object, amount):
    if object == 'all':
        core.CommandExec('givemoney %s' % (amount))
    elif object.find('team') != -1:
        object = object.replace('team', '')
        for index in sv_utils.getIndicesFromTeam(str(object)):
            core.CommandExec('givemoney %s %s' % (amount, str(index)))
    else:
        core.CommandExec('givemoney %s %s' % (amount, str(sv_utils.getIndexFromName(str(object)))))


def giveresource(object, type, amount):
    if object == 'all':
        core.CommandExec('giveresource %s %s' % (type, amount))
    elif object.find('team') != -1:
        object = object.replace('team', '')
        core.CommandExec('giveresource %s %s %s' % (type, amount, object))


def kick(index, object):
    if object == 'all':
        server.Notify(index, "Kicking all players is not allowed!")
    elif object.find('team') != -1:
        server.Notify(index, "Kicking a whole team is not allowed!")
    else:
        core.CommandExec('kick %s' % (str(sv_utils.getIndexFromName(str(object)))))


def mute(index, object):
    if object == 'all':
        server.Notify(index, "Muting all players is not allowed!")
    elif object.find('team') != -1:
        server.Notify(index, "Muting a whole team is not allowed!")
    else:
        core.CommandExec('mute %s' % (str(sv_utils.getIndexFromName(str(object)))))


def unmute(object):
    if object == 'all':
        for index in sv_utils.getActiveIndices():
            core.CommandExec('unmute %s' % (str(index)))
    elif object.find('team') != -1:
        object = object.replace('team', '')
        for index in sv_utils.getIndicesFromTeam(str(object)):
            core.CommandExec('unmute %s' % (str(index)))
    else:
        core.CommandExec('unmute %s' % (str(sv_utils.getIndexFromName(str(object)))))


def switchteam(index, object, team):
    if team.find('team') != -1:
        team = team.replace('team', '')
    if object == 'all':
        server.Notify(index, "Switching all players is not allowed!")
    elif object.find('team') != -1:
        server.Notify(index, "Switching a whole team is not allowed!")
    else:
        core.CommandExec('switchteam %s %s' % (str(team), str(sv_utils.getIndexFromName(str(object)))))


def slay(index, object):
    if object == 'all':
        server.Notify(index, "Slaying all players is not allowed!")
    elif object.find('team') != -1:
        server.Notify(index, "Slaying a whole team is not allowed!")
    else:
        core.CommandExec('slay %s' % (str(sv_utils.getIndexFromName(str(object)))))


def changeunit(object, unit):
    if unit in validItems:
        if object == 'all':
            for index in sv_utils.getActiveIndices():
                server.GameScript(int(index), '!changeunit target %s' % (str(unit)))
        elif object.find('team') != -1:
            object = object.replace('team', '')
            for index in sv_utils.getIndicesFromTeam(str(object)):
                server.GameScript(int(index), '!changeunit target %s' % (str(unit)))
        else:
            server.GameScript(int(sv_utils.getIndexFromName(str(object))), '!changeunit target %s' % (str(unit)))


def giveitem(object, item, slot, ammo):
    if item in validItems:
        if object == 'all':
            for index in sv_utils.getActiveIndices():
                server.GameScript(int(index), '!give target %s %s %s' % (str(item), str(ammo), str(int(slot) - 1)))
        elif object.find('team') != -1:
            object = object.replace('team', '')
            for index in sv_utils.getIndicesFromTeam(str(object)):
                server.GameScript(int(index), '!give target %s %s %s' % (str(item), str(ammo), str(int(slot) - 1)))
        else:
            server.GameScript(int(sv_utils.getIndexFromName(str(object))),
                              '!give target %s %s %s' % (str(item), str(ammo), str(int(slot) - 1)))


def heal(object):
    if object == 'all':
        for index in sv_utils.getActiveIndices():
            server.GameScript(int(index), '!heal target 10000')
            server.GameScript(int(index), '!givemana target 250')
            server.GameScript(int(index), '!givestamina target 5000')
    elif object.find('team') != -1:
        object = object.replace('team', '')
        for index in sv_utils.getIndicesFromTeam(str(object)):
            server.GameScript(int(index), '!heal target 10000')
            server.GameScript(int(index), '!givemana target 250')
            server.GameScript(int(index), '!givestamina target 5000')
    else:
        server.GameScript(int(sv_utils.getIndexFromName(str(object))), '!heal target 10000')
        server.GameScript(int(sv_utils.getIndexFromName(str(object))), '!givemana target 250')
        server.GameScript(int(sv_utils.getIndexFromName(str(object))), '!givestamina target 5000')


def spawn(object, item, team):
    if item in validItems:
        if object == 'all':
            for index in sv_utils.getActiveIndices():
                server.GameScript(int(index), '!spawnobject target %s %s neutral nearby' % (str(item), str(team)))
        elif object.find('team') != -1:
            object = object.replace('team', '')
            for index in sv_utils.getIndicesFromTeam(str(object)):
                server.GameScript(int(index), '!spawnobject target %s %s neutral nearby' % (str(item), str(team)))
        else:
            server.GameScript(int(sv_utils.getIndexFromName(str(object))),
                              '!spawnobject target %s %s neutral nearby' % (str(item), str(team)))


def teleport(object, target):
    if object == 'all':
        for index in sv_utils.getActiveIndices():
            if target == 'home':
                server.GameScript(int(index), '!teleport target home')
            elif target.find('|') != -1:
                server.GameScript(int(index), '!teleport target coords %s %s' % (
                    str(target.split('|')[0]), str(target.split('|')[1])))
    elif object.find('team') != -1:
        object = object.replace('team', '')
        for index in sv_utils.getIndicesFromTeam(str(object)):
            if target == 'home':
                server.GameScript(int(index), '!teleport target home')
            elif target.find('|') != -1:
                server.GameScript(int(index), '!teleport target coords %s %s' % (
                    str(target.split('|')[0]), str(target.split('|')[1])))
    elif object.find('worker') != -1:
        server.GameScript(int(136),
                          '!teleport target coords %s %s' % (str(target.split('|')[0]), str(target.split('|')[1])))
    else:
        if target == 'home':
            server.GameScript(int(sv_utils.getIndexFromName(str(object))), '!teleport target home')
        elif target.find('|') != -1:
            server.GameScript(int(sv_utils.getIndexFromName(str(object))),
                              '!teleport target coords %s %s' % (str(target.split('|')[0]), str(target.split('|')[1])))


def statelist(index):
    server.Notify(index, '^yStatelist:')
    server.Notify(index, '^y========================')
    for state in validStates:
        server.Notify(index, '^y' + str(state))


def itemlist(index):
    server.Notify(index, '^yItemlist:')
    server.Notify(index, '^y========================')
    for item in validItems:
        server.Notify(index, '^y' + str(item))


def help(index):
    server.Notify(index, '^yClient ^yPython ^yCommands^y:')
    server.Notify(index, '^y========================')
    server.Notify(index, '^y/ref ^ypython ^yhelp')
    if (server.GetClientInfo(index, INFO_REFSTATUS) == 'guest' and server.GetGameInfo(GAME_STATE) < 3) or (
                server.GetClientInfo(index, INFO_REFSTATUS) == 'normal') or (
                server.GetClientInfo(index, INFO_REFSTATUS) == 'god'):
        server.Notify(index, '^yReferee ^yPython ^yCommands:')
        server.Notify(index, '^y========================')
        if server.GetClientInfo(index, INFO_REFSTATUS) == 'god':
            server.Notify(index, '^y/ref ^ypython ^ystatelist')
            server.Notify(index, '^y/ref ^ypython ^yitemlist')
            server.Notify(index, '^y========================')
        server.Notify(index, '^ySyntax: ^y/ref ^ypython ^yobject.^ycommand()')
        server.Notify(index, '^yObjects: ^ynickname, ^yteam1, ^yteam2, ^yteam3, ^yteam4, ^yall')
        server.Notify(index, '^yCommands:')

        if (server.GetClientInfo(index, INFO_REFSTATUS) == 'normal' and int(
                core.CvarGetValue('sv_ref_allowkick')) > 0) or (server.GetClientInfo(index, INFO_REFSTATUS) == 'god'):
            server.Notify(index, '^y/ref python object.kick()')

        if (server.GetClientInfo(index, INFO_REFSTATUS) == 'normal' and int(
                core.CvarGetValue('sv_ref_allowmute')) > 0) or (server.GetClientInfo(index, INFO_REFSTATUS) == 'god'):
            server.Notify(index, '^y/ref python object.mute()')

        if (server.GetClientInfo(index, INFO_REFSTATUS) == 'normal' and int(
                core.CvarGetValue('sv_ref_allowslay')) > 0) or (server.GetClientInfo(index, INFO_REFSTATUS) == 'god'):
            server.Notify(index, '^y/ref python object.slay()')

        if (server.GetClientInfo(index, INFO_REFSTATUS) == 'guest') or (
                        server.GetClientInfo(index, INFO_REFSTATUS) == 'normal' and int(
                    core.CvarGetValue('sv_ref_allowswitchteam')) > 0) or (
                    server.GetClientInfo(index, INFO_REFSTATUS) == 'god'):
            server.Notify(index, '^y/ref python object.switchteam(team)')

        if (server.GetClientInfo(index, INFO_REFSTATUS) == 'normal' and int(
                core.CvarGetValue('sv_ref_allowmute')) > 0) or (server.GetClientInfo(index, INFO_REFSTATUS) == 'god'):
            server.Notify(index, '^y/ref python object.unmute()')

        if server.GetClientInfo(index, INFO_REFSTATUS) == 'god':
            server.Notify(index, '^y/ref ^ypython ^yobject.changeunit(unit)')
            server.Notify(index, '^y/ref ^ypython ^yobject.giveitem(unit/weapon/item,slot,ammo)')
            server.Notify(index, '^y/ref ^ypython ^yobject.givemoney(amount)')
            server.Notify(index, '^y/ref ^ypython ^yobject.giveresource(stone/gold,amount)')
            server.Notify(index, '^y/ref ^ypython ^yobject.givestate(state,duration)')
            server.Notify(index, '^y/ref ^ypython ^yobject.heal()')
            server.Notify(index, '^y/ref ^ypython ^yobject.removestate(state)')
            server.Notify(index, '^y/ref ^ypython ^yobject.removeallstates()')
            server.Notify(index, '^y/ref ^ypython ^yobject.revive()')
            server.Notify(index, '^y/ref ^ypython ^yobject.spawn(unit)')
            server.Notify(index, '^y/ref ^ypython ^yobject.teleport(home/x|y)')
    if server.GetClientInfo(index, INFO_REFSTATUS) == 'guest' and server.GetGameInfo(GAME_STATE) >= 3:
        server.Notify(index, '^yGuest ^yreferee ^ycommands ^yare ^ynot ^yallowed ^yduring ^ythe ^ymatch! ^yWait '
                             '^yuntil ^ythe ^ynext ^ysetup ^ytime.')


def senddenymessage(index):
    if server.GetClientInfo(index, INFO_REFSTATUS) == 'guest' and server.GetGameInfo(GAME_STATE) >= 3:
        server.Notify(index, '^yGuest ^yreferee ^ycommands ^yare ^ynot ^yallowed ^yduring ^ythe ^ymatch! ^yWait '
                             '^yuntil ^ythe ^ynext ^ysetup ^ytime.')
    elif server.GetClientInfo(index, INFO_REFSTATUS) == 'guest':
        server.Notify(index, '^yThis ^ycommand ^yhas ^ybeen ^ydisabled ^yfor ^yguest ^yreferees.')
    elif server.GetClientInfo(index, INFO_REFSTATUS) == 'normal':
        server.Notify(index, '^yThis ^ycommand ^yhas ^ybeen ^ydisabled ^yfor ^yreferees.')
    elif server.GetClientInfo(index, INFO_REFSTATUS) == 'god':
        server.Notify(index, '^yThis ^ycommand ^yhas ^ybeen ^ydisabled ^yfor ^ygod ^yreferees.')
    else:
        server.Notify(index,
                      '^yYou ^yare ^ynot ^ya ^yreferee.  ^yTo ^ybecome ^yreferee, ^ytype ^y"/refpwd ^y<password>"')
        server.Notify(index, '^yType ^y"/reflist" ^yto ^yget ^ythe ^ylist ^yof ^yall ^yreferees ^yon ^ythe ^yserver.')
