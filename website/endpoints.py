from flask import Blueprint, render_template, flash, request, redirect, url_for, Response
from geopy.geocoders import Nominatim
from models import User, GPSData, Vehicle, TomorrowIO
from werkzeug.security import generate_password_hash, check_password_hash
from website.database import db
from datetime import datetime, timezone
from geopy.exc import GeocoderTimedOut
from flask_login import login_user, logout_user, login_required, logout_user, current_user
from flask import abort

endpoints = Blueprint('endpoints', __name__)


@endpoints.route('/')
def landing_page():
    return render_template("landing.html", user=current_user)


@endpoints.route('/auth/sign-in.html', methods=['POST', 'GET'])
def sign_in_page():
    form = request.form
    if request.method == 'POST':
        email = request.form.get('email').strip().lower()
        password = request.form.get('password')
        user = db.session.query(User).filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                flash('Logged in successfully!', category='success')
                login_user(user, remember=('remember' in request.form))
                return redirect(url_for('endpoints.user_friends'))
            else:
                flash('Incorrect email or password.', category='error')
        else:
            flash('Email does not exist.', category='error')
    return render_template("sign-in.html", user=current_user, form=form)


@endpoints.route('/auth/sign-up.html', methods=['POST', 'GET'])
def sign_up_page():
    form = request.form
    if request.method == 'POST':
        name = request.form.get('name')
        username = request.form.get('username')
        email = request.form.get('email').strip().lower()
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')

        if db.session.query(User).filter_by(email=email).first():
            flash('Email already exists', category='error')
        elif db.session.query(User).filter_by(username=username).first():
            flash('Username already exists', category='error')
        elif len(name) < 2:
            flash('Name must be greater than 1 character.', category='error')
        elif len(email) < 4:
            flash('Email must be greater than 3 characters.', category='error')
        elif password != password_confirm:
            flash('Password does not match confirmation', category='error')
        elif len(password) < 7:
            flash('Password must be at least 7 characters.', category='error')
        else:
            new_user = User(email=email, username=username, password=generate_password_hash(password, method='pbkdf2'))
            db.session.add(new_user)
            db.session.commit()

            flash('Account created', category='success')
            login_user(new_user)
            return redirect(url_for('endpoints.user_friends'))
    return render_template('sign-up.html', 
                           user=current_user,
                           form=form)

@endpoints.route('/auth/sign-out.html')
@login_required
def log_out_page():
    logout_user()
    return redirect(url_for('endpoints.sign_in_page'))

@endpoints.route('/api/heartbeat.json', methods=['POST'])
def receive_heartbeat():
    # Get the data from the heartbeat
    data = request.get_json()

    # Attempt to find a user with email provided, if none found issue malformed 400
    user = db.session.query(User).filter_by(email=data['email']).first()
    if not user:
        return Response(f'No user found under email provided ({data["email"]})', status=400)

    # Attempt to find a vehicle with the name provided, if none found issue malformed 400
    vehicle = db.session.query(Vehicle).filter_by(name=data['vehicle_name']).first()
    if not vehicle:
        return Response(f'No vehicle found with name provided ({data["vehicle_name"]})', status=400)

    # Update the vehicle heartbeat
    vehicle.last_heartbeat = datetime.now(timezone.utc)
    vehicle.next_expected_heartbeat = datetime.fromisoformat(data['next_heartbeat'])

    # Process the gps points first, since other points may refer to these
    gps_mappings = {}
    response = {'received': {'gps': [], 'tio': []}}
    for gps_data in data['database']['gps']['data']:
        # Create a dictionary so that we can mutate it for the new database
        gps_dict = dict(zip(data['database']['gps']['headers'], gps_data))

        # Remove the old key but save it, so we can track changes
        old_id = gps_dict.pop('id')

        # Assign a user id, parse the datetime, and check for any None values
        gps_dict['owner_id'] = user.id
        gps_dict['utc_time'] = datetime.strptime(gps_dict['utc_time'], '%Y-%m-%d %H:%M:%S')
        for key in gps_dict.keys():
            if gps_dict[key] == 'None':
                gps_dict[key] = None

        # Create the database object and insert/update the db
        gps = GPSData(**gps_dict)
        db.session.add(gps)
        db.session.flush()

        # Map the new id to the old id and update the received response
        gps_mappings[old_id] = gps.id
        response['received']['gps'].append(old_id)
    # Load tio updates
    for tio_data in data['database']['tio']['data']:
        # Create dict to make mutating easier
        tio_dict = dict(zip(data['database']['tio']['headers'], tio_data))

        # Remove the id and add it to the received response
        response['received']['tio'].append(tio_dict.pop('id'))

        # Update the owner id and the new gps id as well as parsing the time
        tio_dict['owner_id'] = user.id
        tio_dict['gps_id'] = gps_mappings[tio_dict['gps_id']]
        tio_dict['utc_time'] = datetime.strptime(tio_dict['utc_time'], '%Y-%m-%d %H:%M:%S')
        for key in tio_dict.keys():
            if tio_dict[key] == 'None':
                tio_dict[key] = None
            if tio_dict[key] == 'True':
                tio_dict[key] = True
            if tio_dict[key] == 'False':
                tio_dict[key] = False

        # Create object and add to db
        tio = TomorrowIO(**tio_dict)
        db.session.add(tio)

    db.session.commit()
    return response


