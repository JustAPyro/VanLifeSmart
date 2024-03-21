from flask import Blueprint, render_template, flash, request

endpoints = Blueprint('endpoints', __name__)


@endpoints.route('/')
def landing_page():
    return render_template("landing.html")


@endpoints.route('/auth/sign-in.html', methods=['POST', 'GET'])
def sign_in_page():
    return render_template("sign-in.html")


@endpoints.route('/auth/sign-up.html', methods=['POST', 'GET'])
def sign_up_page():
    if request.method == 'POST':
        name = request.form.get('name')
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')

        if len(name) < 2:
            flash('Name must be greater than 1 character.', category='error')
        elif len(email) < 4:
            flash('Email must be greater than 3 characters.', category='error')
        elif password != password_confirm:
            flash('Password does not match confirmation', category='error')
        elif len(password) < 7:
            flash('Password must be at least 7 characters.', category='error')
        else:
            flash('Account created', category='success')
    return render_template('sign-up.html')


@endpoints.route('/user/<user_id>/friends.html')
def user_friends(user_id: int):
    return render_template('friends.html')
