from flask.templating import render_template
from flask import Flask, request, redirect, url_for, session, flash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret'


@app.route('/')
def hello_world():
    return render_template("landing.html")


@app.route('/auth/sign-in.html', methods=['POST', 'GET'])
def sign_in_page():
    return render_template("sign-in.html")


@app.route('/auth/sign-up.html', methods=['POST', 'GET'])
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


@app.route('/user/<user_id>/friends.html')
def user_friends(user_id: int):
    return render_template('friends.html')


if __name__ == '__main__':
    app.run(debug=True)
