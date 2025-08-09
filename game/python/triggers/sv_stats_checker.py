# ---------------------------------------------------------------------------------
#           Name: sv_stats_checker.py
#    Description: Scheduler that triggers updating of the stats info for publishing
# ---------------------------------------------------------------------------------


# Savage API
import server

# External modules
import sh_custom_utils
import sv_stats_publisher


class Stats:
    TIME_MINUTES = 60
    # TIME_DELTA is applied to escape execution of the different scripts in the same time
    # should be useful for the server-fps
    TIME_DELTA_SECONDS = 5
    STATS_UPDATER_PLAYER_STATE_INTERVAL_SECONDS = \
        python_config.getint('Python_Stats', 'STATS_UPDATER_PLAYER_STATE_INTERVAL_MINUTES') \
        * TIME_MINUTES + TIME_DELTA_SECONDS

    def __init__(self):
        self.checked_once = False
        self.latest_check_game = 0
        self.latest_check_players = 0
        self.current_game_time_seconds = 0

    def check_players(self):
        try:
            if self.current_game_time_seconds >= self.latest_check_players \
                    + Stats.STATS_UPDATER_PLAYER_STATE_INTERVAL_SECONDS:
                if server.GetGameInfo(GAME_STATE) == 3:
                    sv_stats_publisher.update_players_stats()
                    self.latest_check_players = self.current_game_time_seconds
        except:
            sh_custom_utils.get_and_log_exception_info()


is_end_game_publisher_enabled = python_config.getboolean('Python_Stats', 'STATS_ENDGAME_PUBLISHER_ENABLED')
stats = Stats()


# Is called during every server frame
def check():
    if is_end_game_publisher_enabled:
        stats.check_players()
    return 0


# Is called by Silverback when check() returns 1
# Is not used in the current script
def execute():
    pass
