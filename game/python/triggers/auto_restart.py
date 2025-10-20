# ---------------------------------------------------------------------------
#           Name: auto_restart.py
#    Description: Server Trigger for automatic Server Restarts, every hour it idles.
# ---------------------------------------------------------------------------

# Savage API
import core
import server


class _RestartContext:
    IS_RESTART_TRIGGER_ENABLED = python_config.getboolean('Python_General', 'IS_RESTART_TRIGGER_ENABLED')


# -------------------------------
def check():
    if _RestartContext.IS_RESTART_TRIGGER_ENABLED:
        # Check that server is idle and the game time is over 1h.
        if server.GetGameInfo(GAME_STATE) == 0 and server.GetGameInfo(GAME_TIME) >= 3600000:
            return 1
    return 0


# -------------------------------
def execute():
    # Fire close event here!
    core.CommandExec('quit')
