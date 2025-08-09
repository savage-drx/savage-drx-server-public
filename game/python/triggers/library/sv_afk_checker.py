# ---------------------------------------------------------------------------
#           Name: sv_afk_checker.py
#    Description: Moves AFKs at start of the game
# ---------------------------------------------------------------------------


# Savage API
import core
import server

# External modules
import sh_custom_utils
import sv_defs

type_list = ["CLIENT", "WORKER", "NPC", "MINE", "BASE", "OUTPOST", "BUILDING", "OTHER"]

AFK_CHECK_TIME_SEC = 60 * 1000
run_once_flag = True


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
    if run_once_flag and server.GetGameInfo(GAME_STATE) == 3 and sv_defs.gameTime >= AFK_CHECK_TIME_SEC:
        run_once_flag = False
        iterate_over_clients()


def iterate_over_clients():
    core.ConsolePrint("[INFO] Checking for afks\n")
    for guid in range(0, sv_defs.objectList_Last):
        # Selects all not active clients and not spectators
        if sv_defs.objectList_Active[guid] == 0 and sv_defs.objectList_Team[guid] > 0:
            object_type = str(type_list[sv_defs.objectList_Type[guid]])
            if object_type == "CLIENT":
                exp = int(server.GetClientInfo(guid, STAT_EXPERIENCE))
                if exp == 0:
                    switch_client(guid)


def switch_client(guid):
    core.CommandExec("switchteam 0 %s" % guid)
    object_name = str(server.GetClientInfo(guid, INFO_NAME))
    core.ConsolePrint("[INFO] %s is AFK\n" % object_name)
    server.Broadcast("^g%s ^yhas ^ybeen ^ymoved ^yto ^yspectators, ^ybecause ^yof ^ybeing ^yAFK" % object_name)


# Is called when check() returns 1
# Is not used in the current script
def execute():
    pass
