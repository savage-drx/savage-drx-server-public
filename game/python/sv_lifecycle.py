# ---------------------------------------------------------------------------
#           Name: sv_lifecycle.py
#    Description: server states
# ---------------------------------------------------------------------------

import sv_triggers
import sh_logger as log
import sv_votes_processor
import sh_executor
import sh_initializer
import sv_discord
import sv_maps
import sv_events
import sv_events_handler
import sv_warmup
import sv_stats_publisher
import sv_bans
import gc
import sv_permissions


class LifeCycleContext:
    STATS_ENDGAME_PUBLISHER_ENABLED = python_config.getboolean('Python_Stats', 'STATS_ENDGAME_PUBLISHER_ENABLED')


def when_game_is_in_setup():
    sh_initializer.init_python_config()
    sv_votes_processor.reset_custom_vote_settings()
    # sv_events_handler.trigger_bot_settings()
    sv_warmup.start()
    if sv_permissions.PermissionsContext.GAME_PRIVILEGES_ARE_ENABLED:
        sh_executor.submit_task(sv_permissions.PermissionsContext.update_privileges)


def when_game_has_started():
    sh_initializer.init_python_config()
    if sv_discord.DiscordSettings.DISCORD_IS_ENABLED:
        sh_executor.submit_task(sv_discord.send_online_to_discord, False, 12)
    sv_votes_processor.check_custom_vote_settings_on_start()
    # sv_events_handler.trigger_bot_settings()
    sv_events.EventsContext.spawned_players = dict()
    sv_events.EventsContext.is_online_low = False
    sv_events.EventsContext.is_online_high = False
    sv_warmup.stop()


def when_game_has_ended():
    if sv_discord.DiscordSettings.DISCORD_IS_ENABLED:
        sh_executor.submit_task(sv_discord.send_end_of_game_to_discord)
    sv_warmup.stop()
    if LifeCycleContext.STATS_ENDGAME_PUBLISHER_ENABLED:
        sv_stats_publisher.publish_end_game_stats()


def when_game_has_finished():
    sv_votes_processor.reset_custom_vote_settings()
    # sv_events_handler.trigger_bot_settings()
    if sv_discord.DiscordSettings.DISCORD_IS_ENABLED:
        sh_executor.submit_task(sv_discord.send_nextmap_to_discord, 8)
    sv_warmup.stop()
    gc.collect()


class StatusDispatcher:
    EMPTY = 0
    SETUP = 1
    WARMUP = 2
    IN_PROGRESS = 3
    END = 4
    NEXT_MAP = 5
    VOTED_MAP = 6
    RESTART_MAP = 7

    ON_STATUS = {
        EMPTY: (lambda: StatusDispatcher._on_empty()),
        SETUP: (lambda: StatusDispatcher._on_setup()),
        WARMUP: (lambda: StatusDispatcher._on_warmup()),
        IN_PROGRESS: (lambda: StatusDispatcher._on_start()),
        END: (lambda: StatusDispatcher._on_end()),
        NEXT_MAP: (lambda: StatusDispatcher._on_loading_nextmap()),
        VOTED_MAP: (lambda: StatusDispatcher._on_loading_voted_map()),
        RESTART_MAP: (lambda: StatusDispatcher._on_restarting_map())
    }

    # state 0
    @classmethod
    def _on_empty(cls):
        cls._on_state_change()
        # Server is waiting for clients to connect
        sh_initializer.init_python_config()
        log.info("Game state: Empty")
        if sv_permissions.PermissionsContext.GAME_PRIVILEGES_ARE_ENABLED:
            sh_executor.submit_task(sv_permissions.PermissionsContext.init_credentials)

    # state 1
    @classmethod
    def _on_setup(cls):
        cls._on_state_change()
        # Setting a game up in the lobby
        log.info("Game state: Setup")
        when_game_is_in_setup()

    # state 2
    @classmethod
    def _on_warmup(cls):
        cls._on_state_change()
        # Warming up
        log.info("Game state: Warmup")

    # state 3
    @classmethod
    def _on_start(cls):
        cls._on_state_change()
        # Normal play mode
        log.info("Game state: Normal")
        when_game_has_started()

    # state 4
    @classmethod
    def _on_end(cls):
        cls._on_state_change()
        # Game has ended
        log.info("Game state: Ended")
        when_game_has_ended()

    # states: 5, 6, 7
    @classmethod
    def _on_change_world(cls):
        cls._on_state_change()
        when_game_has_finished()

    # state 5
    @classmethod
    def _on_loading_nextmap(cls):
        # About to load the next map
        log.info("Game state: Loading Next Map")
        sv_maps.nextmap()
        cls._on_change_world()

    # state 6
    @classmethod
    def _on_loading_voted_map(cls):
        # About to load the voted map
        log.info("Game state: Loading Voted Map")
        cls._on_change_world()

    # state 7
    @classmethod
    def _on_restarting_map(cls):
        # Match is restarting (same map)
        log.info("Game state: Restarting Map")
        cls._on_change_world()

    @classmethod
    def _on_state_change(cls):
        # Reload Trigger (resets trigger states)
        sv_triggers.re_load()

        # Reload banned ids
        sv_bans.init_banned()
