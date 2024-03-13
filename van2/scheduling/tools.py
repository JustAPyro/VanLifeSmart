import threading
import timeit
from functools import partial
from typing import Optional

from apscheduler.job import Job
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import logging

from van2.sensors import Sensor

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()


def get_scheduler():
    return scheduler


def schedule_sensors(sensors: list[Sensor], payload: dict[Sensor, list]):
    def schedule_sensor(sensor_to_schedule: Sensor, to_payload: dict[Sensor, list]):
        start = timeit.default_timer()
        to_payload.get(sensor_to_schedule).append(sensor_to_schedule.get_data())
        sensor_time = timeit.default_timer() - start
        logger.info(f'Recorded {sensor_to_schedule.data_type} sensor data in {sensor_time}')

    for sensor in sensors:
        sensor: Sensor
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
