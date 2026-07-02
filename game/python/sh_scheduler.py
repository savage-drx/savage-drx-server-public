# ---------------------------------------------------------------------------
#           Name: sh_scheduler.py
#    Description: possibility to schedule events on client/server
# ---------------------------------------------------------------------------


import core
import sched
import time
from typing import Optional

import sh_executor
import sh_logger as log
from sv_context import SharedContext
import sv_requests
import json


class _Context:
    SCHEDULER = Optional[sched.scheduler]
    PUBLISH_CLIENT_ACTIVITY = python_config.getboolean('Python_General', 'PUBLISH_CLIENT_ACTIVITY')
    PUBLISH_CLIENT_ACTIVITY_INTERVAL_SECONDS = python_config.getint('Python_General',
                                                                    'PUBLISH_CLIENT_ACTIVITY_INTERVAL_SECONDS')
    URL_SEND_CLIENT_ACTIVITY = core.CvarGetString('sv_authserver') + "audit/connected-clients"

    STATS_DUELS_PUBLISHER_ENABLED = python_config.getboolean('Python_Stats', 'STATS_DUELS_PUBLISHER_ENABLED')
    PUBLISH_STATS_DUELS_INTERVAL_SECONDS = python_config.getint('Python_Stats', 'PUBLISH_STATS_DUELS_INTERVAL_SECONDS')
    URL_SEND_DUEL_STATS = core.CvarGetString('sv_authserver') + "history/duels"

    @staticmethod
    def init():
        log.info("Initializing Scheduler...")
        _Context.SCHEDULER = sched.scheduler(time.time, time.sleep)
        sh_executor.submit_task(_Context.start)

    @staticmethod
    def stop():
        pass

    @staticmethod
    def start():
        send_client_activity()
        send_duel_stats()
        _Context.SCHEDULER.run()


def send_client_activity():
    if _Context.PUBLISH_CLIENT_ACTIVITY:
        connected_clients_list = SharedContext.get('connected_clients')
        if connected_clients_list and len(connected_clients_list) > 0:
            try:
                body = '{"connected_clients": %s}' % json.dumps(connected_clients_list)
                sv_requests.post_request(_Context.URL_SEND_CLIENT_ACTIVITY, body)
                log.info(f'Sent client activities: {len(connected_clients_list)}')
                connected_clients_list.clear()
            except:
                log.info(f'Failed to send client activity (len: {len(connected_clients_list)})')

        _Context.SCHEDULER.enter(_Context.PUBLISH_CLIENT_ACTIVITY_INTERVAL_SECONDS, 1, send_client_activity)


def send_duel_stats():
    if _Context.STATS_DUELS_PUBLISHER_ENABLED:
        duel_stats = SharedContext.get('duel_stats')
        body = None
        if duel_stats and len(duel_stats) > 0:
            try:
                body = '{"duels": %s}' % json.dumps(duel_stats)
                sv_requests.post_request(_Context.URL_SEND_DUEL_STATS, body)
                log.info(f'Sent duel results: {len(duel_stats)}')
                duel_stats.clear()
            except:
                log.info(f'Failed to send duel stats: {body})')
                duel_stats.clear()
        else:
            log.info('duel stats: nothing to send')

    _Context.SCHEDULER.enter(_Context.PUBLISH_STATS_DUELS_INTERVAL_SECONDS, 1, send_duel_stats)
