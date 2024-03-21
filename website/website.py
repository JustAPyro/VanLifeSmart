import os

from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from models import Base

load_dotenv()
db = SQLAlchemy(model_class=Base)


def create_app():
    application = Flask(__name__)
    application.config['SECRET_KEY'] = 'secret'
    application.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('VLS_DATABASE_URI')
    db.init_app(application)

    from endpoints import endpoints
    application.register_blueprint(endpoints, url_prefix='/')

    with application.app_context():
        db.create_all()

    return application


app = create_app()
if __name__ == '__main__':
    app.run(debug=True)
