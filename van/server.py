#!/usr/bin/env python3.x

# TODO: If data/backups and data/logs don't exist on startup create automagically

import os
import logging
import uvicorn
from sqlalchemy import create_engine

from models import Base
from fastapi import FastAPI
from functools import partial
from pathlib import Path
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from fastapi.staticfiles import StaticFiles
from core import heartbeat
from sensors import activate_sensors
from van.scheduling.endpoints import schedule_urls
from van.scheduling.tools import scheduler, schedule_sensors

# Refuse to start if these environment variables aren't set
required_environment = (
    'VLS_INSTALL',  # Install location
    'VLS_DATA_PATH'  # Location of logs and local database
)

# This maps loggers to output files
logging_map = {
    'server.txt': 'uvicorn',
    'traffic.txt': 'uvicorn.access',
    'apscheduler.txt': 'apscheduler'
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Fail to launch if any environment variable listed in required are missing
    if not all([(os.getenv(env) is not None) for env in required_environment]):
        raise NotImplementedError("You are missing a required environment variable.")

    # Check to make sure the data path exists for logs (Database will go in the data path root)
    Path(f'{os.getenv("VLS_DATA_PATH")}/logs').mkdir(parents=True, exist_ok=True)

    engine = create_engine(
        f'sqlite:///{os.getenv("VLS_DATA_PATH")}/database.db',
        connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)

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

    payload = {sensor: [] for sensor in sensors}
    # schedule the heartbeat call
    heartbeat_call = partial(heartbeat, payload)
    scheduler.add_job(heartbeat_call, trigger='interval', seconds=30)

    # Register all the subdomain routers
    app.include_router(schedule_urls)

    # Mount static files (html, css, js, etc)
    app.mount('/static', StaticFiles(directory=f'{os.getenv("VLS_LOCATION")}/van/static'), name="static")

    # Launch the server
    yield


load_dotenv()
server = FastAPI(title='Van Hub', lifespan=lifespan)

if __name__ == '__main__':
    uvicorn.run('server:server', host='localhost')
