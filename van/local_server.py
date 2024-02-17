"""
Demonstrates how to use the background scheduler to schedule a job that executes on 3 second
intervals.
"""
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

from vanhub import get_gps_data

payload = {'gps': []}


def get_online_server():
    with open('vhs_cmd_config.json', 'r') as file:
        return json.load(file)['ONLINE_SERVER_LOCATION']


def report():
    logger.info(f'Reporting to online server with email {os.getenv("VLS_USERNAME")}')
    # TODO: Guard and throw useful error against missing .env variables
    session = requests.Session()
    auth_url = f'{get_online_server()}/api/auth.json'
    email = os.getenv('VLS_USERNAME')
    auth_json = {'email': email, 'password': os.getenv('VLS_PASSWORD'), 'remember': True}
    auth_response = session.post(auth_url, json=auth_json)
    logger.info(f'Authorization returned: [{auth_response.status_code}] | Sending payload:\n{json.dumps(payload, indent=4)}')

    report_url = f'{get_online_server()}/api/report.json'
    report_response = session.post(report_url, json=payload)
    logger.info(f'Report returned status code [{report_response.status_code}] '
                f'and the following payload:\n{json.dumps(report_response.json(), indent=4)}')


def log_gps():
    logger.info('Logged GPS data')
    payload['gps'].append(get_gps_data())


@asynccontextmanager
async def lifespan(fast_app: FastAPI):
    """Manages the lifespan of the FastAPI app"""

    # ----- Startup ------------------------
    load_dotenv()
    global scheduler
    try:
        scheduler = AsyncIOScheduler()
        scheduler.start()

        scheduler.add_job(report, 'interval', id='report', minutes=1,
                          name='Reports current payload to online server')
        scheduler.add_job(log_gps, 'interval', id='log_gps', seconds=30,
                          name='Logs GPS data to payload.')

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
        }
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
