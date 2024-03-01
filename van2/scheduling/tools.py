from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from van2.sensors import DataFactory

_scheduler: Optional[AsyncIOScheduler] = None


# This is a singleton scheduler that
def get_scheduler() -> AsyncIOScheduler:
    global _scheduler

    if _scheduler is None:
        _scheduler = AsyncIOScheduler()
        _scheduler.start()

    return _scheduler


def schedule_sensors(sensors: list[DataFactory]):
    pass