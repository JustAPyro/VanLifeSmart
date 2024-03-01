import timeit
from functools import partial
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import logging

from van2.sensors import DataFactory

_scheduler: Optional[AsyncIOScheduler] = None

logger = logging.getLogger(__name__)


# This is a singleton scheduler that
def get_scheduler() -> AsyncIOScheduler:
    global _scheduler

    if _scheduler is None:
        _scheduler = AsyncIOScheduler()
        _scheduler.start()

    return _scheduler


def schedule_sensors(sensors: list[DataFactory], payload: dict[DataFactory, list]):
    scheduler = get_scheduler()

    def schedule_sensor(sensor_to_schedule: DataFactory, to_payload: dict[DataFactory, list]):
        start = timeit.default_timer()
        to_payload.get(sensor_to_schedule).append(sensor_to_schedule.get_data().to_line())
        sensor_time = timeit.default_timer() - start
        logger.info(f'Recorded {sensor_to_schedule.data_type} sensor data in {sensor_time}')

    for sensor in sensors:
        sensor: DataFactory
        report_sensor = partial(schedule_sensor, sensor, payload)
        scheduler.add_job(report_sensor, 'interval', id=f'report_{sensor.data_type}', seconds=10)
    # ** sensor.default_schedule,
    # name = sensor.sensor_description)
