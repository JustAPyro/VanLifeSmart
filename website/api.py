import os

import requests
from flask import Blueprint, request
from flask_login import login_required, current_user

from .models import Maintenance, Checkpoint, DHTSensor, TomorrowIO
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


@api.route('update/', methods=['GET', 'POST'])
@login_required
def status_update():
    data_latitude = 0
    data_longitude = 0

    if request.method == 'POST':
        checkpoint = Checkpoint(
            latitude=data_latitude,
            longitude=data_longitude,)


        db.session.add(checkpoint)
        db.session.flush()

        # If this is marked as live we want to do some extra processing server side
        live = True
        if live:
            response = requests.get('https://api.tomorrow.io/v4/weather/realtime'
                                    f'?location={data_latitude},{data_longitude}'
                                    f'&apikey={os.environ["TOMORROWAPI"]}')
            tio_data = response.json()['data']['values']
            tio = TomorrowIO(
                uv_index=tio_data['uvIndex'],
                humidity=tio_data['humidity'],
                wind_gust=tio_data['windGust'],
                dew_point=tio_data['dewPoint'],
                cloud_base=tio_data['cloudBase'],
                wind_speed=tio_data['windSpeed'],
                visibility=tio_data['visibility'],
                cloud_cover=tio_data['cloudCover'],
                temperature=tio_data['temperature'],
                weather_code=tio_data['weatherCode'],
                cloud_ceiling=tio_data['cloudCeiling'],
                rain_intensity=tio_data['rainIntensity'],
                snow_intensity=tio_data['snowIntensity'],
                wind_direction=tio_data['windDirection'],
                sleet_intensity=tio_data['sleetIntensity'],
                uv_health_concern=tio_data['uvHealthConcern'],
                temperature_apparent=tio_data['temperatureApparent'],
                pressure_surface_level=tio_data['pressureSurfaceLevel'],
                freezing_rain_intensity=tio_data['freezingRainIntensity'],
                precipitation_probability=tio_data['precipitationProbability'],
            )



        return '{200: OKAY}'
    return '{200: OKAY}'

