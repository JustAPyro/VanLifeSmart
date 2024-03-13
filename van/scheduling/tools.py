import logging
import timeit
from functools import partial

from apscheduler.job import Job
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import Engine
from sqlalchemy.orm import Session

from van.sensors import Sensor

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()


def get_scheduler():
    """Dependency fetcher- Returns the parent scheduler"""
    return scheduler


def schedule_sensors(sensors: list[Sensor], database: Engine):
    """This takes a list of sensors and records their output to the provided database."""

    # Methodology for scheduling sensors
    def schedule_sensor(s: Sensor, db: Engine):
        # Get the start time so we can check runtime
        start = timeit.default_timer()

        # Create a database session and commit the data
        with Session(db) as session:
            session.add(s.get_data())
            session.commit()

        # Calculate and log the time to get data and commit
        sensor_time = timeit.default_timer() - start
        logger.info(f'Recorded {s.data_type} sensor data in {sensor_time}')

    # Now that we've defined the method that logs the data,
    # We create a partial function by binding the above method to the database and each sensor
    # And then schedule the sensor to run on a set interval
    for sensor in sensors:
        sensor: Sensor
        report_sensor = partial(schedule_sensor, sensor, database)
        scheduler.add_job(report_sensor, 'interval',
                          id=sensor.schedule_config['id'], seconds=10,
                          name=sensor.schedule_config['description'],
                          )
    # ** sensor.default_schedule,
    # name = sensor.sensor_description)


def schedule_info(job: Job):
    """Helper method to return a dict of useful information about a scheduled job"""
    return {
        'id': job.id,
        'description': job.name,
        'trigger': str(job.trigger),
        'next_run_time': job.next_run_time,
        'max_instances': job.max_instances,
        'misfire_grace_time': job.misfire_grace_time,
        'active': 'True'
    }
