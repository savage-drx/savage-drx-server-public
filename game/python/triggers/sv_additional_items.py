# ---------------------------------------------------------------------------
#           Name: sv_additional_items.py
#    Description: Adds or removes additional items for players
# ---------------------------------------------------------------------------


# Savage API
import core
import server

# External modules
import sh_custom_utils

run_once_flag = True


# Is called when check() returns 1
# Is not used in the current script
def execute():
    pass


# Is called during every server frame
def check():
    try:
        # Run-once
        run_once()
    except:
        sh_custom_utils.get_and_log_exception_info()
    return 0


def run_once():
    global run_once_flag
    if run_once_flag and server.GetGameInfo(GAME_STATE) == 3:
        run_once_flag = False
        if core.CvarGetString('sv_map_gametype') == "INSTAGIB":
            return

        is_april_fools_enabled = int(core.CvarGetValue('sv_enableAprilFools'))
        if is_april_fools_enabled:
            core.CommandExec('objedit human_nomad; objSet forceInventory1 human_boomerang')
            core.CommandExec('objedit beast_scavenger; objSet forceInventory1 beast_skullstack')
        else:
            core.CommandExec('objedit human_nomad; objSet forceInventory1 \"\"')
            core.CommandExec('objedit beast_scavenger; objSet forceInventory1 \"\"')
    elif run_once_flag and server.GetGameInfo(GAME_STATE) == 1:
        run_once_flag = False
        if core.CvarGetString('sv_map_gametype') == "INSTAGIB":
            return

        core.CommandExec('objedit human_nomad; objSet forceInventory1 \"\"')
        core.CommandExec('objedit beast_scavenger; objSet forceInventory1 \"\"')
        core.CvarSetValue('sv_enableAprilFools', 0)
