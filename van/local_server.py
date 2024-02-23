import os
import sys
import json
import copy
import timeit
import uvicorn
import logging
import requests
import urllib.request, urllib.error

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import Request as fastRequest
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from functools import partial
from pympler import asizeof
from fastapi import FastAPI
from typing import Optional

from sensors import sensors

required_environments = [
    'VLS_USERNAME',  # Username for public server account
    'VLS_PASSWORD',  # Password for public server account
    'VLS_SERVER',  # Address of the public server to report to
    'TOMORROWAPI'  # API key for Tomorrow API - Used to pull weather data
]


def has_connection(timeout: int = 5) -> bool:
    """
    Check if the local_server can establish an outgoing internet connection to the server.
    :param timeout: The amount of time to try.
    :return: True if we can connect to the server, False otherwise.
    """
    try:
        urllib.request.urlopen(f'{os.getenv("VLS_SERVER")}/api/auth.json', timeout=timeout)
        return True
    except (urllib.error.URLError,):
        return False
    except (Exception,) as e:
        logger.exception(e)


def _abort_report():
    return
    backup_size = 0
    backup_payload = copy.deepcopy(payload)
    for data_log in payload.values():
        data_log.clear()

    for dtype, data in backup_payload.items():
        with open(f'data_backups/{dtype}_backup.csv', 'a') as file:
            if data[0]:
                # Pull header on the first item
                # TODO: Make this less fragile lol
                file.write(','.join(*data[0].keys()))
            for item in data:
                file.write((','.join(*[str(value) for value in item.values()])) + '\n')
            file.seek(0, os.SEEK_END)
            backup_size += file.tell()

    logger.info(f'Aborted report and saved {backup_size / 1024}kb data to backup folders.')


def report(payload: dict[str, list]):
    # Check for server connectivity
    # and abort immediately if not found
    if not has_connection():
        logger.info(f'Failed to connect to server, Storing and Skipping Report ...', )
        _abort_report()
        return

    # Now that we know we have server connectivity the client will try to authorize
    # Using the username and email provided either in the system environment or in the
    # .env file with keys 'VLS_USERNAME' and 'VLS_PASSWORD'
    logger.info('Established connection, Attempting authorization & upload...')
    try:
        session = requests.Session()
        auth_response = session.post(f'{os.getenv("VLS_SERVER")}/api/auth.json', json={
            'email': os.getenv('VLS_USERNAME'),
            'password': os.getenv('VLS_PASSWORD'),
            'remember': True})

        # If we don't get the expected 200 response log the error and abort report
        if auth_response.status_code != 200:
            logger.error(f'Failed Server authentication (status: [{auth_response.status_code}]) aborting report')
            _abort_report()
            return

    # If there's an error networking log it and abort
    except (Exception,) as e:
        logger.error('Error during authentication request, aborting report')
        _abort_report()
        logger.exception(e)
        return

    logger.info(f'Authorization successful! | Sending payload ({asizeof.asizeof(payload) / 1024}kb)')

    report_response = session.post(f'{os.getenv("VLS_SERVER")}/api/report.json', json=payload)
    if report_response.status_code != 200:
        logger.warning(f'Server responded to report with {report_response.status_code}, aborting report')
        return

    logger.info(f'Report successful, clearing payload')
    for data_log in payload.values():
        data_log.clear()


def log_sensor(name: str, method: callable, log_to: dict[str, list]) -> None:
    """This is just a helper method that will log the data collection and add results to payload"""
    start = timeit.default_timer()
    log_to[name].append(method())
    logger.info(f'Logged {name} Sensor Data in {(timeit.default_timer() - start):.2f}s.')


