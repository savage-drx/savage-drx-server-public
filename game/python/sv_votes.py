# ------------------------------------------------------------------------------------------------
#           Name: sv_votes.py
#    Description: Silverback Vote Event Entries (init, callvote, callcustomvote, passcustomvote)
# ------------------------------------------------------------------------------------------------

# Savage API
import core
import server

# Savage Modules
import sv_defs
import sh_custom_utils
import sv_votes_processor
import sv_utils
import sh_logger as log
from sv_permissions import PermissionsContext as pc


# -------------------------------
# Called directly by Silverback
# -------------------------------
def init():
    log.info("Initializing Custom Votes...")


class CustomVote:
    CAMPER = 'camper'
    OUTCOME = 'outcome'
    UN_BAN = 'unban'
    APRIL_FOOLS = 'april-fools'
    ELECT = 'elect'
    ENABLE_SELF_BUFFS = 'enable-self-buffs'
    DISABLE_SELF_BUFFS = 'disable-self-buffs'
    ENABLE_BUFF_POOLS = 'enable-buff-pools'
    DISABLE_BUFF_POOLS = 'disable-buff-pools'
    # ENABLE_BOTS = 'enable-bots'
    # DISABLE_BOTS = 'disable-bots'

    ON_CUSTOM_VOTE_CALL = {
        CAMPER: (lambda vi: camper(vi.client_index, vi.vote_info)),
        OUTCOME: (lambda vi: outcome(vi.vote_info)),
        UN_BAN: (lambda vi: unban(vi.client_index, vi.vote_info)),
        APRIL_FOOLS: (lambda vi: april_fools(vi.client_index, vi.vote_info)),
        ELECT: (lambda vi: elect(vi.client_index, vi.vote_info)),
        ENABLE_SELF_BUFFS: (lambda vi: enable_self_buffs(vi.client_index, vi.vote_info)),
        DISABLE_SELF_BUFFS: (lambda vi: disable_self_buffs(vi.client_index, vi.vote_info)),
        ENABLE_BUFF_POOLS: (lambda vi: enable_buff_pools(vi.client_index, vi.vote_info)),
        DISABLE_BUFF_POOLS: (lambda vi: disable_buff_pools(vi.client_index, vi.vote_info)),
        # ENABLE_BOTS: (lambda vi: enable_bots(vi.client_index, vi.vote_info)),
        # DISABLE_BOTS: (lambda vi: disable_bots(vi.client_index, vi.vote_info))
    }

    ON_CUSTOM_VOTE_PASS = {
        CAMPER: (lambda vote: sv_votes_processor.ban_siege_camper(vote.affected_index)),
        OUTCOME: (lambda vote: sv_votes_processor.outcome_restricts()),
        UN_BAN: (lambda vote: sv_votes_processor.unban_siege_for_one(vote.affected_index)),
        APRIL_FOOLS: (lambda vote: sv_votes_processor.toggle_april_fools()),
        ELECT: (lambda vote: sv_votes_processor.custom_elect(vote.affected_index, vote.vote_info.split(" ")[0])),
        ENABLE_SELF_BUFFS: (lambda vote: sv_votes_processor.enable_self_buffs()),
        DISABLE_SELF_BUFFS: (lambda vote: sv_votes_processor.disable_self_buffs()),
        ENABLE_BUFF_POOLS: (lambda vote: sv_votes_processor.enable_buff_pools()),
        DISABLE_BUFF_POOLS: (lambda vote: sv_votes_processor.disable_buff_pools()),
        # ENABLE_BOTS: (lambda vote: sv_votes_processor.enable_bots()),
        # DISABLE_BOTS: (lambda vote: sv_votes_processor.disable_bots())
    }

    # Valid vote
    VOTE_VALID = 1
    # Client gets a message: "Invalid custom vote"
    VOTE_INVALID = 0
    # No message for client
    VOTE_INVALID_NO_WARNING = -1
    # passed
    VOTE_PASSED = 1
    # not passed
    VOTE_NOT_PASSED = 0

    ACCEPT_IS_NOT_NEEDED = 1
    ACCEPT_IS_NEEDED = 0

    ALL_TEAMS_CAN_VOTE = 0
    ONE_TEAM_VOTE = 1

    UID_IS_NOT_NEEDED = -1

    def __init__(self,
                 vote_name='',
                 vote_info='',
                 vote_type='',
                 pass_percent=1.00,
                 affected_index=UID_IS_NOT_NEEDED,
                 does_not_need_acceptance=ACCEPT_IS_NOT_NEEDED,
                 votable_by=ALL_TEAMS_CAN_VOTE,
                 vote_result=VOTE_INVALID,
                 voted_by_uid=UID_IS_NOT_NEEDED):
        self.vote_name = vote_name
        self.vote_info = vote_info
        self.vote_type = vote_type
        # float
        self.pass_percent = pass_percent
        # -1 = none
        self.affected_index = affected_index
        # 0 - Player has accepted/has refused the vote
        # 1 - vote goes on
        self.does_not_need_acceptance = does_not_need_acceptance
        # 1 = TEAM; Set 0 if you want to allow both teams to vote
        self.votable_by = votable_by
        self.vote_result = vote_result
        self.voted_by_uid = voted_by_uid

    def enable_core_vars(self):
        CustomVote.set_core_vars(self.vote_name, self.vote_info, self.vote_type, self.pass_percent,
                                 self.affected_index, self.does_not_need_acceptance, self.votable_by)

    @staticmethod
    def set_core_vars(vote_name, vote_info, vote_type, pass_percent,
                      affected_index, does_not_need_acceptance, votable_by):
        core.CvarSetString('sv_customVoteName', vote_name)
        core.CvarSetString('sv_customVoteInfo', vote_info)
        core.CvarSetString('sv_customVoteType', vote_type)
        core.CvarSetValue('sv_customVotePassPercent', pass_percent)
        core.CvarSetValue('sv_customVoteAffectedIndex', affected_index)
        core.CvarSetValue('sv_customVoteMalus', does_not_need_acceptance)
        core.CvarSetValue('sv_customVoteVotableBy', votable_by)

    @staticmethod
    def reset_core_vars():
        CustomVote.set_core_vars(
            '',
            '',
            '',
            1.00,
            CustomVote.UID_IS_NOT_NEEDED,
            CustomVote.ACCEPT_IS_NOT_NEEDED,
            CustomVote.ALL_TEAMS_CAN_VOTE)


