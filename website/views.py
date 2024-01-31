from flask import Blueprint, render_template
from flask_login import login_required, current_user
import requests
import os

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
    return render_template('status.html', user=current_user, gmkey=os.environ['GOOGLEAPI'], coordinates='41.6206391,-85.826671',
                           weather_data=weather_data, weather_time=weather_time)
