# ---------------------------------------------------------------------------
#           Name: sv_announcement.py
#    Description: Announcements for all registered clients
# ---------------------------------------------------------------------------


# Savage API
import core
import server

# External modules
import sh_custom_utils
import sv_defs
import time

type_list = ["CLIENT", "WORKER", "NPC", "MINE", "BASE", "OUTPOST", "BUILDING", "OTHER"]

NOTIFY_WARMUP_SEC = 60 * 1000
NOTIFY_NORMAL_MIN = 15 * 1000 * 60

warmup_last_notify_time = 0
normal_last_notify_time = 0
run_once_flag = True

ANNOUNCEMENT_WARMUP = '^yTake ^ypart ^yto ^ymake ^ythis ^yserver ^ybetter: ^ggoo.gl/PXCnqR'
ANNOUNCEMENT_GAME = '^yTake ^ypart ^yto ^ymake ^ythis ^yserver ^ybetter: ^ggoo.gl/PXCnqR'


# Is called during every server frame
def check():
    try:
        # Run-once
        run_once()

        global warmup_last_notify_time
        global normal_last_notify_time
        current_time_millis = int(round(time.time() * 1000))
        
        if current_time_millis > warmup_last_notify_time + NOTIFY_WARMUP_SEC:
            if server.GetGameInfo(GAME_STATE) == 1 or server.GetGameInfo(GAME_STATE) == 2:
                warmup_last_notify_time = current_time_millis
                iterate_over_clients(ANNOUNCEMENT_WARMUP)
        
        if current_time_millis > normal_last_notify_time + NOTIFY_NORMAL_MIN:
            if server.GetGameInfo(GAME_STATE) == 3:
                normal_last_notify_time = current_time_millis
                iterate_over_clients(ANNOUNCEMENT_GAME)
    except:
        sh_custom_utils.get_and_log_exception_info()
    return 0


def run_once():
    global run_once_flag
    if run_once_flag:
        run_once_flag = False
        global normal_last_notify_time
        global warmup_last_notify_time
        current_time_millis = int(round(time.time() * 1000))
        normal_last_notify_time = current_time_millis
        warmup_last_notify_time = current_time_millis


def iterate_over_clients(message):
    core.ConsolePrint("Announcement: %s" % message)
    for guid in range(0, sv_defs.objectList_Last):
        if (sv_defs.objectList_Active[guid] and sv_defs.objectList_Team[guid] > 0) or server.GetGameInfo(GAME_STATE) == 3:
            object_type = str(type_list[sv_defs.objectList_Type[guid]])
            if object_type == "CLIENT":
                server.Notify(guid, message)


# Is called when check() returns 1
# Is not used in the current script
def execute():
    pass

