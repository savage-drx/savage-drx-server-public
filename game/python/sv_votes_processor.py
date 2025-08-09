# ---------------------------------------------------------------------------
#           Name: sv_votes_processor.py
#    Description: different vote handlers
# ---------------------------------------------------------------------------


import core
import server
import sv_maps
import sv_utils
import time
import sh_logger as log
import sv_events_handler
from sv_permissions import PermissionsContext as pc


class VoteSettings:
    # Sec:
    OUTCOME_PERIOD_MIN = 5 * 1000 * 60
    CALLVOTE_MSG_TIMEOUT = 60
    BASE_ALLOWABLE_HP_PERCENTAGE = 70
    # stateful:
    banned_client_uids = []
    is_outcome_enabled = False
    outcome_start_millis = 0
    are_self_buffs_enabled = True
    are_buff_pools_enabled = True


class Vote:
    ALLOWED = 1
    FORBIDDEN = 0

    VOTE_TYPE_HANDLERS = {
        'world': (lambda vote: process_world(vote)),
        'nextmap': (lambda vote: process_nextmap(vote)),
        'restartmatch': (lambda vote: process_restart(vote)),
        'msg': (lambda vote: process_msg(vote)),
        'draw': (lambda vote: process_draw(vote)),
        'concede': (lambda vote: process_concede(vote)),
        'shuffle': (lambda vote: process_shuffle(vote)),
        'even': (lambda vote: process_even(vote)),
        'elect': (lambda vote: process_elect(vote)),
        'kick': (lambda vote: process_kick(vote)),
        'impeach': (lambda vote: process_impeach(vote)),
        'mute': (lambda vote: process_mute(vote)),
        'switchteam': (lambda vote: process_switchteam(vote)),
        'lockspec': (lambda vote: process_lockspec(vote)),
        'movetospec': (lambda vote: process_movetospec(vote)),
        'nocomm': (lambda vote: process_nocomm(vote)),
        'swapbase': (lambda vote: process_swapbase(vote)),
        'commless': (lambda vote: process_commless(vote)),
        'ruleset': (lambda vote: process_ruleset(vote))
    }

    def __init__(self, client_index, vote_type, vote_info):
        # ex.: 1, user, elect (1: id of the voter)
        self.client_index = client_index
        self.vote_type = vote_type
        self.vote_info = vote_info
        self.is_vote_allowed = self.ALLOWED
        self.uid = server.GetClientInfo(self.client_index, INFO_UID)
        self.check_rights_for_vote()

    def check_rights_for_vote(self):
        # process_elect: 1, elect, drk

        if self.vote_type == 'msg':
            self.is_vote_allowed = int(pc.has_privilege('CAN_VOTE_MESSAGE', self.uid))
        if self.vote_type == 'elect':
            self.is_vote_allowed = int(pc.has_privilege('CAN_VOTE_ELECT', self.uid))
        if self.vote_type == 'impeach':
            self.is_vote_allowed = int(pc.has_privilege('CAN_VOTE_IMPEACH', self.uid))
        if self.vote_type == 'kick':
            self.is_vote_allowed = int(pc.has_privilege('CAN_VOTE_KICK', self.uid))
        if self.vote_type == 'lockspec':
            self.is_vote_allowed = int(pc.has_privilege('CAN_VOTE_LOCK_SPEC', self.uid))
        if self.vote_type == 'concede':
            self.is_vote_allowed = int(pc.has_privilege('CAN_VOTE_CONCEDE', self.uid))
        if self.vote_type == 'mute':
            self.is_vote_allowed = int(pc.has_privilege('CAN_VOTE_MUTE', self.uid))
        if self.vote_type == 'nextmap':
            self.is_vote_allowed = int(pc.has_privilege('CAN_VOTE_NEXT_MAP', self.uid))
        if self.vote_type == 'world':
            self.is_vote_allowed = int(pc.has_privilege('CAN_VOTE_MAP', self.uid))
        if self.vote_type == 'restartmatch':
            self.is_vote_allowed = int(pc.has_privilege('CAN_VOTE_RESTART', self.uid))
        if self.vote_type == 'draw':
            self.is_vote_allowed = int(pc.has_privilege('CAN_VOTE_DRAW', self.uid))
        if self.vote_type == 'shuffle':
            self.is_vote_allowed = int(pc.has_privilege('CAN_VOTE_SHUFFLE', self.uid))
        if self.vote_type == 'swapbase':
            self.is_vote_allowed = int(pc.has_privilege('CAN_VOTE_SWAP_BASE', self.uid))
        if self.vote_type == 'even':
            self.is_vote_allowed = int(pc.has_privilege('CAN_VOTE_EVEN', self.uid))
        if self.vote_type == 'switchteam':
            self.is_vote_allowed = int(pc.has_privilege('CAN_VOTE_SWITCH_TEAM', self.uid))
        if self.vote_type == 'movetospec':
            self.is_vote_allowed = int(pc.has_privilege('CAN_VOTE_MOVE_SPEC', self.uid))
        if self.vote_type == 'nocomm':
            self.is_vote_allowed = int(pc.has_privilege('CAN_VOTE_NO_COMM', self.uid))
        if self.vote_type == 'commless':
            self.is_vote_allowed = int(pc.has_privilege('CAN_VOTE_COMMLESS_MODE', self.uid))
        if self.vote_type == 'ruleset':
            self.is_vote_allowed = int(pc.has_privilege('CAN_VOTE_RULESET', self.uid))

        log.debug(f"Vote type: {self.vote_type}, info: {self.vote_info}, uid: {self.uid}, "
                  f"name: {server.GetClientInfo(self.client_index, INFO_NAME)}, "
                  f"isAllowed -> [{bool(self.is_vote_allowed)}]")

    def __str__(self):
        return str(self.__dict__)


