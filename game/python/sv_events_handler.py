# ---------------------------------------------------------------------------
#           Name: sv_events_handler.py
#    Description: respawn handlers
# ---------------------------------------------------------------------------


import core
import server
import sv_defs
import sv_votes_processor
import sh_logger as log
import sv_utils
import sv_discord
import sh_custom_utils


def check_banned_units(client_index):
    # Don't log bot's actions
    if not sv_defs.clientList_Bot[client_index]:
        uid = server.GetClientInfo(client_index, INFO_UID)
        log.info(f"Spawned: {sv_defs.objectList_Name[client_index]}, "
                 f"name: {server.GetClientInfo(client_index, INFO_NAME)}, client_index: {client_index}, uid: {uid}")
        if uid in sv_votes_processor.VoteSettings.banned_client_uids:
            warn_and_change_unit(client_index)


def warn_and_change_unit(client_index):
    object_name = sv_defs.objectList_Name[client_index]
    object_team = str(sv_defs.objectList_Team[client_index])
    if object_name in EventsHandlerSettings.HUMAN_SIEGE:
        server.Notify(client_index, '^ySiege ^yis ^900banned ^yfor ^yyou! ^yTake ^yanother ^yunit.')
        server.GameScript(client_index, f'!changeunit target {EventsHandlerSettings.HUMAN_NOMAD}')
        core.CommandExec(
            'giveresource %s %s %s' % ('gold', EventsHandlerSettings.HUMAN_SIEGE[object_name], object_team))
    if object_name in EventsHandlerSettings.BEAST_SIEGE:
        server.Notify(client_index, '^ySiege ^yis ^900banned ^yfor ^yyou! ^yTake ^yanother ^yunit.')
        server.GameScript(client_index, f'!changeunit target {EventsHandlerSettings.BEAST_SCAVENGER}')
        core.CommandExec(f'giveresource gold {EventsHandlerSettings.BEAST_SIEGE[object_name]} {object_team}')


def process_death_from_siege(client_index, killer_index):
    killer_object_name = sv_defs.objectList_Name[killer_index]
    dead_object_name = sv_defs.objectList_Name[client_index]
    if killer_object_name in EventsHandlerSettings.PAYBACK_SIEGE and dead_object_name in \
            EventsHandlerSettings.PAYBACK_UNITS:
        log.warn("Player %s was killed by %s" % (server.GetClientInfo(client_index, INFO_NAME), killer_object_name))
        core.CommandExec(f'givemoney {EventsHandlerSettings.PAYBACK_UNITS[dead_object_name]} {client_index}')
        server.Notify(client_index, f'^yYou ^ywere ^ykilled ^yby ^ysiege. ^gRefund: ^900'
                            f'{EventsHandlerSettings.PAYBACK_UNITS[dead_object_name]}')
        log.info(f"Player {server.GetClientInfo(client_index, INFO_NAME)} got refund: "
                 f"{EventsHandlerSettings.PAYBACK_UNITS[dead_object_name]}")


def send_frag_to_discord(client_index, killer_index):
    killer = server.GetClientInfo(killer_index, INFO_NAME)
    dead = server.GetClientInfo(client_index, INFO_NAME)
    if server.GetGameInfo(GAME_STATE) == 3:
        msg = f"`{sv_discord.get_current_utc_timestamp()}` *{dead} was killed by {killer}*"
        sv_discord.send_message_to_discord(msg)


def apply_low_online_settings(online_state: sv_utils.OnlineState, max_active_players: int):
    log.info(f"Online is: {online_state.active_players}/{online_state.online}. Applying low online settings...")
    server.Broadcast(f'^yApplying ^gsimple ^ysettings ^y(online ^yis ^g{online_state.online}^y/^900{max_active_players}^y)')
    core.CvarSetValue('sv_commSpawnSiege', 1)
    core.CvarSetValue('sv_allowWorldVoteOnLowOnline', 1)
    core.CvarSetValue('sv_respawnTimeEnter', 0)
    core.CvarSetValue('sv_respawnTimeResign', 0)
    core.CvarSetValue('sv_reconnectRespawnDelay', 20000)
    # core.CvarSetValue('sv_allowEnemySameIP', 1)


def apply_high_online_settings(online_state: sv_utils.OnlineState, max_active_players: int):
    log.info(f"Online is: {online_state.active_players}/{online_state.online}. Applying high online settings...")
    server.Broadcast(f'^yApplying ^gstrict ^ysettings ^y(^yonline ^yis ^g{online_state.online}^y/^900{max_active_players}^y)')
    core.CvarSetValue('sv_allowWorldVoteOnLowOnline', 0)
    core.CvarSetValue('sv_commSpawnSiege', 0)
    # core.CvarSetValue('sv_respawnTimeEnter', 5000)
    core.CvarSetValue('sv_respawnTimeResign', 5000)
    core.CvarSetValue('sv_reconnectRespawnDelay', 30000)
    # core.CvarSetValue('sv_allowEnemySameIP', 0)


