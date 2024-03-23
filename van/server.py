#!/usr/bin/env python3.x
import requests
from dotenv import load_dotenv

import logging
import os
from contextlib import asynccontextmanager
from functools import partial
from pathlib import Path

import uvicorn

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from sensors import activate_sensors
from van.scheduling.tools import scheduler, schedule_sensors
from endpoints import endpoints, not_found_exception_handler
from database import engine
from models import GPSData, TomorrowIO

# Refuse to start if these environment variables aren't set
required_environment = (
    'VLS_INSTALL',  # Install location
    'VLS_DATA_PATH',  # Location of logs and local database
    'TOMORROW_IO_KEY',  # API Key for weather information
)

# This maps loggers to output files
logging_map = {
    'server.txt': 'uvicorn',
    'traffic.txt': 'uvicorn.access',
    'apscheduler.txt': 'apscheduler'
}


def heartbeat():
    heartbeat_job = scheduler.get_job('heartbeat')
    with Session(engine) as session:
        gps_data = {'headers': GPSData.__table__.columns.keys(),
                    'data': [data.as_list() for data in session.query(GPSData).all()]}
        try:
            x = requests.post('http://127.0.0.1:5000/api/heartbeat.json',
                              json={'email': 'luke.m.hanna@gmail.com', 'next_heartbeat': str(heartbeat_job.next_run_time), 'gps': gps_data})
            if x.json():
                for gps_id in x.json()['gps']:
                    session.query(GPSData).filter_by(id=gps_id).delete()
                session.commit()
        except ConnectionError as e:
            pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start by loading any environment variables we can find
    load_dotenv()

    # Fail to launch if any environment variable listed in required are missing
    if not all([(os.getenv(env) is not None) for env in required_environment]):
        raise NotImplementedError("You are missing a required environment variable.")

    # Check to make sure the data path exists for logs (Database will go in the data path root)
    Path(f'{os.getenv("VLS_DATA_PATH")}/logs').mkdir(parents=True, exist_ok=True)

    # Map library logs to output log files
    logging.basicConfig(level=logging.INFO)
    for log_file, logger_name in logging_map.items():
        path = os.path.abspath(f'{os.getenv("VLS_DATA_PATH")}/logs/{log_file}')
        file_handler = logging.FileHandler(path)
        logger = logging.getLogger(logger_name)
        logger.addHandler(file_handler)

    # Get and start the scheduler
    scheduler.start()

    # Activate the sensors, create a payload for them, then schedule them
    sensors = activate_sensors(development=True)
    schedule_sensors(sensors, engine)

    # schedule the heartbeat call
    scheduler.add_job(heartbeat, trigger='interval', seconds=30,
                      id='heartbeat',
                      name="Connect to the online server to upload/download data.")

    # Register all the subdomain routers
    app.include_router(endpoints)

    # Mount static files (html, css, js, etc)
    app.mount('/static', StaticFiles(directory=f'{os.getenv("VLS_INSTALL")}/van/static'), name="static")

    # Launch the server
    yield


load_dotenv()
server = FastAPI(title='Van Hub',
                 lifespan=lifespan,
                 exception_handlers={
                     404: not_found_exception_handler
                 })

if __name__ == '__main__':
    uvicorn.run('server:server', host='localhost', reload=True)