@asynccontextmanager
async def lifespan(fast_app: FastAPI):
    """Manages the lifespan of the FastAPI app"""
    # ----- Startup ------------------------
    # Load environment vars from .env
    load_dotenv()

    # Here we check to make sure we have the expected environment variables
    # as missing env variables down the line can cause silent failures
    for env in required_environments:
        if os.getenv(env) is None:
            raise RuntimeError(f'Missing environment variable: {env} | Add to .env or system environment')

    # Create the local server payload with a list for each type of sensor.
    # This is where data is stored in memory before
    # being sent to the server.
    payload = {}
    for x_sensor in sensors:
        payload[x_sensor.sensor_type] = []

    global scheduler
    try:
        # Create an async scheduler to update and send data in the background
        scheduler = AsyncIOScheduler()
        scheduler.start()

        # bind the payload to report then schedule the report job.
        # This is a schedule that will always run to report data to server
        # if the server cannot be reached it will write it to csv files instead.
        report_method = partial(report, payload)
        scheduler.add_job(report_method, 'interval', id='report', minutes=1,
                          name='Reports current payload to online server')

        # This is a fairly complicated block of code that generates a job for
        # each sensor provided in the sensors list of sensors.py
        # It does this first by creating a partial function, essentially passing the
        # sensor name and get function into the log sensor method. Then it adds the partial
        # function to a scheduler job, by unpacking the arguments from the sensors default schedule
        for sensor in sensors:
            log_method = partial(log_sensor, sensor.sensor_type, sensor.get_data, payload)
            scheduler.add_job(log_method, 'interval', id=f'log_{sensor.sensor_type}',
                              **sensor.default_schedule,
                              name=f'Log {sensor.sensor_type}')
        logger.info('Successfully created and loaded schedulers')
    except (Exception,) as e:
        # If we get any type of exception we log it
        logger.error('Error creating scheduler object', exc_info=e)

    # ---- Yield To App --------------------
    # This is where the app actually runs
    yield

    # ---- Shutdown after app ------------
    # This is cleanup and shutdown code
    scheduler.shutdown()

    # Shutdown each sensor
    for sensor in sensors:
        sensor.shutdown()



app = FastAPI(title='Van Hub', lifespan=lifespan)
logging.basicConfig(level=logging.INFO)
#logging.basicConfig(level=logging.INFO,
#                    filename='2.22.24_server_log.txt',
#                    filemode='a',
#                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
#                    datefmt='%H:%M:%S')

logger = logging.getLogger(__name__)
scheduler: Optional[AsyncIOScheduler] = None


@app.get('/')
def resched():
    return 'hello'


@app.get('/scheduler.json')
def get_scheduler():
    report_job = scheduler.get_job('report')
    log_gps_job = scheduler.get_job('log_gps')
    log_tio_job = scheduler.get_job('log_tio')
    # ABSTRACT: Step 4?5? - Add it to the scheduler
    return {
        'report': {
            'description': report_job.name,
            'trigger': str(report_job.trigger),
            'next_run_time': report_job.next_run_time,
            'max_instances': report_job.max_instances,
            'misfire_grace_time': report_job.misfire_grace_time
        },
        'log_gps': {
            'description': log_gps_job.name,
            'trigger': str(log_gps_job.trigger),
            'next_run_time': log_gps_job.next_run_time,
            'max_instances': log_gps_job.max_instances,
            'misfire_grace_time': log_gps_job.misfire_grace_time
        },
        'log_tio': {
            'description': log_tio_job.name,
            'trigger': str(log_tio_job.trigger),
            'next_run_time': log_tio_job.next_run_time,
            'max_instances': log_tio_job.max_instances,
            'misfire_grace_time': log_tio_job.misfire_grace_time
        },
    }


@app.get('/scheduler/{schedule}.json')
def get_specific_scheduler(schedule: str):
    job = scheduler.get_job(schedule)
    if not job:
        # TODO: JSON Error format
        return {'Error': f'Could not find scheduler: {schedule}'}
    return {
        'description': job.name,
        'trigger': str(job.trigger),
        'next_run_time': job.next_run_time,
        'max_instances': job.max_instances,
        'misfire_grace_time': job.misfire_grace_time
    }


@app.patch('/scheduler/{schedule}.json')
async def patch_specific_scheduler(schedule: str, request: fastRequest):
    job = scheduler.get_job(schedule)
    if not job:
        # TODO: JSON error format
        return {'Error': f'Could not find scheduler: {schedule}'}
    patch_values = await request.json()
    trigger = patch_values['trigger']['type']
    intervals = patch_values['trigger']['interval']
    scheduler.reschedule_job(job.id, trigger=trigger, **intervals)
    return {
        'description': job.name,
        'trigger': str(job.trigger),
        'next_run_time': job.next_run_time,
        'max_instances': job.max_instances,
        'misfire_grace_time': job.misfire_grace_time
    }


if __name__ == '__main__':
    uvicorn.run('local_server:app', host='0.0.0.0', reload=False)
