from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from os import path

import os
from dotenv import load_dotenv


db = SQLAlchemy()
migrate = Migrate()
DB_NAME = 'database.db'

# Load environment variables from hidden .env file
load_dotenv()

def create_app():
    # Setup Flask
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'secret'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'

    # Setup database
    db.init_app(app)

    # Set up database versioning/migration
    migrate.init_app(app, db)

    # Import / Register all views
    from .views import views
    from .auth import auth
    from .api import api
    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')
    app.register_blueprint(api, url_prefix='/api/')

    # Create the database
    from .models import User, Checkpoint
    create_database(app)

    # Set up the login manager for flask
    login_manager = LoginManager()
    login_manager.login_view = 'auth.log_in'
    login_manager.init_app(app)

    # Define a way to load users for the login manager
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    return app


def create_database(app):
    if not path.exists('website/' + DB_NAME):
        with app.app_context():
            db.create_all()
