# ------------------------------------------------------------------------------------------------
#           Name: sv_warmup.py
#    Description: events and state for the warmup stage
# ------------------------------------------------------------------------------------------------


import core
import random
import server

import sh_logger as log
import sv_utils
import sh_custom_utils


class _Context:
    is_enabled = False
    strategy = None
    spawned_client_indices = set()
    ON_FRAME_EVENT_INTERVAL_SECONDS = 20
    GIVE_STATE_DURATION_SECONDS = 10


def start():
    try:
        __init_strategy()
        _Context.is_enabled = python_config.getboolean('Python_Warmup', 'IS_WARMUP_ENABLED')
        # Warmup is not available for Instagib
        _Context.is_enabled = _Context.is_enabled and core.CvarGetString('sv_map_gametype') not in ["INSTAGIB", "DUEL"]
        _Context.ON_FRAME_EVENT_INTERVAL_SECONDS = python_config.getint('Python_Warmup',
                                                                        'ON_FRAME_EVENT_INTERVAL_SECONDS')
        _Context.GIVE_STATE_DURATION_SECONDS = python_config.getint('Python_Warmup', 'GIVE_STATE_DURATION_SECONDS')
        log.info("Warmup events were enabled")
    except:
        sh_custom_utils.get_and_log_exception_info()


def stop():
    _Context.is_enabled = False
    _Context.spawned_client_indices = set()
    log.info("Warmup events were disabled")


def on_spawn(client_index: int):
    if _Context.is_enabled:
        try:
            if client_index in _Context.spawned_client_indices:
                return
            else:
                _Context.spawned_client_indices.add(client_index)

            _Context.strategy.on_spawn(client_index)
        except:
            sh_custom_utils.get_and_log_exception_info()


def on_death(client_index: int):
    if _Context.is_enabled:
        try:
            if client_index in _Context.spawned_client_indices:
                _Context.spawned_client_indices.remove(client_index)
        except:
            sh_custom_utils.get_and_log_exception_info()


def on_frame():
    if _Context.is_enabled:
        try:
            _Context.strategy.on_frame()
        except:
            sh_custom_utils.get_and_log_exception_info()


# ___ PRIVATE ________________________________________________________________


def __init_strategy():
    _Context.strategy = SimpleStrategy()


