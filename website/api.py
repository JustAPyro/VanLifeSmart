from flask import Blueprint, request
from flask_login import login_required, current_user

from lutil import create_checkpoint
from .models import Maintenance
from . import db

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


sample = {
    'latitude': '?',
    'longitude': '?',
    'tomorrowIO': 'fillOnServer',
    'dhts': {
        'cabin': {
            'temperature': 32.4,
            'humidity': 43
        },
        'outdoor': {
            'temperature': 43.2,
            'humidity': 54
        }
    }

}


@api.route('update.json', methods=['GET', 'POST'])
@login_required
def status_update():
    latitude = request.json.get('latitude')
    longitude = request.json.get('longitude')
    print(longitude)
    print(request.json)
    if latitude[1] == 'S':
        latitude = latitude[0] * -1
    else:
        latitude = latitude[0]

    if longitude[1] == 'W':
        longitude = float(longitude[0]) * -1  # CAUSING A BUG????
    else:
        longitude = longitude[0]

    if request.method == 'POST':
        checkpoint = create_checkpoint(current_user, latitude, longitude, load_tio=False)
        db.session.add(checkpoint)
        db.session.commit()

        return '{200: OKAY}'
    return '{200: OKAY}'
