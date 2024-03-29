#!/usr/bin/env python3.x
import requests
from dotenv import load_dotenv

import logging
import os
from contextlib import asynccontextmanager
from functools import partial
from pathlib import Path
import pytz

import uvicorn

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from urllib3.exceptions import MaxRetryError, NewConnectionError

from van.sensors import activate_sensors
from van.scheduling.tools import scheduler, schedule_sensors
from van.endpoints import endpoints, not_found_exception_handler
from van.database import engine
from models import GPSData, TomorrowIO, Vehicle

dev_env = True

# Refuse to start if these environment variables aren't set
required_environment = (
    'VLS_INSTALL',  # Install location
    'VLS_DATA_PATH',  # Location of logs and local database
    'TOMORROW_IO_KEY',  # API Key for weather information
    'VLS_VEHICLE_NAME',
    'VLS_VEHICLE_EMAIL',
)

# This maps loggers to output files
logging_map = {
    'server.txt': 'uvicorn',
    'traffic.txt': 'uvicorn.access',
    'apscheduler.txt': 'apscheduler'
}


def heartbeat():
    # Get the time of the next heartbeat
    heartbeat_job = scheduler.get_job('heartbeat')
    next_heartbeat = heartbeat_job.next_run_time.astimezone(pytz.utc).isoformat()

    # Get the name of the vehicle and user data
    vehicle_name = os.getenv('VLS_VEHICLE_NAME')
    email = os.getenv('VLS_VEHICLE_EMAIL')

    # Generate the data structure we send to the server
    data = {
        'email': email,
        'vehicle_name': vehicle_name,
        'next_heartbeat': next_heartbeat,
        'database': {
            # Here we also find and insert the column names for each dataset
            'gps': {'headers': GPSData.__table__.columns.keys(), 'data': []},
            'tio': {'headers': TomorrowIO.__table__.columns.keys()}
        }
    }

    # This list provides names and model data tables
    # For any tables we want to upload to the server
    # TODO Autogenerate this list
    upload = [
        ('gps', GPSData),
        ('tio', TomorrowIO)
    ]

    # TODO abort beforehand if no connection
    # This packs the data from the table and names provided in the list
    with Session(engine) as session:
        for data_name, table in upload:
            data['database'][data_name]['data'] = [
                line.as_list() for line in session.query(table).all()
            ]

    # Now we try to send this all to the server
    try:
        url = ('http://127.0.0.1:5000/api/heartbeat.json' if dev_env else 
            'http://justapyr0.pythonanywhere.com/api/heartbeat.json')
        response = requests.post(
            url=url,
            json=data)

        # Filter for responses that aren't 200
        # TODO: We should differentiate between requests
        if response.status_code != 200:
            print(response.status_code)
            print(response.content)

        # Delete from local tables based
        # the json we received back
        json_back = response.json()
        for data_name, table in upload:
            for received_id in json_back['received'][data_name]:
                session.query(table).filter_by(id=received_id).delete()

        # Commit all the changes we made from the database
        session.commit()

        # TODO: We may want to do another handshake before we commit this delete
    except requests.exceptions.ConnectionError as e:
        return


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
        path = os.path.abspath(f'{os.getenv("VLS_DATA_PATH")}/logs/{log_file}.log')
        #file_handler = logging.FileHandler(path)
        logger = logging.getLogger(logger_name)
        #logger.addHandler(file_handler)

    # Get and start the scheduler
    scheduler.start()

    # Activate the sensors, create a payload for them, then schedule them
    sensors = activate_sensors(development=dev_env)
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

    # Shutdown the scheduler
    scheduler.shutdown()

    # After the server runs shut down all the sensors
    for sensor in sensors:
        sensor.shutdown()


load_dotenv()
server = FastAPI(title='Van Hub',
                 lifespan=lifespan,
                 exception_handlers={
                     404: not_found_exception_handler
                 })

if __name__ == '__main__':
    uvicorn.run('server:server', host='localhost', reload=True)
