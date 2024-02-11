from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    name = db.Column(db.String(150))
    created_on = db.Column(db.DateTime(timezone=True), default=func.now(), nullable=False)
    last_activity = db.Column(db.DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)

    mechanics = db.relationship('Mechanic')
    maintenance = db.relationship('Maintenance')


sample = {
    'latitude': '?',
    'longitude': '?',
    'tomorrowIO': 'fillOnServer',
    'dhts': {
        'cabin': {
            'temperature': 32.4,
            'humidity': 43
        },
        'outdoor': {
            'temperature': 43.2,
            'humidity': 54
        }
    }

}


class Checkpoint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner = db.Column(db.Integer, db.ForeignKey('user.id'))
    time = db.Column(db.DateTime(timezone=True), default=func.now(), nullable=False)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)

    tio = db.relationship('TomorrowIO', uselist=False)
    #gps = db.relationship('GPSData', uselist=False)
    dht = db.relationship('DHTSensor')


class DHTSensor(db.Model):
    # ID & associated checkpoint
    id = db.Column(db.Integer, primary_key=True)
    sensor = db.Column(db.String(50), nullable=False)
    checkpoint = db.Column(db.Integer, db.ForeignKey('checkpoint.id'))

    # Data
    temperature = db.Column(db.Float, nullable=False)
    humidity = db.Column(db.Float, nullable=False)


# class GPSData(db.Model):
#    id = db.Column(db.Integer, primary_key=True)
#    checkpoint = db.Column(db.Integer, db.ForeignKey('checkpoint.id'))


class TomorrowIO(db.Model):
    # ID
    id = db.Column(db.Integer, primary_key=True)
    checkpoint = db.Column(db.Integer, db.ForeignKey('checkpoint.id'))

    # TomorrowIO
    cloud_base = db.Column(db.Float, nullable=True)
    cloud_ceiling = db.Column(db.Float, nullable=True)
    cloud_cover = db.Column(db.Integer, nullable=True)
    dew_point = db.Column(db.Float, nullable=True)
    freezing_rain_intensity = db.Column(db.Integer, nullable=True)
    humidity = db.Column(db.Integer, nullable=True)
    precipitation_probability = db.Column(db.Integer, nullable=True)
    pressure_surface_level = db.Column(db.Float, nullable=True)
    rain_intensity = db.Column(db.Integer, nullable=True)
    sleet_intensity = db.Column(db.Integer, nullable=True)
    snow_intensity = db.Column(db.Integer, nullable=True)
    temperature = db.Column(db.Float, nullable=True)
    temperature_apparent = db.Column(db.Float, nullable=True)
    uv_health_concern = db.Column(db.Integer, nullable=True)
    uv_index = db.Column(db.Integer, nullable=True)
    visibility = db.Column(db.Float, nullable=True)
    weather_code = db.Column(db.Integer, nullable=True)
    wind_direction = db.Column(db.Float, nullable=True)
    wind_gust = db.Column(db.Float, nullable=True)
    wind_speed = db.Column(db.Float, nullable=True)


class Roles(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)

    write_location = db.Column(db.Boolean, unique=False)


class Mechanic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))
    email = db.Column(db.String(150), nullable=True)
    phone = db.Column(db.String(10), nullable=True)

    # Address fields
    street = db.Column(db.String(150))
    city = db.Column(db.String(150))
    state = db.Column(db.String(10))
    zip = db.Column(db.String(10))

    deleted = db.Column(db.Boolean, default=False)

    maintenance = db.relationship('Maintenance')
    owner = db.Column(db.Integer, db.ForeignKey('user.id'))


class Maintenance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # The mechanic/garage that performed the repairs associated with this
    mechanic_id = db.Column(db.Integer, db.ForeignKey('mechanic.id'))

    # Total cost of repairs
    cost_invoiced = db.Column(db.Numeric, nullable=False)

    mileage = db.Column(db.Integer, nullable=False)
    date_invoiced = db.Column(db.DateTime, nullable=False)
    invoice_number = db.Column(db.String(150), nullable=True)
    description_of_work = db.Column(db.String(20000), nullable=True)
    owner = db.Column(db.Integer, db.ForeignKey('user.id'))
    deleted = db.Column(db.Boolean, default=False)
    technicians = db.Column(db.String(150))
