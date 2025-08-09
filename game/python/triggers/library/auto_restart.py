# ---------------------------------------------------------------------------
#           Name: auto_restart.py
#    Description: Server Trigger for automatic Server Restarts, every hour it idles.
# ---------------------------------------------------------------------------

# Savage API
import core
import server

# External modules
import sh_executor
import sv_discord
from sh_scheduler import _Context


# Create IS_RESTART_TRIGGER_ENABLED in the config.ini
is_trigger_enabled = python_config.getboolean('Python_General', 'IS_RESTART_TRIGGER_ENABLED')


# -------------------------------
def check():
    if is_trigger_enabled:
        # Check that server is idle and the game time is over 1h.
        if server.GetGameInfo(GAME_STATE) == 0 and server.GetGameInfo(GAME_TIME) >= 3600000:
            return 1

    return 0


# -------------------------------
def execute():
    # Restart the server

    # Stop scheduled events
    if python_config.getboolean('Python_General', 'SCHEDULER_IS_ENABLED'):
        _Context.stop()

    # Closing running threads
    sh_executor.stop()
    if sv_discord.DiscordSettings.DISCORD_IS_ENABLED:
        sv_discord.stop()

    # Fire close event here!
    core.CommandExec('quit')
    pass
