from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from .models import Mechanic, Maintenance, Checkpoint
from . import db
import requests
import os
from datetime import datetime

views = Blueprint('views', __name__)


@views.route('/')
@login_required
def home():
    return render_template('home.html', user=current_user)


@views.route('/status')
@login_required
def status():
    response = requests.get('https://api.tomorrow.io/v4/weather/realtime'
                            '?location=41.6206391,-85.826671'
                            f'&apikey={os.environ["TOMORROWAPI"]}')
    weather_data = response.json()['data']['values']
    weather_time = response.json()['data']['time']
    return render_template('status.html', user=current_user, gmkey=os.environ['GOOGLEAPI'],
                           coordinates='41.6206391,-85.826671',
                           weather_data=weather_data, weather_time=weather_time)


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


@views.route('/maintenance/post')
@login_required
def post_maintenance():
    return render_template('post_maintenance.html', user=current_user)


@views.route('/update/', methods=['GET', 'POST'])
@login_required
def update():

    # different kinds of art
    if request.method == 'POST':

        # Collect all data from the POST
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')
        data = {}

        # Collect all data from API's at this moment
        # Note that the following code makes extensive use of the drn method
        # This Dict Rename method just changes the name of the keys in the dict so I can
        # Easily unpack them into the constructor. This design choice was so that I could easily include
        # or not include them

        call_apis = True
        if call_apis:
            # TomorrowIO (Weather)
            # https: // docs.tomorrow.io / reference / realtime - weather
            response = requests.get('https://api.tomorrow.io/v4/weather/realtime'
                                    '?location=41.6206391,-85.826671'
                                    f'&apikey={os.environ["TOMORROWAPI"]}')
            weather_tomorrow_io = response.json()['data']['values']
            data['tio_cloud_base'] = weather_tomorrow_io['cloudBase']
            data['tio_cloud_ceiling'] = weather_tomorrow_io['cloudCeiling']
            data['tio_cloud_cover'] = weather_tomorrow_io['cloudCover']
            data['tio_dew_point'] = weather_tomorrow_io['dewPoint']
            data['tio_freezing_rain_intensity'] = weather_tomorrow_io['freezingRainIntensity']
            data['tio_humidity'] = weather_tomorrow_io['humidity']
            data['tio_precipitation_probability'] = weather_tomorrow_io['precipitationProbability']
            data['tio_pressure_surface_level'] = weather_tomorrow_io['pressureSurfaceLevel']
            data['tio_rain_intensity'] = weather_tomorrow_io['rainIntensity']
            data['tio_sleet_intensity'] = weather_tomorrow_io['sleetIntensity']
            data['tio_snow_intensity'] = weather_tomorrow_io['snowIntensity']
            data['tio_temperature'] = weather_tomorrow_io['temperature']
            data['tio_temperature_apparent'] = weather_tomorrow_io['temperatureApparent']
            data['tio_uv_health_concern'] = weather_tomorrow_io['uvHealthConcern']
            data['tio_uv_index'] = weather_tomorrow_io['uvIndex']
            data['tio_visibility'] = weather_tomorrow_io['visibility']
            data['tio_weather_code'] = weather_tomorrow_io['weatherCode']
            data['tio_wind_direction'] = weather_tomorrow_io['windDirection']
            data['tio_wind_gust'] = weather_tomorrow_io['windGust']
            data['tio_wind_speed'] = weather_tomorrow_io['windSpeed']
            print(data)
            print('Break----')
            print(weather_tomorrow_io)

        c = Checkpoint(
            latitude=latitude,
            longitude=longitude,
            **data
        )
        db.session.add(c)
        db.session.commit()
        return redirect(url_for('views.update'))

    return render_template('update.html', user=current_user)
