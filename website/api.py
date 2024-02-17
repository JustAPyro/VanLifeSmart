import logging
import datetime

from flask import Blueprint, request
from flask_login import login_required, current_user

from .auth import authorize_user
from .models import Maintenance, GPSData
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
def report():
    user = request.authorization.username
    password = request.authorization.password
    if not authorize_user(user, password):
        return {'Error': 'Unauthorized'}
    received_payload = request.json

    # Process gps into DB entries
    gps_updates = received_payload.get('gps')
    for gps_update in gps_updates:
        dt = datetime.datetime.utcfromtimestamp(gps_update.pop('utc_time'))
        data = GPSData(owner=current_user.id, time=dt, **gps_update)
        db.session.add(data)

    print(gps_updates)

    print('Recieved: ' + str(request.json))
    # End the sesion
    db.session.commit()
    return {'good': 'work'}