@log.log_debug_info
def process_vote(client_index, vote_type, vote_info):
    vote_type = vote_type.lower()
    if vote_type not in Vote.VOTE_TYPE_HANDLERS:
        return Vote.ALLOWED

    vote = Vote(client_index, vote_type, vote_info)
    return Vote.VOTE_TYPE_HANDLERS[vote_type](vote)


@log.log_debug_info
def process_world(vote: Vote):
    if not vote.is_vote_allowed:
        return Vote.FORBIDDEN

    game_state = server.GetGameInfo(GAME_STATE)
    if game_state == 3 and int(core.CvarGetValue('sv_allowWorldVoteOnLowOnline')) == 0:
        # Notify client
        server.Notify(vote.client_index, '^900[World] ^yis ^900disabled ^ywhen ^ythe ^ygame ^yis ^yin ^yprogress.')
        return Vote.FORBIDDEN
    if sv_utils.are_commanders_elected() and game_state in [1, 2]:
        server.Notify(vote.client_index, '^900[World] ^ywas ^900disabled ^ysince ^ycommanders ^ywere ^yelected.')
        return Vote.FORBIDDEN

    # Block map votes between different modes
    current_game_type = core.CvarGetString('sv_map_gametype')

    if current_game_type == 'RTSS' and vote.vote_info.lower().startswith(('duel_', 'ig_')):
        return Vote.FORBIDDEN
    if current_game_type == 'DUEL' and not vote.vote_info.lower().startswith('duel_'):
        return Vote.FORBIDDEN
    if current_game_type == 'INSTAGIB' and not vote.vote_info.lower().startswith('ig_'):
        return Vote.FORBIDDEN

    return sv_maps.callvote(vote.client_index, vote.vote_info)


@log.log_debug_info
def process_nextmap(vote: Vote):
    if server.GetGameInfo(GAME_STATE) == 3:
        # Notify client
        server.Notify(vote.client_index, '^900[Nextmap] ^yis ^900disabled ^ywhen ^ythe ^ygame ^yis ^yin ^yprogress.')
        return Vote.FORBIDDEN
    if sv_utils.are_commanders_elected() and server.GetGameInfo(GAME_STATE) != 4:
        server.Notify(vote.client_index, '^900[Nextmap] ^ywas ^900disabled ^ysince ^ycommanders ^ywere ^yelected.')
        return Vote.FORBIDDEN
    return vote.is_vote_allowed


@log.log_debug_info
def process_restart(vote: Vote):
    if server.GetGameInfo(GAME_STATE) in [1, 2]:
        # Notify client
        server.Notify(vote.client_index, '^900[Restart] ^yis ^900disabled ^yin ^ythe ^ywarmup')
        return Vote.FORBIDDEN
    return vote.is_vote_allowed


@log.log_debug_info
def process_shuffle(vote: Vote):
    if server.GetGameInfo(GAME_STATE) == 3:
        # Notify client
        server.Notify(vote.client_index, '^900[Shuffle] ^yis ^900disabled ^ywhen ^ythe ^ygame ^yis ^yin ^yprogress.'
                                 ' Use ^900even ^yvote.')
        return Vote.FORBIDDEN
    return sv_maps.callvote(vote.client_index, vote.vote_info)


@log.log_debug_info
def process_msg(vote: Vote):
    return vote.is_vote_allowed


@log.log_debug_info
def process_kick(vote: Vote):
    return vote.is_vote_allowed


