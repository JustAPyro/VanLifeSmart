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


class Checkpoint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    time = db.Column(db.DateTime(timezone=True), default=func.now(), nullable=False)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)

    # TomorrowIO
    tio_cloud_base = db.Column(db.Float, nullable=True)
    tio_cloud_ceiling = db.Column(db.Float, nullable=True)
    tio_cloud_cover = db.Column(db.Integer, nullable=True)
    tio_dew_point = db.Column(db.Float, nullable=True)
    tio_freezing_rain_intensity = db.Column(db.Integer, nullable=True)
    tio_humidity = db.Column(db.Integer, nullable=True)
    tio_precipitation_probability = db.Column(db.Integer, nullable=True)
    tio_pressure_surface_level = db.Column(db.Float, nullable=True)
    tio_rain_intensity = db.Column(db.Integer, nullable=True)
    tio_sleet_intensity = db.Column(db.Integer, nullable=True)
    tio_snow_intensity = db.Column(db.Integer, nullable=True)
    tio_temperature = db.Column(db.Float, nullable=True)
    tio_temperature_apparent = db.Column(db.Float, nullable=True)
    tio_uv_health_concern = db.Column(db.Integer, nullable=True)
    tio_uv_index = db.Column(db.Integer, nullable=True)
    tio_visibility = db.Column(db.Float, nullable=True)
    tio_weather_code = db.Column(db.Integer, nullable=True)
    tio_wind_direction = db.Column(db.Float, nullable=True)
    tio_wind_gust = db.Column(db.Float, nullable=True)
    tio_wind_speed = db.Column(db.Float, nullable=True)


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



