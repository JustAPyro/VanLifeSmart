"""
Demonstrates how to use the background scheduler to schedule a job that executes on 3 second
intervals.
"""
import time
import os
import requests
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('example_logger')


def update():
    logger.info('Sending Server Update...')
    load_dotenv()
    session = requests.Session()
    auth_url = 'http://127.0.0.1:5000/api/auth.json'
    auth_json = {'email': 'luke.m.hanna@gmail.com', 'password': os.getenv('MYPASS'), 'remember': True}
    auth_response = session.post(auth_url, json=auth_json)

    if auth_response.status_code != 200:
        raise Exception("Failed to authenticate with API")

    update_url = 'http://127.0.0.1:5000/api/update.json'
    update_json = {
        'latitude': 41.6206289,
        'longitude': -85.8266781
    }
    update_response = session.post(update_url, json=update_json)


if __name__ == '__main__':
    scheduler = BackgroundScheduler()
    scheduler.add_job(update, 'interval', seconds=60)
    scheduler.start()

    try:
        # This is here to simulate application activity (which keeps the main thread alive).
        while True:
            time.sleep(2)
    except (KeyboardInterrupt, SystemExit):
        # Not strictly necessary if daemonic mode is enabled but should be done if possible
        scheduler.shutdown()
