from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from .models import Mechanic, Maintenance, TomorrowIO
from . import db
import requests
import folium
import os
from datetime import datetime
import logging

logger = logging.getLogger('funmobile_server')
views = Blueprint('views', __name__)


@views.route('/')
@login_required
def home():
    return render_template('home.html', user=current_user)


@views.route('/status')
@login_required
def status():
    # response = requests.get('https://api.tomorrow.io/v4/weather/realtime'
    #                        '?location=41.6206391,-85.826671'
    #                        f'&apikey={os.environ["TOMORROWAPI"]}')
    # d = response.json()
    # print(d)
    weather_data = {}  # response.json()['data']['values']
    weather_time = {}  # response.json()['data']['time']

    temp_chart = {
        'labels': [1, 2, 3, 4],
        'tio': [1, 2, 3, 4],
        'tio_apparent': [1, 2, 3, 4]
    }

    return render_template('status.html', user=current_user, gmkey=os.environ['GOOGLEAPI'],
                           coordinates='41.6206391,-85.826671',
                           weather_data=weather_data, weather_time=weather_time,
                           temp_chart=temp_chart)


@views.route('/maintenance', methods=['GET', 'POST'])
@login_required
def maintenance():
    if request.method == 'POST':

        if request.form['submit'] == 'newMechanic':
            mechanicName = request.form.get('mechanicName')
            email = request.form.get('email')
            phone = request.form.get('phone')
            street = request.form.get('street')

            if not mechanicName:
                flash('Please supply mechanic name.')
            if not email or phone:
                flash('Please supply either email or phone.')
            if len(request.form.get('state')) < 3:
                flash('Please enter state as 2 characters.')

            m = Mechanic(
                name=request.form.get('mechanicName'),
                owner=current_user.id,
                email=request.form.get('email'),
                phone=request.form.get('phone'),
                street=request.form.get('street'),
                city=request.form.get('city'),
                state=request.form.get('state'),
                zip=request.form.get('zip')
            )

            db.session.add(m)
            db.session.commit()
            flash('Mechanic registered!')
            return redirect(url_for('views.maintenance'))

        elif request.form['submit'] == 'newRecord':
            # Verify
            mechanic_id = request.form.get('mechanicSelected')
            cost_invoiced = int(float(request.form.get('invoiceCost')) * 100)
            date_invoiced = datetime.strptime(request.form.get('date'), '%m/%d/%Y')
            description_of_work = request.form.get('descriptionOfWork')
            nm = Maintenance(
                mechanic_id=mechanic_id,
                owner=current_user.id,
                cost_invoiced=cost_invoiced,
                invoice_number=request.form.get('invoiceNumber'),
                date_invoiced=date_invoiced,
                mileage=request.form.get('mileage'),
                description_of_work=description_of_work
            )

            db.session.add(nm)
            db.session.commit()
            return redirect(url_for('views.maintenance'))

    print(current_user.mechanics)
    return render_template('maintenance.html',
                           user=current_user,
                           mechanic_map={mechanic.id: mechanic for mechanic in current_user.mechanics})


@views.route('/map')
@login_required
def view_map():
    positions = [(getattr(data, 'latitude'), getattr(data, 'longitude') * -1) for data in current_user.gps_data]

    map_view = folium.Map(
        location=positions[-1]
    )

    folium.PolyLine(positions,
                    color='red',
                    weight=5,
                    opacity=1).add_to(map_view)

    return map_view._repr_html_()


@views.route('/maintenance/post')
@login_required
def post_maintenance():
    return render_template('post_maintenance.html', user=current_user)


@views.route('/update/', methods=['GET', 'POST'])
@login_required
def update():
    # different kinds of art
    if request.method == 'POST':
        logger.info(f'Post Update with payload: {request.json()}')
        print(request.json())
        # Collect all data from the POST
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')

        checkpoint = Checkpoint(
            owner=current_user.id,
            latitude=latitude,
            longitude=longitude,
        )

        # TomorrowIO (Weather)
        # https: // docs.tomorrow.io / reference / realtime - weather
        response = requests.get('https://api.tomorrow.io/v4/weather/realtime'
                                f'?location={checkpoint.latitude},{checkpoint.longitude}'
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
        checkpoint.tio = tio

        db.session.add(checkpoint)
        db.session.commit()
        return redirect(url_for('views.update'))

    return render_template('update.html', user=current_user)
