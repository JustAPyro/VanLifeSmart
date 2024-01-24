from flask import Flask


def create_app():
    # Setup Flask
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'secret'

    return app
