import os
import base64
from werkzeug.security import check_password_hash

from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from website.database import db
from models import Base, User
from flask_login import LoginManager
from website.filters import datetimefilter 

def create_app():
    application = Flask(__name__)
    application.config['SECRET_KEY'] = 'secret'
    application.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('VLS_DATABASE_URI')
    db.init_app(application)

    from website.endpoints import endpoints
    application.register_blueprint(endpoints, url_prefix='/')

    application.jinja_env.filters['datetimefilter'] = datetimefilter

    with application.app_context():
        db.create_all()

    login_manager = LoginManager()
    login_manager.login_view = 'endpoints.sign_in_page'
    login_manager.init_app(application)

    @login_manager.user_loader
    def load_user(id: int):
        return db.session.get(User, id)

    # This allows for basic auth
    @login_manager.request_loader
    def load_user_from_request(request):
        auth = request.headers.get('Authorization')
        if not auth:
            return None

        if auth[:6] == 'Basic ':
            # Note that here we slice off the b'' symbol
            basic_auth = base64.b64decode(auth[8:-1]).decode('ascii')
            print(f'=>{basic_auth}')
            email, password = basic_auth.split(':')
            
            user = db.session.query(User).filter_by(email=email).first()
            
            if user == None:
                return None

            if check_password_hash(user.password, password) == False:
                return None

            return user

        return None


    return application


if __name__ == '__main__':
    create_app().run()
