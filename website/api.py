import logging
import datetime
import pytz
import time

from flask import Blueprint, request
from flask_login import login_required, current_user

from .models import Maintenance, GPSData, TomorrowIO
from . import db

logger = logging.getLogger('funmobile_server')
api = Blueprint('api', __name__)


@api.route('maintenance/record/<record_id>/', methods=['GET', 'POST', 'DELETE'])
@login_required
def api_maintenance_record(record_id: int):
    if request.method == 'DELETE':
        record = Maintenance.query.filter_by(id=record_id).first()
        record.deleted = True
        db.session.commit()
        # TODO: Confirm they have permission to do this
        # Check to make sure they're allowed to delete and have confirmed it
        # Then delete thing

    return '{200: OKAY}'


def get_time(gps_update):
    time = str(gps_update.pop('time')).split('.')[0]
    if len(time) < 6:
        time = '0' + time
    date = datetime.date.today()
    return datetime.datetime(
        year=date.year,
        month=date.month,
        day=date.day,
        hour=int(time[0:2]),
        minute=int(time[2:4]),
        second=int(time[4:6]),
        tzinfo=datetime.timezone.utc
    ).astimezone(pytz.timezone('US/Eastern'))


@api.route('report.json', methods=['GET', 'POST'])
@login_required
def report():
    received_payload = request.json
    import json
    logger.info(f'Received Payload from user {current_user.email}'
                f'\nGPS Updates: {len(received_payload.get("gps", 0))}')
    # f'\nTIO Updates: {len(received_payload.get("tio", 0))}'
    # f'\nDHT Updates: {len(received_payload.get("dht", 0))}')
    # ---- Process GPS Updates ----
    return {'good': 'work'}
    gps_updates = received_payload.get('gps')
    for gps_update in gps_updates:
        dt = get_time(gps_update)
        data = GPSData(owner=current_user.id, time=dt, **gps_update)
        db.session.add(data)

    # ---- Process TomorrowIO Updates ----
    tio_updates = received_payload.get('tio')
    for tio_update in tio_updates:
        gps = tio_update.pop('gps')
        gps_time = get_time(gps)
        tio_time = (datetime.datetime.strptime(tio_update.pop('time'), '%Y-%m-%dT%H:%M:%SZ')
                    .replace(tzinfo=datetime.timezone.utc)
                    .astimezone(pytz.timezone('US/Eastern')))
        tio_data = TomorrowIO(owner=current_user.id, time=tio_time, **tio_update)
        tio_data.gps = GPSData(owner=current_user.id, time=gps_time, **gps)
        db.session.add(tio_data)

    # End the session
    db.session.commit()
    return {'good': 'work'}
