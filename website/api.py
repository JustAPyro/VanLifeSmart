from flask import Blueprint, request
from flask_login import login_required, current_user
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


@api.route('status/update/', methods=['GET', 'POST'])
@login_required
def status_update():
    return '{200: OKAY}'