class VoteInfo:
    def __init__(self, client_index, vote_type, vote_info):
        self.client_index = client_index
        self.vote_type = vote_type
        self.vote_info = vote_info

    def __str__(self):
        return "VoteInfo index: %s, type: %s, info: %s" % (self.client_index, self.vote_type, self.vote_info)


# -------------------------------
# Called directly by Silverback
# -------------------------------
@log.log_debug_info
def callvote(client_index, vote_type, vote_info):
    # Accept vote by default
    answer = 1
    try:
        answer = sv_votes_processor.process_vote(client_index, vote_type, vote_info)
    except:
        sh_custom_utils.get_and_log_exception_info()

    return answer


# -------------------------------
# Called directly by Silverback
# -------------------------------
@log.log_debug_info
def callcustomvote(client_index, vote_type, vote_info):
    uid = server.GetClientInfo(client_index, INFO_UID)
    if not pc.has_privilege('CAN_VOTE_CUSTOM', uid):
        return CustomVote.VOTE_INVALID_NO_WARNING

    if vote_type:
        vote_type = vote_type.lower()

    log.info(f'Custom vote uid: {uid}, type: {vote_type}, info {vote_info}')

    global custom_vote
    custom_vote = None
    CustomVote.reset_core_vars()

    if vote_type not in CustomVote.ON_CUSTOM_VOTE_CALL:
        server.Notify(client_index, '^yWrong ^ycustom ^yvote. ^ySay ^900!help ^yfor ^ymore ^yinfo')
        return CustomVote.VOTE_INVALID_NO_WARNING

    try:
        custom_vote = CustomVote.ON_CUSTOM_VOTE_CALL[vote_type](VoteInfo(client_index, vote_type, vote_info))
        custom_vote.enable_core_vars()
    except:
        sh_custom_utils.get_and_log_exception_info()

    log.info("Custom vote answer: [%s]" % custom_vote.vote_result)
    return custom_vote.vote_result


