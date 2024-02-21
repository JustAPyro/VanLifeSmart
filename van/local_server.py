import json
import os
import requests
import uvicorn
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import Request as fastRequest
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI
from typing import Optional

from vanhub import get_gps_data, get_tio_data
from sensors import get_dht_data

payload = {'gps': [], 'tio': []}


def get_online_server():
    with open('van/vhs_cmd_config.json', 'r') as file:
        config = json.load(file)
        return config['ONLINE_SERVER_LOCATION']


def report():
    logger.info(f'Reporting to online server with email {os.getenv("VLS_USERNAME")}')
    # TODO: Guard and throw useful error against missing .env variables

    if not os.getenv('VLS_PASSWORD') or not os.getenv('VLS_USERNAME'):
        logger.error('MISSING .env file with VLS_USERNAME and VLS_PASSWORD')
        raise Exception('Include .env file with VLS_USERNAME and VLS_PASSWORD')

    session = requests.Session()
    auth_url = f'{get_online_server()}/api/auth.json'
    email = os.getenv('VLS_USERNAME')
    auth_json = {'email': email, 'password': os.getenv('VLS_PASSWORD'), 'remember': True}
    try:
        auth_response = session.post(auth_url, json=auth_json)
    except (Exception,) as e:
        logger.info(str(e))
        logger.info('Failed to establish connection, skipping report.')
        return
    logger.info(
        f'Authorization returned: [{auth_response.status_code}] | Sending payload:\n{json.dumps(payload, indent=4)}')

    report_url = f'{get_online_server()}/api/report.json'
    report_response = session.post(report_url, json=payload)
    logger.info(f'Report returned status code [{report_response.status_code}] '
                f'and the following payload:\n{json.dumps(report_response.json(), indent=4)}')
    # ABSTRACT: Step 2- Clear data from that sensor when it's submitted
    payload['gps'].clear()
    payload['tio'].clear()


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

        logger.info('Successfully Created Scheduler Object')
    except (Exception,) as e:
        # If we get any type of exception we log it
        logger.error('Error creating scheduler object', exc_info=e)

    # ---- Yield To App --------------------
    yield


app = FastAPI(title='Van Hub', lifespan=lifespan)
logging.basicConfig(level=logging.INFO)
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
