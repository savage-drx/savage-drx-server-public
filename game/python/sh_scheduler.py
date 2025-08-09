# ---------------------------------------------------------------------------
#           Name: sh_scheduler.py
#    Description: possibility to schedule events on client/server
# ---------------------------------------------------------------------------


import sched
import time
from typing import Optional

import sh_executor
import sh_logger as log
import sv_discord


class _Context:
    SCHEDULER = Optional[sched.scheduler]

    @staticmethod
    def init():
        log.info("Initializing Scheduler...")
        _Context.SCHEDULER = sched.scheduler(time.time, time.sleep)
        sh_executor.submit_task(_Context.start)

    @staticmethod
    def stop():
        _Context.SCHEDULER.cancel(restart_discord)

    @staticmethod
    def start():
        # if sv_discord.DiscordSettings.DISCORD_IS_ENABLED:
        #     s.enter(30, 1, _restart_discord)
        _Context.SCHEDULER.run()


def restart_discord():
    log.info("Scheduler: restarting Discord...")
    sv_discord.reconnect()
    _Context.SCHEDULER.enter(3600, 1, restart_discord)