# -------------------------------
# Called directly by Silverback
# -------------------------------
@log.log_debug_info
def passcustomvote(yes, no):
    log.info(f'Custom vote passed: {yes} vs {no}')

    try:
        CustomVote.ON_CUSTOM_VOTE_PASS[custom_vote.vote_type](custom_vote)
    except:
        sh_custom_utils.get_and_log_exception_info()

    return CustomVote.VOTE_PASSED


def camper(client_index: int, vote_info: str):
    # Invalid custom vote (built-in message)
    if vote_info == '':
        return CustomVote(vote_result=CustomVote.VOTE_INVALID)

    if sv_defs.clientList_Team[client_index] == 0:
        server.Notify(client_index, 'Custom vote is forbidden for specs')
        return CustomVote(vote_result=CustomVote.VOTE_INVALID_NO_WARNING)

    affected_index = sv_utils.getIndexFromFullName(str(vote_info))
    if affected_index is None:
        server.Notify(client_index, '%s is not found' % vote_info)
        return CustomVote(vote_result=CustomVote.VOTE_INVALID_NO_WARNING)
    else:
        return CustomVote(
            'Ban siege for %s' % vote_info,
            vote_info, CustomVote.CAMPER,
            0.50,
            int(affected_index),
            CustomVote.ACCEPT_IS_NOT_NEEDED,
            CustomVote.ALL_TEAMS_CAN_VOTE,
            CustomVote.VOTE_VALID)


def april_fools(client_index: int, vote_info: str):
    if server.GetGameInfo(GAME_STATE) not in {1, 2}:
        server.Notify(client_index,
                      '^yApril ^yfool\'s ^yvote is ^900disabled ^ywhen ^ythe ^ygame ^yis ^yin ^yprogress.')
        return CustomVote(vote_result=CustomVote.VOTE_INVALID_NO_WARNING)

    vote_info_values = {'enable', 'disable'}
    vote_info = vote_info.lower()
    if vote_info not in vote_info_values:
        return CustomVote(vote_result=CustomVote.VOTE_INVALID)

    is_april_fools_enabled = int(core.CvarGetValue('sv_enableAprilFools'))

    if (vote_info == 'enable' and is_april_fools_enabled is 1) or (
                    vote_info == 'disable' and is_april_fools_enabled is 0):
        server.Notify(client_index, 'April fool\'s is already ^900%sd' % vote_info)
        return CustomVote(vote_result=CustomVote.VOTE_INVALID_NO_WARNING)

    # Toggle April-Fools items
    return CustomVote(
        '%s april fool\'s' % vote_info,
        vote_info,
        CustomVote.APRIL_FOOLS,
        0.60,
        CustomVote.UID_IS_NOT_NEEDED,
        CustomVote.ACCEPT_IS_NOT_NEEDED,
        CustomVote.ALL_TEAMS_CAN_VOTE,
        CustomVote.VOTE_VALID)


