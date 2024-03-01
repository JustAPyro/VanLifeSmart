import threading
import timeit
from functools import partial
from typing import Optional

from apscheduler.job import Job
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import logging

from van2.sensors import DataFactory


logger = logging.getLogger(__name__)

_scheduler: Optional[AsyncIOScheduler] = None


# This is a singleton scheduler that
def get_scheduler() -> AsyncIOScheduler:
    global _scheduler
    _lock = threading.Lock()

    if _scheduler is None:
        with _lock:
            if not _scheduler:
                logger.warning('Creating new AsyncIOScheduler')
                _scheduler = AsyncIOScheduler()

    return _scheduler


def schedule_sensors(sensors: list[DataFactory], payload: dict[DataFactory, list]):
    scheduler = get_scheduler()

    def schedule_sensor(sensor_to_schedule: DataFactory, to_payload: dict[DataFactory, list]):
        start = timeit.default_timer()
        to_payload.get(sensor_to_schedule).append(sensor_to_schedule.get_data())
        sensor_time = timeit.default_timer() - start
        logger.info(f'Recorded {sensor_to_schedule.data_type} sensor data in {sensor_time}')

    for sensor in sensors:
        sensor: DataFactory
        report_sensor = partial(schedule_sensor, sensor, payload)
        scheduler.add_job(report_sensor, 'interval', id=f'report_{sensor.data_type}', seconds=10)
    # ** sensor.default_schedule,
    # name = sensor.sensor_description)


def schedule_info(job: Job):
    return {
        'id': job.id,
        'description': job.name,
        'trigger': str(job.trigger),
        'next_run_time': job.next_run_time,
        'max_instances': job.max_instances,
        'misfire_grace_time': job.misfire_grace_time,
        'active': 'True'
    }
