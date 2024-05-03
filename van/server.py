#!/usr/bin/env python3.x
import requests
from dotenv import load_dotenv
import base64
import logging
import os
from contextlib import asynccontextmanager
from functools import partial
from pathlib import Path
import pytz
from sqlalchemy import desc, asc
import uvicorn
from datetime import datetime, timedelta
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from urllib3.exceptions import MaxRetryError, NewConnectionError
from urllib import request

from van.sensors import activate_sensors
from van.scheduling.tools import scheduler, schedule_sensors
from van.endpoints import endpoints, not_found_exception_handler
from van.database import engine
from models import GPSData, TomorrowIO, Vehicle, Heartbeat

dev_env = True

logger = logging.getLogger(__name__)

# Refuse to start if these environment variables aren't set
required_environment = (
    'VLS_INSTALL',  # Install location
    'VLS_DATA_PATH',  # Location of logs and local database
    'TOMORROW_IO_KEY',  # API Key for weather information
    'VLS_V_NAME',
    'VLS_VEHICLE_EMAIL',
    'VLS_V_USER_PASSWORD',
)

# This maps loggers to output files
logging_map = {
    'server.txt': 'uvicorn',
    'traffic.txt': 'uvicorn.access',
    'apscheduler.txt': 'apscheduler'
}

def can_connect(url_string: str) -> bool:
    try:
        request.urlopen(url_string, timeout=1)
        return True
    except request.URLError:
        return False

def record_heartbeat():
    # Starting point for the heartbeat object
    heartbeat_dict = {
        'time_utc': datetime.now(),
        'next_time': scheduler.get_job('heartbeat').next_run_time
    }

    # Get the last heartbeat
    last = None
    with Session(engine) as session:
        last = session.query(Heartbeat).order_by(desc('time_utc')).first()

    # Check if this heartbeat was expected or if it's late 
    if last == None or datetime.now() - last.next_time < timedelta(seconds=1):
        heartbeat_dict['on_schedule'] = True
    else:
        heartbeat_dict['on_schedule'] = False

    # Check for connectivity to server and internet
    google_url = 'http://142.250.190.142'
    server_url = ('http://127.0.0.1:5000/api/heartbeat.json' if dev_env else 
        'https://justapyr0.pythonanywhere.com/api/heartbeat.json')

    heartbeat_dict['server'] = can_connect(server_url)
    heartbeat_dict['internet'] = True if heartbeat_dict['server'] else can_connect(google_url)
    with Session(engine) as session:
        session.add(Heartbeat(**heartbeat_dict))
        session.commit()
    

def heartbeat():

    # Generate the data structure we send to the server
    data = {
        'database': {
            'gps': {'headers': GPSData.__table__.columns.keys(), 'data': []},
        }
    }

    # This list provides names and model data tables
    # For any tables we want to upload to the server
    # TODO Autogenerate this list
    upload = [
        ('gps', GPSData),
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
        # Create an authorization header by encoding email/password (Basic-Auth)
        basic_auth_string = f'{os.getenv("VLS_VEHICLE_EMAIL")}:{os.getenv("VLS_V_USER_PASSWORD")}'
        basic_auth_encoded = base64.b64encode(basic_auth_string.encode('ascii'))
        request_headers = {
            'Authorization': f'Basic {basic_auth_encoded}',
            'Content-Type': 'application/json'
        }

        # Construct the URL
        url = ('http://127.0.0.1:5000/api/heartbeat.json' if dev_env else 
            f'https://justapyr0.pythonanywhere.com/api/heartbeat/{os.getenv("VLS_V_NAME")}.json')

        # And post to server
        response = requests.post(
            url=url,
            json=data,
            headers=request_headers)

        # Filter for responses that aren't 200
        # TODO: We should differentiate between requests
        if response.status_code != 200:
            print(response.status_code)
            print(response.content)

        # Commit all the changes that we made
        # TODO: Consider another handshake before commiting this delete
        session.commit()

    except requests.exceptions.ConnectionError as e:
        return


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start by loading any environment variables we can find
    load_dotenv()


    # Fail to launch if any environment variable listed in required are missing
    missing = []
    for env in required_environment:
        if os.getenv(env) is None:
            missing.append(env)
    if len(missing) != 0:
        raise NotImplementedError(f'You are missing the following required environment variables: {missing}')

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

    # Call a start-up heartbeat
    heartbeat()

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