def get_location_string(latitude, longitude):
    # Create the geolocator object (See geo.py)
    geolocator = Nominatim(user_agent=__name__)

    # Default name will return just latitude and longitude
    name = f'{latitude}, {longitude}'
    try:
        # Attempt to get a nicer name from the geolocator
        name = geolocator.reverse((latitude, longitude))
    except GeocoderTimedOut as e:
        pass

    return name



@endpoints.route('/vehicle/<vehicle_name>.html', methods=['GET'])
@login_required
def vehicle_page(vehicle_name: str):
    permissions = {
        'view_connected': True,
        'view_heartbeat': True,
        'view_location': True,
        'view_weather': True,
    }

    vehicle = db.session.query(Vehicle).filter_by(name=vehicle_name).first()
    context = {}

    # If permission
    if permissions['view_connected'] and vehicle.next_expected_heartbeat:
        # If now is sooner than the next heartbeat, we assumed connection is valid
        context['connected'] = vehicle.next_expected_heartbeat > datetime.utcnow()
    # TODO: If the database is new this can crash
    if vehicle.last_heartbeat and vehicle.next_expected_heartbeat:
        context['period'] = vehicle.next_expected_heartbeat - vehicle.last_heartbeat

    if permissions['view_heartbeat']:
        context['heartbeat'] = {
            'last': vehicle.last_heartbeat,
            'next': vehicle.next_expected_heartbeat,
            'now': datetime.utcnow()
        }

    if permissions['view_location'] and vehicle.owner.gps_data:

        # Get the last gps data this user has logged
        gps = vehicle.owner.gps_data[-1]

        context['location'] = gps.as_dict()

        # Try to parse the location name information
        context['location']['location'] = get_location_string(gps.latitude, gps.longitude)


    if permissions['view_weather'] and vehicle.owner.tio_data:
        # Add the weather data to the context
        weather = vehicle.owner.tio_data[-1]
        context['weather'] = weather.as_dict()

        # Try to add the nice name of location
        loc = weather.gps_data
        context['weather']['location'] = get_location_string(loc.latitude, loc.longitude)

    return render_template(
        'vehicle/home.html',
        user=current_user,
        vehicle=vehicle,
        permissions=permissions,
        **context,
    )



@endpoints.route('/vehicle/<vehicle_name>/heartbeat.html')
@login_required
def vehicle_heartbeat_page(vehicle_name: str):
    vehicle = db.session.query(Vehicle).filter_by(name=vehicle_name).first()
    return render_template(
        'vehicle/heartbeat.html',
        user=current_user,
        vehicle=vehicle,
    )


@endpoints.route('/vehicle/<vehicle_name>/location.html')
@login_required
def vehicle_location_page(vehicle_name: str):
    vehicle = db.session.query(Vehicle).filter_by(name=vehicle_name).first()
    if not vehicle:
       abort(404) 

    return render_template(
        'vehicle/location.html',
        user=current_user,
        vehicle=vehicle,
    )


@endpoints.route('/user/friends.html', methods=['GET', 'POST'])
@login_required
def user_friends():
    if request.method == 'POST':
        uname = request.form.get('username')
        user = db.session.query(User).filter_by(username=uname).first()
        if not user:
            flash('Sorry, no users have this username.', category='error')
        if user:
            flash(f'Followed {uname}', category='success')
            current_user.follows.append(user)
            db.session.commit()

        return redirect(url_for('endpoints.user_friends'))

    return render_template('friends.html', 
                           user=current_user,
                           following=current_user.follows)