@log.log_debug_info
def process_impeach(vote: Vote):
    return vote.is_vote_allowed


@log.log_debug_info
def process_mute(vote: Vote):
    affected_index = sv_utils.getIndexFromFullName(vote.vote_info)
    if sv_utils.is_commander(affected_index):
        affected_name = server.GetClientInfo(affected_index, INFO_NAME)
        log.info("Commander '%s' can not be muted!" % affected_name)
        server.Notify(vote.client_index, "^yCommander ^900'%s' ^ycan ^ynot ^ybe ^ymuted!" % affected_name)
        return Vote.FORBIDDEN

    return vote.is_vote_allowed


@log.log_debug_info
def process_even(vote: Vote):
    return vote.is_vote_allowed


@log.log_debug_info
def process_elect(vote: Vote):
    if not vote.is_vote_allowed:
        return vote.is_vote_allowed

    if '#' in vote.vote_info:
        target_index = int(vote.vote_info.replace("#", ""))
    else:
        target_index = sv_utils.getIndexFromFullName(str(vote.vote_info))

    if target_index is None:
        return Vote.FORBIDDEN

    uid = server.GetClientInfo(target_index, INFO_UID)
    if not pc.has_privilege('CAN_COMMAND', uid):
        server.Notify(vote.client_index, f'{vote.vote_info} is not allowed to command')
        return Vote.FORBIDDEN

    return vote.is_vote_allowed


@log.log_debug_info
def process_switchteam(vote: Vote):
    return vote.is_vote_allowed


@log.log_debug_info
def process_lockspec(vote: Vote):
    return vote.is_vote_allowed


@log.log_debug_info
def process_movetospec(vote: Vote):
    return vote.is_vote_allowed


@log.log_debug_info
def process_nocomm(vote: Vote):
    return vote.is_vote_allowed


@log.log_debug_info
def process_swapbase(vote: Vote):
    return vote.is_vote_allowed


@log.log_debug_info
def process_commless(vote: Vote):
    return vote.is_vote_allowed


@log.log_debug_info
def process_ruleset(vote: Vote):
    return vote.is_vote_allowed


@log.log_debug_info
def process_draw(vote: Vote):
    if server.GetGameInfo(GAME_STATE) == 3 and not is_outcome_passed():
        # Notify client
        server.Notify(vote.client_index, '^yDraw ^yvotes ^ywere ^900blocked ^yfor ^y5 ^yminutes')
        return Vote.FORBIDDEN
    base = sv_utils.are_bases_damaged(VoteSettings.BASE_ALLOWABLE_HP_PERCENTAGE)
    if base:
        server.Notify(vote.client_index,
                      "^yDraw ^yvote ^900is ^900blocked ^ybecause ^y%s's ^yHP ^yis ^900less ^900than ^900%s%%" %
                      (base['base_name'], VoteSettings.BASE_ALLOWABLE_HP_PERCENTAGE))
        log.info("Draw vote was blocked because %s's HP is less than %s percent"
                  % (base['base_name'], VoteSettings.BASE_ALLOWABLE_HP_PERCENTAGE))
        return Vote.FORBIDDEN
    return vote.is_vote_allowed


@log.log_debug_info
def process_concede(vote: Vote):
    return vote.is_vote_allowed


@log.log_debug_info
def outcome_restricts():
    VoteSettings.is_outcome_enabled = True
    VoteSettings.outcome_start_millis = int(round(time.time() * 1000))
    server.Broadcast("^gDRAW ^yvotes ^ywere ^900blocked ^yfor ^900%s ^yminutes" %
                     (VoteSettings.OUTCOME_PERIOD_MIN / 1000 / 60))


@log.log_debug_info
def is_outcome_passed():
    current_time_millis = int(round(time.time() * 1000))
    if VoteSettings.is_outcome_enabled:
        if current_time_millis > VoteSettings.outcome_start_millis + VoteSettings.OUTCOME_PERIOD_MIN:
            VoteSettings.is_outcome_enabled = False
        else:
            return False
    return True


@log.log_debug_info
def toggle_april_fools():
    core.CvarSetValue('sv_enableAprilFools', 0 if int(core.CvarGetValue('sv_enableAprilFools')) else 1)
    is_april_fools_enabled = int(core.CvarGetValue('sv_enableAprilFools'))

    if core.CvarGetString('sv_map_gametype') == "INSTAGIB":
        return

    if is_april_fools_enabled:
        core.CommandExec('objedit human_nomad; objSet forceInventory1 human_boomerang')
        core.CommandExec('objedit beast_scavenger; objSet forceInventory1 beast_skullstack')
    else:
        core.CommandExec('objedit human_nomad; objSet forceInventory1 \"\"')
        core.CommandExec('objedit beast_scavenger; objSet forceInventory1 \"\"')

    log.info("sv_enableAprilFools was changed to %s" % int(core.CvarGetValue('sv_enableAprilFools')))


