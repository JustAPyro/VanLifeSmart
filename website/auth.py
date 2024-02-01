from flask import Blueprint, render_template, request, flash, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from .models import User
from . import db
from flask_login import login_user, login_required, logout_user, current_user
from .lutil import normalize_email
auth = Blueprint('auth', __name__)


@auth.route('/log-in', methods=['GET', 'POST'])
def log_in():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        email = normalize_email(email)
        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                flash('Logged in successfully!', category='success')
                login_user(user, remember=True)
                return redirect(url_for('views.home'))
            else:
                flash('Incorrect password, try again or contact support.', category='error')
        else:
            flash('Email does not exist.', category='error')

    return render_template('log_in.html', user=current_user)


@auth.route('/log-out')
@login_required
def log_out():
    logout_user()
    return redirect(url_for('auth.log_in'))



@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        email = request.form.get('email')
        name = request.form.get('givenName')
        password = request.form.get('password')
        confirmPassword = request.form.get('confirmPassword')
        token = request.form.get('token')

        # Try to find a user with the existing email
        email = normalize_email(email)
        user = User.query.filter_by(email=email)

        if user:
            flash('Email already in use. Please log in.', category='error')
        elif len(email) < 4:
            flash('Email must be greater than 4 characters.', category='error')
        elif len(name) < 2:
            flash('Given name bust be greater than 2 characters.', category='error')
        elif password != confirmPassword:
            flash('Passwords don\'t match.', category='error')
        elif len(password) < 7:
            flash('Password must be at least 7 characters.', category='error')
        else:
            new_user = User(
                email=email,
                name=name,
                password=generate_password_hash(password))
            db.session.add(new_user)
            db.session.commit()

            flash('Account created!', category='success')
            login_user(user, remember=True)
            return redirect(url_for('views.home'))

    return render_template('sign_up.html')
