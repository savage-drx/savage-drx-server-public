# ---------------------------------------------------------------------------
#           Name: sh_scheduler.py
#    Description: possibility to schedule events on client/server
# ---------------------------------------------------------------------------


import json
import sched
import time
from typing import Optional

import core

import sh_executor
import sh_logger as log
import sv_requests
from sv_context import SharedContext


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
        schedule_client_activity()
        schedule_duel_stats()
        _Context.SCHEDULER.run()


def schedule_client_activity():
    sh_executor.submit_task(send_client_activity)
    _Context.SCHEDULER.enter(_Context.PUBLISH_CLIENT_ACTIVITY_INTERVAL_SECONDS, 1, schedule_client_activity)


def schedule_duel_stats():
    sh_executor.submit_task(send_duel_stats)
    _Context.SCHEDULER.enter(_Context.PUBLISH_STATS_DUELS_INTERVAL_SECONDS, 1, schedule_duel_stats)


def send_client_activity():
    try:
        if not _Context.PUBLISH_CLIENT_ACTIVITY:
            return

        connected_clients = SharedContext.get('connected_clients')

        if connected_clients:
            body = '{"connected_clients": %s}' % json.dumps(connected_clients)
            sv_requests.post_request(_Context.URL_SEND_CLIENT_ACTIVITY, body)
            log.info(f'Sent client activities: {len(connected_clients)}')
            connected_clients.clear()
        else:
            # todo remove debug logs
            log.info('Client activity: nothing to send')

    except Exception as e:
        log.info(f'Failed to send client activity: {e}')


def send_duel_stats():
    try:
        if not _Context.STATS_DUELS_PUBLISHER_ENABLED:
            return

        duel_stats = SharedContext.get('duel_stats')

        if duel_stats:
            body = '{"duels": %s}' % json.dumps(duel_stats)
            sv_requests.post_request(_Context.URL_SEND_DUEL_STATS, body)
            log.info(f'Sent duel results: {len(duel_stats)}')
            duel_stats.clear()
        else:
            # todo remove debug logs
            log.info('duel stats: nothing to send')

    except Exception as e:
        log.info(f'Failed to send duel stats: {e}')
