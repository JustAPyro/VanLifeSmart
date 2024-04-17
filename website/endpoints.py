from flask import Blueprint, render_template, flash, request, redirect, url_for, Response
import json
import math
from datetime import timedelta
from geopy.geocoders import Nominatim
from models import User, GPSData, Vehicle, TomorrowIO, Heartbeat, Pitstop, Follow, Role
from werkzeug.security import generate_password_hash, check_password_hash
from website.database import db
from website.notifications import send_gas_email
from datetime import datetime, timezone
from geopy.exc import GeocoderTimedOut
from flask_login import login_user, logout_user, login_required, logout_user, current_user
from flask import abort
from sqlalchemy import desc, and_
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
                return redirect(url_for('endpoints.user_following'))
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
            return redirect(url_for('endpoints.user_following'))
    return render_template('sign-up.html', 
                           user=current_user,
                           form=form)

@endpoints.route('/auth/sign-out.html')
@login_required
def log_out_page():
    logout_user()
    return redirect(url_for('endpoints.sign_in_page'))

@endpoints.route('/api/heartbeat.json', methods=['GET', 'POST'])
def receive_heartbeat():
    if request.method == 'GET':
        return ('', 204)
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
    response = {'received': {'gps': [], 'tio': [], 'heartbeat': []}}
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

    for heartbeat_data in data['database']['heartbeat']['data']:
        heartbeat_dict = dict(zip(data['database']['heartbeat']['headers'], heartbeat_data))
        response['received']['heartbeat'].append(heartbeat_dict.pop('id'))
        heartbeat_dict['vehicle_id'] = vehicle.id
        heartbeat_dict['time_utc'] = datetime.fromisoformat(heartbeat_dict['time_utc'])
        heartbeat_dict['next_time'] = datetime.fromisoformat(heartbeat_dict['next_time'])
        
        heartbeat_dict['server'] = True if heartbeat_dict['server'] == 'True' else False
        heartbeat_dict['internet'] = True if heartbeat_dict['internet'] =='True' else False
        heartbeat_dict['on_schedule'] = True if heartbeat_dict['on_schedule'] == 'True' else False
        
        heartbeat = Heartbeat(**heartbeat_dict)
        db.session.add(heartbeat)
        

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

def can_access(user: User, vehicle: Vehicle):
    if vehicle.owner == user:
        return True

    follow = db.session.query(Follow).filter(
        and_(
            Follow.user_id == current_user.id,
            Follow.vehicle_id == vehicle.id
        )
    ).first()

    if follow == None or follow.role == None:
        return False
    else:
        return True

@endpoints.route('/vehicle.html', methods=['GET', 'POST'])
@login_required
def create_vehicle_page():

    if request.method == 'POST': 
        vehicle_name = request.form.get('vehicle_name')
        if not vehicle_name or len(vehicle_name) < 2:
            flash('Please enter a vehicle name greater than 1 character.', category='error')
        elif db.session.query(Vehicle).filter_by(name=vehicle_name).first() != None:
            flash('There is already a vehicle registered under this name!', category='error')
        else:
            db.session.add(Vehicle(
                name=vehicle_name,
                owner_id=current_user.id
            ))
            db.session.commit()
            flash('Created new vehicle!', category='success')
            return redirect(url_for('endpoints.create_vehicle_page'))

    return render_template(
        'vehicle/create.html',
        user=current_user,
    )

@endpoints.route('/vehicle/<vehicle_name>.html', methods=['GET'])
@login_required
def vehicle_page(vehicle_name: str):
    
    # First try to find the vehicle
    vehicle = db.session.query(Vehicle).filter_by(name=vehicle_name).first()

    if not vehicle: # TODO: Better 404
        return ('Could not find vehicle', 404)
    if not can_access(current_user, vehicle):
        return ('Unauthorized', 403)

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

    if permissions['view_location'] and vehicle.gps_data:

        # Get the last gps data this user has logged
        gps = vehicle.gps_data[-1]

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

@endpoints.route('/vehicle/<vehicle_name>/pitstop.html', methods=['GET', 'POST'])
@login_required
def vehicle_pitstop_page(vehicle_name: str):
    # TODO: Error handling here
    vehicle = db.session.query(Vehicle).filter_by(name=vehicle_name).first()

    if request.method == 'POST':
        # TODO: Validate
        ps = Pitstop(
            vehicle_id=vehicle.id,
            gallons_filled=request.form.get('gallons_filled'),
            total_cost=request.form.get('total_cost'),
            mileage=request.form.get('mileage'),
            filled=bool('filled' in request.form)
                        
        )
        db.session.add(ps)
        db.session.commit()
        send_gas_email('Luke', ps)
        return redirect(url_for('endpoints.vehicle_pitstop_page', vehicle_name=vehicle_name))



    return render_template('vehicle/pitstop.html',
                           user=current_user,
                           vehicle=vehicle)

