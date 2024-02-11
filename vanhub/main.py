"""
Demonstrates how to use the background scheduler to schedule a job that executes on 3 second
intervals.
"""

from datetime import datetime
import time
import os

import requests
from apscheduler.schedulers.background import BackgroundScheduler


def tick():
    print('Tick! The time is: %s' % datetime.now())


def update():
    url = 'http://127.0.0.1:5000/api/update/'
    myobj = {'somekey': 'somevalue'}
    x = requests.post(url, json=myobj)
    print(x.text)


if __name__ == '__main__':
    update()
    '''
    scheduler = BackgroundScheduler()
    scheduler.add_job(tick, 'interval', seconds=3)
    scheduler.start()
    print('Press Ctrl+{0} to exit'.format('Break' if os.name == 'nt' else 'C'))

    try:
        # This is here to simulate application activity (which keeps the main thread alive).
        while True:
            time.sleep(2)
    except (KeyboardInterrupt, SystemExit):
        # Not strictly necessary if daemonic mode is enabled but should be done if possible
        scheduler.shutdown()
    '''