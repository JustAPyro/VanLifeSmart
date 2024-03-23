from flask import Blueprint, render_template, flash, request, redirect, url_for, Response
from models import User, GPSData, Vehicle
from werkzeug.security import generate_password_hash, check_password_hash
from database import db
from datetime import datetime, timezone
from flask_login import login_user, login_required, logout_user, current_user

endpoints = Blueprint('endpoints', __name__)


@endpoints.route('/')
def landing_page():
    return render_template("landing.html")


@endpoints.route('/auth/sign-in.html', methods=['POST', 'GET'])
def sign_in_page():
    form = request.form
    if request.method == 'POST':
        email = request.form.get('email')
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
    return render_template("sign-in.html", form=form)


@endpoints.route('/auth/sign-up.html', methods=['POST', 'GET'])
def sign_up_page():
    form = request.form
    if request.method == 'POST':
        name = request.form.get('name')
        username = request.form.get('username')
        email = request.form.get('email')
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
    return render_template('sign-up.html', form=form)


@endpoints.route('/api/heartbeat.json', methods=['POST'])
def receive_heartbeat():
    data = request.get_json()

    user = db.session.query(User).filter_by(email=data['email']).first()
    if not user:
        return Response(f'No user found under email provided ({data["email"]})', status=400)

    vehicle = db.session.query(Vehicle).filter_by(name=data['vehicle_name']).first()
    if not vehicle:
        return Response(f'No vehicle found with name provided ({data["vehicle_name"]})', status=400)
    
    vehicle.last_heartbeat = datetime.now(timezone.utc)

    received = {'gps': []}

    gps_headers = data['gps']['headers']
    all_gps_data = data['gps']['data']
    for gps_data in all_gps_data:
        # Create a dict with headers and values for this row
        gps_dict = dict(zip(gps_headers, gps_data)) 
        received['gps'].append(gps_dict['id'])
        gps_dict.pop('id')
        gps_dict['owner_id'] = user.id
        gps_dict['utc_time'] = datetime.strptime(gps_dict['utc_time'], '%Y-%m-%d %H:%M:%S')
        for key in gps_dict.keys():
            if gps_dict[key] == 'None':
                gps_dict[key] = None
        gps = GPSData(**gps_dict)
        db.session.add(gps)
    db.session.commit()
    return received


@endpoints.route('/vehicle/<vehicle_name>.html', methods=['GET'])
@login_required
def vehicle_page(vehicle_name: str):
    return f'Hello! Welcome to {vehicle_name}\'s official page!'


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

    return render_template('friends.html', following=current_user.follows)
