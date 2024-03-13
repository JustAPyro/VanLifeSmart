import threading
import timeit
from functools import partial
from typing import Optional

from sqlalchemy import Engine
from sqlalchemy.orm import Session
from apscheduler.job import Job
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from van2.sensors import Sensor
import logging



logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()


def get_scheduler():
    return scheduler


def schedule_sensors(sensors: list[Sensor], database: Engine):

    # Methodology for scheduling sensors
    def schedule_sensor(s: Sensor, db: Engine):
        # Get the start time so we can check runtime
        start = timeit.default_timer()

        # Create a database session and commit the data
        with Session(db) as session:
            session.add(s.get_data())
            session.commit()

        # Calculate the time to get data and commit
        sensor_time = timeit.default_timer() - start

        # Log that it's completed
        logger.info(f'Recorded {s.data_type} sensor data in {sensor_time}')

    for sensor in sensors:
        sensor: Sensor
        report_sensor = partial(schedule_sensor, sensor, database)
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
