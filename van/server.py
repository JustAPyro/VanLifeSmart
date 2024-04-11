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
    'VLS_VEHICLE_NAME',
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

    # Log the heartbeat
    record_heartbeat()

    # Get the name of the vehicle and user data
    vehicle_name = os.getenv('VLS_VEHICLE_NAME')
    email = os.getenv('VLS_VEHICLE_EMAIL')

    # Generate the data structure we send to the server
    data = {
        'email': email,
        'vehicle_name': vehicle_name,
        'next_heartbeat': datetime.now().isoformat(),
        'database': {
            'heartbeat': {'headers': Heartbeat.__table__.columns.keys(), 'data': []},
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
        heartbeats = session.query(Heartbeat).order_by(asc('time_utc')).all()
        for heartbeat in heartbeats[:-1]:
            data['database']['heartbeat']['data'].append(heartbeat.as_list())


    # Now we try to send this all to the server
    try:
        basic_auth_string = f'{os.getenv("VLS_VEHICLE_EMAIL")}:{os.getenv("VLS_V_USER_PASSWORD")}'
        basic_auth_encoded = base64.b64encode(basic_auth_string.encode('ascii'))
        request_headers = {
            'Authorization': f'Basic {basic_auth_encoded}'
        }

        url = ('http://127.0.0.1:5000/api/heartbeat.json' if dev_env else 
            'https://justapyr0.pythonanywhere.com/api/heartbeat.json')
        response = requests.post(
            url=url,
            json=data,
            headers=request_headers)

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

        if 'heartbeat' in json_back['recieved']:
            for item in json_back['received']['heartbeat']:
                session.query(Heartbeat).filter_by(id=item).delete()

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