@endpoints.route('/vehicle/<vehicle_name>/heartbeat.html')
@login_required
def vehicle_heartbeat_page(vehicle_name: str):
    vehicle = db.session.query(Vehicle).filter_by(name=vehicle_name).first()

    heartbeats = db.session.query(Heartbeat).order_by(desc('time_utc')).all()
    connection_health = []
        
    hours_back = 12

    for i, hb in enumerate(heartbeats):
        if hb.on_schedule == False:
            if i == len(heartbeats)-1:
                continue

            missing_entries = (hb.time_utc - heartbeats[i+1].time_utc) / timedelta(seconds=30)
            for _ in range(math.floor(missing_entries)):
                connection_health.append((hb.time_utc, False, False, False, 'ADDED'))

        connection_health.append((hb.time_utc, True, hb.internet, hb.server))
    health = {0: {'offline': 0, 'no_server': 0, 'no_internet': 0, 'online': 0}}
    hour = 0
    now = datetime.now()
    while hour < 6:
        for hb in connection_health:
            if hb[0] < now - timedelta(hours=hour):
                hour += 1
                health[hour] = {'offline': 0, 'no_server': 0, 'no_internet': 0, 'online': 0}

            if hb[1] == False:
                health[hour]['offline'] += 1
            elif hb[2] == False:
                health[hour]['no_internet'] += 1
            elif hb[3] == False:
                health[hour]['no_server'] += 1
            elif hb[1] and hb[2] and hb[3]:
                health[hour]['online'] += 1
            else:
                raise Exception
        break


    for hour, status in health.items():
        total = status['offline'] + status['no_server'] + status['no_internet'] + status['online']
        if total == 0:
            continue
        status['online'] = (status['online']/total) * 100
        status['offline'] = (status['offline']/total) * 100
        status['no_server'] = (status['no_server']/total) * 100
        status['no_internet'] = (status['no_internet']/total) * 100

    chart_health = {
        'offline': [],
        'no_server': [],
        'no_internet': [],
        'online': []
    }
    # This goes 5, 4, 3, 2, 1, 0
    for i in range(6, 0, -1):
        for state in ('offline', 'no_server', 'no_internet', 'online'):
            chart_health[state].append(health[i][state] if i in health else 0)


    return render_template(
        'vehicle/heartbeat.html',
        health=health,
        chart_health=chart_health,
        user=current_user,
        vehicle=vehicle,
    )

@endpoints.route('/vehicle/<vehicle_name>/followers.html', methods=['GET', 'POST'])
@login_required
def vehicle_follower_page(vehicle_name: str):
    vehicle = db.session.query(Vehicle).filter_by(name=vehicle_name).first()
    
    if not vehicle:
        abort(404)

    if vehicle.owner.id != current_user.id:
        return ('You must own the vehicle to access this page', 403)

    if request.method == 'POST':

        if 'delete_form' in request.form:
            # TODO: ADD SOME CHECKS here
            db.session.query(Role).filter(Role.id == request.form.get('delete_form')).delete()
            db.session.commit()
            return redirect(url_for('endpoints.vehicle_follower_page', vehicle_name=vehicle.name))


        r_name = request.form.get('role_name')

        if r_name == None or len(r_name) < 2:
            flash('Role name is required and must be greater than one character.', category='error')
        elif db.session.query(Role).filter(Role.name == r_name).first() is not None:
            flash('You\'ve arlready created a role with that name!', category='error')
        else:
            db.session.add(Role(
                name=r_name,
                vehicle_id=vehicle.id,
                view_location='view_location' in request.form,
                view_weather='view_weather' in request.form,
                view_heartbeat='view_heartbeat' in request.form,
                write_heartbeat='write_heartbeat' in request.form,
                view_gas='view_gas' in request.form,
                email_gas='email_gas' in request.form,
            ))
            db.session.commit()
            return redirect(url_for('endpoints.vehicle_follower_page', vehicle_name=vehicle.name))

    return render_template(
        'vehicle/followers.html',
        user=current_user,
        vehicle=vehicle,
    )

@endpoints.route('/vehicle/<vehicle_name>/location.html')
@login_required
def vehicle_location_page(vehicle_name: str):
    vehicle = db.session.query(Vehicle).filter_by(name=vehicle_name).first()
    if not vehicle:
       abort(404) 
    
    path = [[gps.latitude, gps.longitude] for gps in vehicle.owner.gps_data]
    return render_template(
        'vehicle/location.html',
        locations=path,
        user=current_user,
        vehicle=vehicle,
    )


@endpoints.route('/settings.html', methods=['GET', 'POST'])
@login_required
def settings_page():
    
    return render_template(
        'user/settings.html',
        user=current_user,
    )

@endpoints.route('/user/following.html', methods=['GET', 'POST'])
@login_required
def user_following():
    if request.method == 'POST':
        vname = request.form.get('vehicle_name')
        vehicle = db.session.query(Vehicle).filter_by(name=vname).first()
        if not vehicle:
            flash(f'Sorry, no vehicles are registered as "{vname}"', category='error')
        elif current_user.follows is not None and vehicle.id in [v.vehicle_id for v in current_user.follows]:
            flash(f'You are already following "{vname}"', category='error')
        else:
            db.session.add(Follow(
                user_id=current_user.id,
                vehicle_id=vehicle.id
            ))
            db.session.commit()
            flash(f'Followed {vname}!')
            return redirect(url_for('endpoints.user_following'))

    return render_template('user/following.html', user=current_user)

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

        return redirect(url_for('endpoints.user_friends'))

    vehicle_permission_ids = {}
    if current_user.vehicle_permissions:
        vehicle_permission_ids = [permission.owner.id for permission in current_user.vehicle_permissions]
    
    following = {}
    for friend in current_user.follows:
        vehicles = []

        for vehicle in friend.vehicles:
            if vehicle.id in vehicle_permission_ids:

                vehicles.append(vehicle)

        following[friend] = vehicles
        



    return render_template('friends.html', 
                           user=current_user,
                           following=following)
