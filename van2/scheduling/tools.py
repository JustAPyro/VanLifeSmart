from functools import partial
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
    scheduler = get_scheduler()

    def schedule_sensor(sensor, payload):
        print(sensor.get_data().to_line())

    for sensor in sensors:
        sensor: DataFactory
        report_sensor = partial(schedule_sensor, sensor, {})
        scheduler.add_job(report_sensor, 'interval', id=f'report_{sensor.data_type}', seconds=10)
       # ** sensor.default_schedule,
       # name = sensor.sensor_description)