@log.log_debug_info
def elect(client_index: int, vote_info: str):
    # Invalid custom vote (built-in message)
    if vote_info == '':
        return CustomVote(vote_result=CustomVote.VOTE_INVALID)

    # check if game is in the warmup state
    if server.GetGameInfo(GAME_STATE) >= 3:
        server.Notify(client_index, '^yCustom ^yelect ^yvote ^yis ^yallowed ^yonly ^yin ^ythe ^900warmup')
        return CustomVote(vote_result=CustomVote.VOTE_INVALID_NO_WARNING)

    split = vote_info.split(" ")
    # check that vote has 1-4 team and comm name
    teams = sv_utils.get_teams()

    if len(split) < 2:
        server.Notify(client_index, '^yRead ^y!help ^yfor ^ymore ^yinfo')
        return CustomVote(vote_result=CustomVote.VOTE_INVALID_NO_WARNING)

    try:
        if int(split[0]) not in range(1, len(teams) + 1):
            server.Notify(client_index, '^yRead ^y!help ^yfor ^ymore ^yinfo')
            return CustomVote(vote_result=CustomVote.VOTE_INVALID_NO_WARNING)
    except:
        server.Notify(client_index, '^yRead ^y!help ^yfor ^ymore ^yinfo')
        return CustomVote(vote_result=CustomVote.VOTE_INVALID_NO_WARNING)

    # check if team already has a commander
    if sv_defs.teamList_Commander[int(split[0])] != -1:
        server.Notify(client_index, '^yTeam ^y%s ^yalready ^900has ^ya ^ycommander!' % split[0])
        return CustomVote(vote_result=CustomVote.VOTE_INVALID_NO_WARNING)

    full_name = str(" ".join(split[1:]))
    target_index = sv_utils.getIndexFromFullName(full_name)
    if target_index is None:
        server.Notify(client_index, f'{full_name} was not found')
        return CustomVote(vote_result=CustomVote.VOTE_INVALID_NO_WARNING)

    target_uid = server.GetClientInfo(target_index, INFO_UID)
    if not pc.has_privilege('CAN_COMMAND', target_uid):
        server.Notify(client_index, f'{full_name} is not allowed to command')
        return CustomVote(vote_result=CustomVote.VOTE_INVALID_NO_WARNING)

    return CustomVote(
        f'Elect {full_name} for T{split[0]}',
        vote_info,
        CustomVote.ELECT, 0.60,
        int(target_index),
        CustomVote.ACCEPT_IS_NEEDED,
        CustomVote.ALL_TEAMS_CAN_VOTE,
        CustomVote.VOTE_VALID)


def unban(client_index: int, vote_info: str):
    # Invalid custom vote (built-in message)
    if vote_info == '':
        return CustomVote(vote_result=CustomVote.VOTE_INVALID)

    if sv_defs.clientList_Team[client_index] == 0:
        server.Notify(client_index, 'Custom vote is forbidden for specs')
        return CustomVote(vote_result=CustomVote.VOTE_INVALID_NO_WARNING)

    affected_index = sv_utils.getIndexFromFullName(str(vote_info))
    if affected_index is None:
        server.Notify(client_index, '%s is not found' % vote_info)
        return CustomVote(vote_result=CustomVote.VOTE_INVALID_NO_WARNING)
    else:
        return CustomVote(
            'Unban siege for %s' % vote_info,
            vote_info,
            CustomVote.UN_BAN,
            0.60,
            int(affected_index),
            CustomVote.ACCEPT_IS_NEEDED,
            CustomVote.ALL_TEAMS_CAN_VOTE,
            CustomVote.VOTE_VALID)


def outcome(vote_info: str):
    # Block draw/concede votes for 5 min.
    # No end-game votes
    return CustomVote(
        'Block draws for 5 min',
        vote_info,
        CustomVote.OUTCOME,
        0.50,
        CustomVote.UID_IS_NOT_NEEDED,
        CustomVote.ACCEPT_IS_NOT_NEEDED,
        CustomVote.ALL_TEAMS_CAN_VOTE,
        CustomVote.VOTE_VALID)


def enable_self_buffs(client_index: int, vote_info: str):
    if not bool(core.CvarGetValue('sv_allowPowerupRequests')):
        return CustomVote(
            'Enable self buffs',
            vote_info,
            CustomVote.ENABLE_SELF_BUFFS,
            0.50,
            CustomVote.UID_IS_NOT_NEEDED,
            CustomVote.ACCEPT_IS_NOT_NEEDED,
            CustomVote.ALL_TEAMS_CAN_VOTE,
            CustomVote.VOTE_VALID)

    server.Notify(client_index, 'Self buffs are already ON')
    return CustomVote(vote_result=CustomVote.VOTE_INVALID_NO_WARNING)


