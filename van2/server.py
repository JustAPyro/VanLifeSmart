#!/usr/bin/env python3.x
import uvicorn
import os
from fastapi import FastAPI
from dotenv import load_dotenv
import logging
from contextlib import asynccontextmanager
from sensors import activate_sensors
from scheduling.tools import get_scheduler, schedule_sensors
from core import heartbeat

# Refuse to start if these environment variables aren't set
required_environment = (
    'VLS_INSTALL',  # Install location
)

# This maps loggers to output files
logging_map = {
    'server.txt': 'uvicorn',
    'traffic.txt': 'uvicorn.access',
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Map library logs to output log files
    for log_file, logger_name in logging_map.items():
        path = os.path.abspath(f'{os.getenv("VLS_INSTALL")}/van2/data/logs/{log_file}')
        file_handler = logging.FileHandler(path)
        logger = logging.getLogger(logger_name)
        logger.addHandler(file_handler)

    # Fail to launch if any environment variable listed in required are missing
    if not all([(os.getenv(env) is not None) for env in required_environment]):
        raise NotImplementedError("You are missing a required environment variable.")

    # This will create all sensors with the given configuration
    sensors = activate_sensors(development=True)

    yield


load_dotenv()
server = FastAPI(title='Van Hub', lifespan=lifespan)


@server.get('/')
def thing():
    return 'hi'


if __name__ == '__main__':
    uvicorn.run('server:server', host='localhost', reload=True)
