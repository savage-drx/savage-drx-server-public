# ---------------------------------------------------------------------------
#           Name: sv_afk_checker.py
#    Description: Moves AFKs during the game
# ---------------------------------------------------------------------------


# Savage API
import server

# External modules
import sh_custom_utils
import sv_utils
import sh_logger as log


class Afk:
    TIME_MINUTES = 60
    SINGLE_CHECKOUT_SECONDS = python_config.getint('Python_Afk', 'AFK_SINGLE_CHECKOUT_SECONDS')
    INTERVAL_CHECKOUT_SECONDS = python_config.getint('Python_Afk', 'AFK_INTERVAL_CHECKOUT_MINUTES') * TIME_MINUTES
    INITIAL_PRE_CHECK_SECONDS = python_config.getint('Python_Afk', 'AFK_INITIAL_PRE_CHECK_SECONDS')

    def __init__(self):
        self.checked_clients = {}
        self.latest_check_with_interval = 0
        self.checked_once = False
        self.pre_checked = False
        self.online_state = None
        self.current_game_time_seconds = 0

    def check(self):
        try:
            self.current_game_time_seconds = sv_utils.get_game_time_in_seconds()

            if not self.checked_once:
                self.__pre_check()

                if server.GetGameInfo(GAME_STATE) == 3 \
                        and self.current_game_time_seconds >= Afk.SINGLE_CHECKOUT_SECONDS:
                    server.Broadcast("^yChecking ^yfor ^900AFKs ^y(%s ^yseconds ^yfrom ^ythe ^ystart)" %
                                     Afk.SINGLE_CHECKOUT_SECONDS)
                    log.info("AFK: Started checking (%s seconds from the start). Game time: %s" %
                             (Afk.SINGLE_CHECKOUT_SECONDS,
                              sh_custom_utils.time_formatter(self.current_game_time_seconds)))

                    self.checked_once = True
                    self.__compare_client_states()

                    log.info("AFK: Finished checking")

            else:
                if self.current_game_time_seconds >= self.latest_check_with_interval + Afk.INTERVAL_CHECKOUT_SECONDS:
                    if server.GetGameInfo(GAME_STATE) == 3:
                        server.Broadcast("^yChecking ^yfor ^900AFKs ^y(every ^y%s ^yminutes)" %
                                         int(Afk.INTERVAL_CHECKOUT_SECONDS / Afk.TIME_MINUTES))
                        log.info("AFK: Started checking (every %s minutes). Game time: %s" %
                                 (int(Afk.INTERVAL_CHECKOUT_SECONDS / Afk.TIME_MINUTES),
                                  sh_custom_utils.time_formatter(self.current_game_time_seconds)))

                        self.latest_check_with_interval = self.current_game_time_seconds
                        self.__compare_client_states()

                        log.info("AFK: Finished checking")
        except:
            sh_custom_utils.get_and_log_exception_info()

    def __pre_check(self):
        if not self.pre_checked:
            if server.GetGameInfo(GAME_STATE) == 3 and self.current_game_time_seconds >= Afk.INITIAL_PRE_CHECK_SECONDS:
                log.info("AFK: Initial pre-check (%s seconds from the start)" % Afk.INITIAL_PRE_CHECK_SECONDS)
                self.pre_checked = True
                self.__update_online_state()
                for client_index in self.online_state.active_indices_without_commanders:
                    self.checked_clients[client_index] = sv_utils.ClientState(client_index)

    def __update_online_state(self):
        log.info("AFK: Updating online state")
        self.online_state = sv_utils.OnlineState()

    def __compare_client_states(self):
        self.__update_online_state()
        for client_index in self.online_state.active_indices_without_commanders:
            client_state = sv_utils.ClientState(client_index)
            # Add client if absent
            if client_index not in self.checked_clients:
                self.checked_clients[client_index] = client_state
            # Check and move client in case of AFK
            elif client_state.is_afk(self.checked_clients[client_index]):
                client_state.switch_to_specs()
                self.checked_clients.pop(client_index)
            # Update latest client state
            else:
                self.checked_clients[client_index] = client_state


is_afk_enabled = python_config.getboolean('Python_Afk', 'AFK_IS_ENABLED')
afk = Afk()


# Is called during every server frame
def check():
    if is_afk_enabled:
        afk.check()
    return 0


# Is called by Silverback when check() returns 1
# Is not used in the current script
def execute():
    pass
