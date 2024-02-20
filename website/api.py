import logging
import datetime
import pytz

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


@api.route('report.json', methods=['GET', 'POST'])
@login_required
def report():
    received_payload = request.json
    print(f'payload: {received_payload}')
    # ---- Process GPS Updates ----
    gps_updates = received_payload.get('gps')
    for gps_update in gps_updates:
        time = str(gps_update.pop('utc_time')).split('.')[0]
        if len(time) < 6:
            time = '0' + time
        date = datetime.date.today()
        dt = datetime.datetime(
            year=date.year,
            month=date.month,
            day=date.day,
            hour=int(time[0:2]),
            minute=int(time[2:4]),
            second=int(time[4:6]),
            tzinfo=datetime.timezone.utc
        ).astimezone(pytz.timezone('US/Eastern'))
        print(dt)
        data = GPSData(owner=current_user.id, time=dt, **gps_update)
        db.session.add(data)

    # ---- Process TomorrowIO Updates ----
    tio_updates = received_payload.get('tio')
    for tio_update in tio_updates:
        tio_data = TomorrowIO(owner=current_user.id, **tio_update)
        db.session.add(tio_data)

    # End the session
    db.session.commit()
    return {'good': 'work'}