@log.log_debug_info
def custom_elect(client_index, team):
    core.CommandExec('switchteam %s %s' % (team, client_index))
    core.CommandExec('setcmdr %s' % client_index)


@log.log_debug_info
def has_vote_timeout_passed(vote):
    uid = int(server.GetClientInfo(vote.client_index, INFO_UID))
    name = server.GetClientInfo(vote.client_index, INFO_NAME)
    clan_id = int(server.GetClientInfo(vote.client_index, INFO_CLANID))
    if clan_id == 0:
        on_team_time = int(server.GetClientInfo(vote.client_index, STAT_ONTEAMTIME))
        if on_team_time / 1000 < VoteSettings.CALLVOTE_MSG_TIMEOUT:
            server.Notify(vote.client_index, '^yWait ^ya ^ybit ^yuntil ^yyou ^yare ^yable ^yto ^ycall ^ythis ^yvote.')
            log.warn("Forbidden (OnTeamTime): %s, Type: %s, Info: %s, Uid: %s, ClanId: %s, Name: %s" %
                     (on_team_time, vote.vote_type, vote.vote_info, uid, clan_id, name))
            return Vote.FORBIDDEN
    return Vote.ALLOWED


@log.log_debug_info
def ban_siege_camper(client_index):
    uid = server.GetClientInfo(client_index, INFO_UID)
    VoteSettings.banned_client_uids.append(uid)
    server.Broadcast('^ySiege ^ywas ^900banned ^yfor ^g%s' % server.GetClientInfo(client_index, INFO_NAME))
    sv_events_handler.warn_and_change_unit(client_index)


@log.log_debug_info
def unban_siege_for_one(client_index):
    uid = server.GetClientInfo(client_index, INFO_UID)
    if uid in VoteSettings.banned_client_uids:
        VoteSettings.banned_client_uids.remove(uid)
        server.Broadcast('^ySiege ^ywas ^900un^gbanned ^yfor ^g%s' % server.GetClientInfo(client_index, INFO_NAME))
        server.Notify(client_index, 'Siege is unbanned for you!')


@log.log_debug_info
def reset_custom_vote_settings():
    VoteSettings.banned_client_uids = []
    VoteSettings.are_self_buffs_enabled = True
    VoteSettings.are_buff_pools_enabled = True
    core.CvarSetValue('sv_allowPowerupRequests', 1)


@log.log_debug_info
def check_custom_vote_settings_on_start():
    core.CvarSetValue('sv_allowPowerupRequests', int(VoteSettings.are_self_buffs_enabled))
    core.CvarSetValue('sv_allowFillBuffPool', int(VoteSettings.are_buff_pools_enabled))
    VoteSettings.banned_client_uids = []


@log.log_debug_info
def enable_self_buffs():
    core.CvarSetValue('sv_allowPowerupRequests', 1)
    server.Broadcast('^ySelf ^ybuffs ^ywere ^900enabled!')
    VoteSettings.are_self_buffs_enabled = True


@log.log_debug_info
def disable_self_buffs():
    core.CvarSetValue('sv_allowPowerupRequests', 0)
    server.Broadcast('^ySelf ^ybuffs ^ywere ^900disabled ^yfor ^ythis ^yround!')
    VoteSettings.are_self_buffs_enabled = False


@log.log_debug_info
def enable_buff_pools():
    core.CvarSetValue('sv_allowFillBuffPool', 1)
    server.Broadcast('^yBuff ^ypools ^ywere ^900enabled!')
    VoteSettings.are_buff_pools_enabled = True


@log.log_debug_info
def disable_buff_pools():
    core.CvarSetValue('sv_allowFillBuffPool', 0)
    server.Broadcast('^yBuff ^ypools ^ywere ^900disabled ^yfor ^ythis ^yround!')
    VoteSettings.are_buff_pools_enabled = False


# def enable_bots():
#     core.CvarSetValue('sv_botEnable', 2)
#     server.Broadcast('^yBots ^ywere ^900enabled!')


# def disable_bots():
#     core.CvarSetValue('sv_botEnable', 0)
#     online_state = sv_utils.OnlineState()
#     for bot in online_state.bots:
#         core.CommandExec('botrem %s' % bot)
#     server.Broadcast('^yBots ^ywere ^900disabled ^yfor ^ythis ^yround!')
