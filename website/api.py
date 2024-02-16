import json

from flask import Blueprint, request
from flask_login import login_required, current_user

from lutil import create_checkpoint
from .models import Maintenance
from . import db
import logging
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


@api.route('update.json', methods=['GET', 'POST'])
@login_required
def status_update():
    latitude = request.json.get('latitude')
    longitude = request.json.get('longitude')
    logger.info(f'---------- Update ----------'
                f'Status update from {current_user.email} at {request.remote_addr} with the following payload:\n'
                f'{json.dumps(request.json, sort_keys=True, indent=4, separators=(",", ":"))}')

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