class SimpleStrategy:
    latest_check_with_interval = 0

    def __init__(self):
        self.human_units = SimpleStrategy.init_s_entity(Props.HUMAN_UNITS)
        self.human_weapons = SimpleStrategy.init_q_entity(Props.HUMAN_WEAPONS)
        self.human_items = SimpleStrategy.init_q_entity(Props.HUMAN_ITEMS)
        self.human_states = SimpleStrategy.init_s_entity(Props.HUMAN_STATES)

        self.beast_units = SimpleStrategy.init_s_entity(Props.BEAST_UNITS)
        self.beast_weapons = SimpleStrategy.init_q_entity(Props.BEAST_WEAPONS)
        self.beast_items = SimpleStrategy.init_q_entity(Props.BEAST_ITEMS)
        self.beast_states = SimpleStrategy.init_s_entity(Props.BEAST_STATES)
        self.beast_melee = SimpleStrategy.init_s_entity(Props.BEAST_MELEE)

    @staticmethod
    def init_s_entity(props: dict):
        return _Entity(props.keys(), [x['weight'] for x in props.values()])

    @staticmethod
    def init_q_entity(props: dict):
        return _QEntity([{x: props[x]['amount']} for x in props.keys()], [x['weight'] for x in props.values()])

    def on_spawn(self, client_index):
        team = server.GetClientInfo(client_index, INFO_TEAM)

        if team > 0 and team % 2 == 1:
            SimpleStrategy.on_human_spawn(self, client_index)

        if team > 0 and team % 2 == 0:
            SimpleStrategy.on_beast_spawn(self, client_index)

    def on_frame(self):
        current_game_time_seconds = sv_utils.get_game_time_in_seconds()
        if current_game_time_seconds >= _Context.ON_FRAME_EVENT_INTERVAL_SECONDS + self.latest_check_with_interval:
            self.latest_check_with_interval = current_game_time_seconds
            online = sv_utils.OnlineState()
            for x in online.teams.values():
                # beast team
                if x.team_id != 0 and x.team_id % 2 == 0:
                    for p in x.players.keys():
                        state = self.beast_states.get_one_random_value()
                        core.CommandExec('givestate %s %s %s' % (p, state, _Context.GIVE_STATE_DURATION_SECONDS * 1000))
                # human team
                if x.team_id != 0 and x.team_id % 2 == 1:
                    for p in x.players.keys():
                        state = self.human_states.get_one_random_value()
                        core.CommandExec('givestate %s %s %s' % (p, state, _Context.GIVE_STATE_DURATION_SECONDS * 1000))

    def on_human_spawn(self, client_index):
        try:
            unit = self.human_units.get_one_random_value()

            server.GameScript(client_index, '!changeunit target %s' % unit)
            if unit == 'hero_jeraziah':
                server.GameScript(client_index, '!give target {} {} {}'.format('hero_jeraziah_weapon', 0, 1))
                server.GameScript(client_index, '!give target {} {} {}'.format('hero_jeraziah_incandescence', 0, 2))
                server.GameScript(client_index, '!give target {} {} {}'.format('hero_jeraziah_planter', 0, 3))
                server.GameScript(client_index, '!give target {} {} {}'.format('hero_jeraziah_avatar', 0, 4))
                return
            if unit == 'human_medic':
                item = self.human_items.get_random_values(1)[0]
                server.GameScript(client_index, '!give target {} {} {}'.format('human_heal', 0, 1))
                server.GameScript(client_index, '!give target {} {} {}'.format('human_potion', 15, 2))
                server.GameScript(client_index, '!give target {} {} {}'.format('human_revive', 0, 3))
                # next(iter(item)) - gets the first key of the dict and item[next(iter(item))] - the value
                # next(iter(x)) is faster than dict[0]
                server.GameScript(client_index, '!give target {} {} {}'
                                  .format(next(iter(item)), item[next(iter(item))], 4))
                return

            # provide weapon
            weapon = self.human_weapons.get_random_values(1)[0]
            # item, amount, slot
            server.GameScript(client_index, '!give target {} {} {}'
                              .format(next(iter(weapon)), weapon[next(iter(weapon))], 1))

            # provide items (3 slots)
            items = self.human_items.get_random_values(3)
            slot_a, slot_b, slot_c = items[0], items[1], items[2]
            server.GameScript(client_index,
                              '!give target {} {} {}'.format(next(iter(slot_a)), slot_a[next(iter(slot_a))], 2))
            server.GameScript(client_index,
                              '!give target {} {} {}'.format(next(iter(slot_b)), slot_b[next(iter(slot_b))], 3))
            server.GameScript(client_index,
                              '!give target {} {} {}'.format(next(iter(slot_c)), slot_c[next(iter(slot_c))], 4))
        except:
            sh_custom_utils.get_and_log_exception_info()

    def on_beast_spawn(self, client_index):
        try:
            unit = self.beast_units.get_one_random_value()

            server.GameScript(client_index, '!changeunit target %s' % unit)
            if unit == 'hero_ophelia':
                server.GameScript(client_index, '!give target {} {} {}'.format('hero_ophelia_weapon', 0, 1))
                server.GameScript(client_index, '!give target {} {} {}'.format('beast_shield', 0, 3))
                server.GameScript(client_index, '!give target {} {} {}'.format('hero_ophelia_teleport', 0, 4))
                return
            if unit == 'beast_medic':
                item = self.beast_items.get_random_values(1)[0]
                server.GameScript(client_index, '!give target {} {} {}'.format('beast_heal', 0, 1))
                server.GameScript(client_index, '!give target {} {} {}'.format('beast_revive', 0, 2))
                server.GameScript(client_index, '!give target {} {} {}'.format('beast_shield', 0, 3))
                server.GameScript(client_index, '!give target {} {} {}'
                                  .format(next(iter(item)), item[next(iter(item))], 4))
                return

            # provide weapon
            weapon = self.beast_weapons.get_random_values(1)[0]
            # item, amount, slot
            server.GameScript(client_index, '!give target {} {} {}'
                              .format(next(iter(weapon)), weapon[next(iter(weapon))], 1))

            # provide melee
            melee = self.beast_melee.get_one_random_value()
            # item, amount, slot
            server.GameScript(client_index, '!give target {} {} {}'.format(melee, 0, 0))

            # provide items (3 slots)
            items = self.beast_items.get_random_values(3)
            slot_a, slot_b, slot_c = items[0], items[1], items[2]
            server.GameScript(client_index,
                              '!give target {} {} {}'.format(next(iter(slot_a)), slot_a[next(iter(slot_a))], 2))
            server.GameScript(client_index,
                              '!give target {} {} {}'.format(next(iter(slot_b)), slot_b[next(iter(slot_b))], 3))
            server.GameScript(client_index,
                              '!give target {} {} {}'.format(next(iter(slot_c)), slot_c[next(iter(slot_c))], 4))

        except:
            sh_custom_utils.get_and_log_exception_info()


class _Entity:
    def __init__(self, names, weights):
        self.names = list(names)
        self.weights = list(map(lambda x: x / sum(weights), weights))

    def get_one_random_value(self):
        return random.choices(population=self.names, weights=self.weights, k=1)[0]


class _QEntity:
    def __init__(self, names, weights):
        self.names = list(names)
        self.weights = list(map(lambda x: x / sum(weights), weights))

    def get_random_values(self, quantity):
        choices = list()
        _names = list(self.names)
        _weights = list(self.weights)

        for x in range(quantity):
            chosen = random.choices(population=_names, weights=_weights, k=1)[0]
            choices.append(chosen)
            index = _names.index(chosen)
            del _names[index]
            del _weights[index]

        return choices


