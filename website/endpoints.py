from flask import Blueprint, render_template, flash, request, redirect, url_for
from models import User
from werkzeug.security import generate_password_hash, check_password_hash
from database import db
from flask_login import login_user, login_required, logout_user, current_user

endpoints = Blueprint('endpoints', __name__)


@endpoints.route('/')
def landing_page():
    return render_template("landing.html")


@endpoints.route('/auth/sign-in.html', methods=['POST', 'GET'])
def sign_in_page():
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
    return render_template("sign-in.html")


@endpoints.route('/auth/sign-up.html', methods=['POST', 'GET'])
def sign_up_page():
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
    return render_template('sign-up.html')


@endpoints.route('/user/friends.html')
def user_friends():
    return render_template('friends.html')
