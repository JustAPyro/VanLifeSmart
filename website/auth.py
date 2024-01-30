from flask import Blueprint, render_template, request, flash

auth = Blueprint('auth', __name__)


@auth.route('/log-in', methods=['GET', 'POST'])
def log_in():
    return render_template('log_in.html')


@auth.route('/log-out')
def log_out():
    return '<p>Logged out</p>'


@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        email = request.form.get('email')
        name = request.form.get('givenName')
        password = request.form.get('password')
        confirmPassword = request.form.get('confirmPassword')
        token = request.form.get('token')
        if len(email) < 4:
            flash('Email must be greater than 4 characters.', category='error')
        elif len(name) < 2:
            flash('Given name bust be greater than 2 characters.', category='error')
        elif password != confirmPassword:
            flash('Passwords don\'t match.', category='error')
        elif len(password) < 7:
            flash('Password must be at least 7 characters.', category='error')
        else:
            # add user
            flash('Account created!', category='success')
    return render_template('sign_up.html')
