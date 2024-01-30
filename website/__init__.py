from flask import Flask


def create_app():
    # Setup Flask
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'secret'

    # Import all views
    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    return app