class Props:
    HUMAN_UNITS = {
        'human_nomad': {'weight': 0.2},
        'human_medic': {'weight': 0.18},
        'human_savage': {'weight': 0.17},
        'human_legionnaire': {'weight': 0.15},
        'hero_jeraziah': {'weight': 0.1}
    }
    HUMAN_WEAPONS = {
        'human_bow': {'weight': 0.01, 'amount': 20},
        'human_scattergun': {'weight': 0.2, 'amount': 30},
        'human_discharger': {'weight': 0.2, 'amount': 50},
        'human_incinerator': {'weight': 0.08, 'amount': 50},
        'human_crossbow': {'weight': 0.15, 'amount': 30},
        'human_repeater': {'weight': 0.15, 'amount': 200},
        'human_fluxgun': {'weight': 0.1, 'amount': 150},
        'human_mortar': {'weight': 0.2, 'amount': 30},
        'human_sniperbow': {'weight': 0.15, 'amount': 20},
        'human_coilrifle': {'weight': 0.15, 'amount': 30},
        'human_pulsegun': {'weight': 0.15, 'amount': 40},
        'human_launcher': {'weight': 0.15, 'amount': 30},
        'human_boomerang': {'weight': 0.1, 'amount': 50},
        'human_ak47': {'weight': 0.1, 'amount': 150}
    }
    HUMAN_ITEMS = {
        'human_medkit': {'weight': 0.3, 'amount': 3},
        'human_motion_sensor': {'weight': 0.01, 'amount': 3},
        'human_disruptor': {'weight': 0.15, 'amount': 3},
        'human_demo_pack': {'weight': 0.2, 'amount': 1},
        'human_imobilizer': {'weight': 0.15, 'amount': 3},
        'human_relocater': {'weight': 0.1, 'amount': 1},
        'human_landmine': {'weight': 0.15, 'amount': 5}
    }
    BEAST_UNITS = {
        'beast_scavenger': {'weight': 0.08},
        'beast_medic': {'weight': 0.10},
        'beast_stalker': {'weight': 0.17},
        'beast_predator': {'weight': 0.5},
        'hero_ophelia': {'weight': 0.04}
    }
    BEAST_MELEE = {
        'beast_poison': {'weight': 0.1},
        'beast_rabid': {'weight': 0.4},
        'beast_vampire': {'weight': 0.2},
    }
    BEAST_WEAPONS = {
        'beast_fire1': {'weight': 0.12, 'amount': 0},
        'beast_fire2': {'weight': 0.15, 'amount': 0},
        'beast_fire3': {'weight': 0.17, 'amount': 0},
        'beast_entropy1': {'weight': 0.11, 'amount': 0},
        'beast_entropy2': {'weight': 0.15, 'amount': 0},
        'beast_entropy3': {'weight': 0.17, 'amount': 0},
        'beast_strata1': {'weight': 0.11, 'amount': 0},
        'beast_strata2': {'weight': 0.15, 'amount': 0},
        'beast_strata3': {'weight': 0.12, 'amount': 0},
        'beast_skullstack': {'weight': 0.08, 'amount': 30}
    }
    BEAST_ITEMS = {
        'beast_tracking_sense': {'weight': 0.15, 'amount': 0},
        'beast_protect': {'weight': 0.1, 'amount': 1},
        'beast_fire_trap': {'weight': 0.15, 'amount': 5},
        'beast_stamina_boost': {'weight': 0.2, 'amount': 1},
        'beast_snare': {'weight': 0.2, 'amount': 2},
        'beast_camouflage': {'weight': 0.15, 'amount': 1},
        'beast_immolate': {'weight': 0.15, 'amount': 1}
    }
    HUMAN_STATES = {
        'adrenaline': {'weight': 0.2},
        'electrify': {'weight': 0.1},
        'magshield': {'weight': 0.2},
        'beast_camouflage': {'weight': 0.15},
        'fire_shield': {'weight': 0.2}
    }
    BEAST_STATES = {
        'adrenaline': {'weight': 0.22},
        'magshield': {'weight': 0.17},
        'beast_camouflage': {'weight': 0.15},
        'fire_shield': {'weight': 0.2}
    }
    NPC_UNITS = {
        'npc_kongor': {'weight': 1},
        'npc_hornman': {'weight': 1},
        'npc_hunchedbeast': {'weight': 1},
        'npc_chiprel': {'weight': 1},
        'npc_monkit': {'weight': 1},
        'npc_mudent': {'weight': 1},
        'npc_oschore': {'weight': 1},
        'npc_gerkat': {'weight': 1},
        'npc_bearloth': {'weight': 1},
        'npc_zizard': {'weight': 1},
        'npc_buffalo_plains': {'weight': 1},
        'npc_buffalo_snow': {'weight': 1},
        'npc_terror': {'weight': 1},
        'npc_mercenary': {'weight': 1},
        'npc_berserker': {'weight': 1},
        'npc_skeleton_guard': {'weight': 1},
        'npc_skeleton_worker': {'weight': 1},
        'npc_ronin': {'weight': 1},
        'npc_macaque': {'weight': 1},
        'npc_panda': {'weight': 1}
    }