def disable_self_buffs(client_index: int, vote_info: str):
    if bool(core.CvarGetValue('sv_allowPowerupRequests')):
        return CustomVote(
            'Disable self buffs',
            vote_info,
            CustomVote.DISABLE_SELF_BUFFS,
            0.50,
            CustomVote.UID_IS_NOT_NEEDED,
            CustomVote.ACCEPT_IS_NOT_NEEDED,
            CustomVote.ALL_TEAMS_CAN_VOTE,
            CustomVote.VOTE_VALID)

    server.Notify(client_index, 'Self buffs are already OFF')
    return CustomVote(vote_result=CustomVote.VOTE_INVALID_NO_WARNING)


def enable_buff_pools(client_index: int, vote_info: str):
    if server.GetGameInfo(GAME_STATE) not in {1, 2}:
        server.Notify(client_index, '^yThis ^yvote is ^900disabled ^ywhen ^ythe ^ygame ^yis ^yin ^yprogress.')
        return CustomVote(vote_result=CustomVote.VOTE_INVALID_NO_WARNING)

    if not bool(core.CvarGetValue('sv_allowFillBuffPool')):
        return CustomVote(
            'Enable buff pools',
            vote_info,
            CustomVote.ENABLE_BUFF_POOLS,
            0.50,
            CustomVote.UID_IS_NOT_NEEDED,
            CustomVote.ACCEPT_IS_NOT_NEEDED,
            CustomVote.ALL_TEAMS_CAN_VOTE,
            CustomVote.VOTE_VALID)

    server.Notify(client_index, '^yBuff ^ypools ^yare ^yalready ^yenabled!')
    return CustomVote(vote_result=CustomVote.VOTE_INVALID_NO_WARNING)


def disable_buff_pools(client_index: int, vote_info: str):
    if server.GetGameInfo(GAME_STATE) not in {1, 2}:
        server.Notify(client_index, '^yThis ^yvote is ^900disabled ^ywhen ^ythe ^ygame ^yis ^yin ^yprogress.')
        return CustomVote(vote_result=CustomVote.VOTE_INVALID_NO_WARNING)

    if bool(core.CvarGetValue('sv_allowFillBuffPool')):
        return CustomVote(
            'Disable buff pools',
            vote_info,
            CustomVote.DISABLE_BUFF_POOLS,
            0.50,
            CustomVote.UID_IS_NOT_NEEDED,
            CustomVote.ACCEPT_IS_NOT_NEEDED,
            CustomVote.ALL_TEAMS_CAN_VOTE,
            CustomVote.VOTE_VALID)

    server.Notify(client_index, '^yBuff ^ypools ^yare ^yalready ^ydisabled!')
    return CustomVote(vote_result=CustomVote.VOTE_INVALID_NO_WARNING)


# def enable_bots(client_index: int, vote_info: str):
#     if int(core.CvarGetValue('sv_botEnable')) == 0:
#         return CustomVote(
#             'Enable bots',
#             vote_info,
#             CustomVote.ENABLE_BOTS,
#             0.50,
#             CustomVote.UID_IS_NOT_NEEDED,
#             CustomVote.ACCEPT_IS_NOT_NEEDED,
#             CustomVote.ALL_TEAMS_CAN_VOTE,
#             CustomVote.VOTE_VALID)
#
#     server.Notify(client_index, 'Bots are already ON')
#     return CustomVote(vote_result=CustomVote.VOTE_INVALID_NO_WARNING)


# def disable_bots(client_index: int, vote_info: str):
#     if core.CvarGetValue('sv_botEnable') > 0:
#         return CustomVote(
#             'Disable bots',
#             vote_info,
#             CustomVote.DISABLE_BOTS,
#             0.50,
#             CustomVote.UID_IS_NOT_NEEDED,
#             CustomVote.ACCEPT_IS_NOT_NEEDED,
#             CustomVote.ALL_TEAMS_CAN_VOTE,
#             CustomVote.VOTE_VALID)
#
#     server.Notify(client_index, 'Bots are already OFF')
#     return CustomVote(vote_result=CustomVote.VOTE_INVALID_NO_WARNING)
