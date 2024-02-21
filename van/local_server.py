import os
import sys
import json
import uvicorn
import logging
import requests
import urllib.request, urllib.error

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from requests.adapters import Retry, HTTPAdapter
from fastapi import Request as fastRequest
from contextlib import asynccontextmanager
from pympler import asizeof
from dotenv import load_dotenv
from functools import partial
from fastapi import FastAPI
from typing import Optional

from vanhub import get_gps_data, get_tio_data
from sensors import sensor_config

# Create the local server payload.
# This is where data is stored in memory before
# being sent to the server.
payload = {'gps': [], 'tio': []}
for sensor in sensor_config.keys():
    payload[sensor] = []


def get_online_server():
    with open('van/vhs_cmd_config.json', 'r') as file:
        config = json.load(file)
        return config['ONLINE_SERVER_LOCATION']


def has_connection(timeout: int = 5) -> bool:
    """
    Check if the local_server can establish an outgoing internet connection to the server.
    :param timeout: The amount of time to try.
    :return: True if we can connect to the server, False otherwise.
    """
    try:
        urllib.request.urlopen(f'{get_online_server()}/api/auth.json', timeout=timeout)
        return True
    except (urllib.error.URLError,):
        return False
    except (Exception,) as e:
        logger.exception(e)


def report():
    # Check for missing server connectivity
    if not has_connection():
        logger.info(f'Failed to connect to server, Storing and Skipping Report ...', )
        logger.info(f'Size of current payload: Memory/{asizeof.asizeof(payload)/1024}kb')
        return

    # Now that we know we have server connectivity the client will try to authorize
    # Using the username and email provided either in the system environment or in the
    # .env file with keys 'VLS_USERNAME' and 'VLS_PASSWORD'
    logger.info('Established connection, Attempting authorization & upload...')
    try:
        session = requests.Session()
        auth_response = session.post(f'{get_online_server()}/api/auth.json', json={
            'email': os.getenv('VLS_USERNAME'),
            'password': os.getenv('VLS_PASSWORD'),
            'remember': True})

        # If we don't get the expected 200 response log the error and abort report
        if auth_response.status_code != 200:
            logger.error(f'Failed Server authentication (status: [{auth_response.status_code}]) aborting report')
            logger.info(f'Size of current payload: Memory/{asizeof.asizeof(payload) / 1024}kb')
            return

    # If there's an error networking log it and abort
    except (Exception,) as e:
        logger.error('Error during authentication request, aborting report')
        logger.exception(e)
        return

    logger.info(f'Authorization successful! | Sending payload ({asizeof.asizeof(payload)/1024}kb)')

    report_response = session.post(f'{get_online_server()}/api/report.json', json=payload)
    if report_response.status_code != 200:
        logger.warning(f'Server responded to report with {report_response.status_code}, aborting report')
        return

    logger.info(f'Report successful, clearing payload')
    # ABSTRACT: Step 2- Clear data from that sensor when it's submitted
    payload['gps'].clear()
    payload['tio'].clear()


def log_sensor(name: str, method: callable) -> None:
    logger.info(f'Logged {name} Sensor Data')
    payload[name].append(method())


def log_gps():
    logger.info('Logged GPS data')
    payload['gps'].append(get_gps_data())


# ABSTRACT: Step 1- Log function that collects the data and adds it to the payload
def log_tio():
    logger.info('Logged TomorrowIO data')
    payload['tio'].append(get_tio_data())


@asynccontextmanager
async def lifespan(fast_app: FastAPI):
    """Manages the lifespan of the FastAPI app"""

    # ----- Startup ------------------------
    load_dotenv()
    # TODO: Guard against missing ENV variables and such
    global scheduler
    try:
        scheduler = AsyncIOScheduler()
        scheduler.start()

        # ABSTRACT: Step 3- Add a job to call the log function on a regular basis
        scheduler.add_job(report, 'interval', id='report', minutes=1,
                          name='Reports current payload to online server')
        scheduler.add_job(log_gps, 'interval', id='log_gps', seconds=30,
                          name='Logs GPS data to payload.')
        scheduler.add_job(log_tio, 'interval', id='log_tio', seconds=30,
                          name='Logs TIO data to payload.')

        for van_sensor in sensor_config.keys():
            log_method = partial(log_sensor, van_sensor, sensor_config[van_sensor]['get'])
            scheduler.add_job(log_method, 'interval', id=f'log_{van_sensor}', minutes=1,
                              name=f'Logs {van_sensor} to payload.')

        logger.info('Successfully Created Scheduler Object')
    except (Exception,) as e:
        # If we get any type of exception we log it
        logger.error('Error creating scheduler object', exc_info=e)

    # ---- Yield To App --------------------
    yield

    # ---- Shutdown after app ------------
    scheduler.shutdown()


app = FastAPI(title='Van Hub', lifespan=lifespan)
logging.basicConfig(filename='example.log', encoding='utf-8', level=logging.INFO)

logger = logging.getLogger(__name__)
scheduler: Optional[AsyncIOScheduler] = None

# Logging Suppression
logging.getLogger('apscheduler.executors.default').setLevel(logging.CRITICAL + 1)


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
