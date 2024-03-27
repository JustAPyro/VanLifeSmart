import os

from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from website.database import db
from models import Base, User
from flask_login import LoginManager

def create_app():
    application = Flask(__name__)
    application.config['SECRET_KEY'] = 'secret'
    application.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('VLS_DATABASE_URI')
    db.init_app(application)

    from website.endpoints import endpoints
    application.register_blueprint(endpoints, url_prefix='/')

    with application.app_context():
        db.create_all()

    login_manager = LoginManager()
    login_manager.login_view = 'endpoints.sign_in_page'
    login_manager.init_app(application)

    @login_manager.user_loader
    def load_user(id: int):
        return db.session.get(User, id)

    return application


if __name__ == '__main__':
    create_app().run()