# def trigger_bot_settings():
#     if bool(int(core.CvarGetValue("sv_triggerBotEnable"))):
#         online_state = sv_utils.OnlineState()
#         if len(online_state.teams) > 3:
#             log.info("Triggering bot settings sv_botEnable: 0")
#             core.CvarSetValue('sv_botEnable', 0)
#         else:
#             log.info("Triggering bot settings sv_botEnable: 2")
#             core.CvarSetValue('sv_botEnable', 2)
#     else:
#         log.info("Triggering bot settings sv_botEnable: 0")
#         core.CvarSetValue('sv_botEnable', 0)


def on_spawn(client_index, spawned_clients):
    object_name = sv_defs.objectList_Name[client_index]
    if object_name == EventsHandlerSettings.BEAST_BEHEMOTH:
        return
        # temporary rollback until the client is fixed
        # spawned_clients[client_index] = sv_utils.get_game_time_in_seconds()
        # server.Notify(client_index, "^388You've ^388spawned ^388with ^388a ^388behemoth"
        #                     " ^900without ^900it's ^900weapon\n")
        # server.Notify(client_index, "^388Behemoth ^388obtains ^388uprooted ^388tree ^388in ^900%s ^388seconds!\n"
        #               % EventsHandlerSettings.ON_SPAWN_BEHEMOTH_UPROOTED_TREE_COOLDOWN_SEC)

    if object_name == EventsHandlerSettings.HERO_OPHELIA:
        spawned_clients[client_index] = sv_utils.get_game_time_in_seconds()
        server.Notify(client_index, "^388You've ^388spawned ^388as ^388an ^388Ophelia"
                            " ^900without ^900her ^900mana ^900crystal\n")
        server.Notify(client_index, "^388Ophelia ^388obtains ^388mana ^388crystal ^388in ^900%s ^388seconds!\n"
                      % EventsHandlerSettings.ON_SPAWN_HERO_OPHELIA_CRYSTAL_COOLDOWN_SEC)


def return_initial_items(spawned_clients):
    try:
        # return if spawned_clients is empty
        if not len(spawned_clients):
            return

        current_game_time_seconds = sv_utils.get_game_time_in_seconds()

        client_indices_to_remove = list()
        for client_index, time in spawned_clients.items():

            if server.GetClientInfo(client_index, INFO_ACTIVE) and not sv_defs.clientList_Bot[client_index]:
                object_name = sv_defs.objectList_Name[client_index]

                if object_name == EventsHandlerSettings.BEAST_BEHEMOTH \
                        and server.GetClientInfo(client_index, INFO_STATUS) == sv_utils.PlayerStatus.STATUS_PLAYER:
                    return
                    # temporary rollback until the client is fixed
                    # if current_game_time_seconds >= time + \
                    #         EventsHandlerSettings.ON_SPAWN_BEHEMOTH_UPROOTED_TREE_COOLDOWN_SEC:
                    #     server.GameScript(client_index, '!give target {} {} {}'
                    #                       .format(EventsHandlerSettings.BEAST_BEHEMOTH_MELEE, 0, 0))
                    #     server.Notify(client_index, "^gYou've ^gbeen ^ggranted ^gwith ^gan ^900uprooted ^900tree!\n")
                    #     client_indices_to_remove.append(client_index)

                if object_name == EventsHandlerSettings.HERO_OPHELIA \
                        and server.GetClientInfo(client_index, INFO_STATUS) == sv_utils.PlayerStatus.STATUS_PLAYER:
                    if current_game_time_seconds >= time + \
                            EventsHandlerSettings.ON_SPAWN_HERO_OPHELIA_CRYSTAL_COOLDOWN_SEC:
                        server.GameScript(client_index, f'!give target {EventsHandlerSettings.HERO_OPHELIA_CRYSTAL} 0 3')
                        server.Notify(client_index, "^gYou've ^gbeen ^ggranted ^gwith ^ga ^900mana ^900crystal!\n")
                        client_indices_to_remove.append(client_index)

        # cleaning from clients that obtained their items
        for x in client_indices_to_remove:
            spawned_clients.pop(x)

    except:
        sh_custom_utils.get_and_log_exception_info()


class EventsHandlerSettings:
    HUMAN_NOMAD = 'human_nomad'
    BEAST_SCAVENGER = 'beast_scavenger'
    HUMAN_SIEGE = {
        'human_ballista': '4000',
        'human_catapult': '7500'
    }
    BEAST_SIEGE = {
        'beast_summoner': '5500',
        'beast_behemoth': '7500'
    }
    PAYBACK_SIEGE = {
        'human_ballista',
        'beast_summoner'
    }
    PAYBACK_UNITS = {
        'human_savage': '2500',
        'human_legionnaire': '4000',
        'human_medic': '1500',
        'beast_stalker': '2500',
        'beast_predator': '4500',
        'beast_medic': '1500'
    }
    BEAST_BEHEMOTH = 'beast_behemoth'
    HERO_OPHELIA = 'hero_ophelia'
    BEAST_BEHEMOTH_MELEE = 'beast_behemoth_melee'
    HERO_OPHELIA_CRYSTAL = 'hero_ophelia_crystal'
    ON_SPAWN_BEHEMOTH_UPROOTED_TREE_COOLDOWN_SEC = 5
    ON_SPAWN_HERO_OPHELIA_CRYSTAL_COOLDOWN_SEC = 10
