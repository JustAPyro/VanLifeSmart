"""
Demonstrates how to use the background scheduler to schedule a job that executes on 3 second
intervals.
"""
import time
import os
from contextlib import asynccontextmanager
from typing import Optional

import requests
import uvicorn
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
import logging
from fastapi import FastAPI

payload = {}


def report():
    logger.info('Reporting to Public Server')


@asynccontextmanager
async def lifespan(fast_app: FastAPI):
    """Manages the lifespan of the FastAPI app"""

    # ----- Startup ------------------------
    global scheduler
    try:
        scheduler = AsyncIOScheduler()
        scheduler.start()
        scheduler.add_job(report, 'interval', seconds=5, id='report')
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


@app.get('/')
def resched():
    scheduler.reschedule_job('printer', trigger='interval', seconds=20)


@app.get('/scheduler.json')
def get_scheduler():
    pass


if __name__ == '__main__':
    uvicorn.run('van.main:app', reload=True)
