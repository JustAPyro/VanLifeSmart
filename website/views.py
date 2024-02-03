from flask import Blueprint, render_template, request, flash
from flask_login import login_required, current_user
from .models import Mechanic, Maintenance
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

        elif request.form['submit'] == 'newRecord':
            # Verify
            mechanic_id = request.form.get('mechanicSelected')
            cost_invoiced = int(float(request.form.get('invoiceCost')) * 100)
            date_invoiced = datetime.strptime(request.form.get('date'), '%m/%d/%Y')
            description_of_work = request.form.get('descriptionOfWork')
            print(description_of_work)
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
    print(current_user.mechanics)
    return render_template('maintenance.html',
                           user=current_user,
                           mechanic_map={mechanic.id: mechanic for mechanic in current_user.mechanics})


@views.route('/maintenance/post')
@login_required
def post_maintenance():
    return render_template('post_maintenance.html', user=current_user)


@views.route('/push')
@login_required
def push():
    return render_template('push.html', user=current_user)
