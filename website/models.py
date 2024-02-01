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


class Checkpoint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    time = db.Column(db.DateTime(timezone=True), default=func.now(), nullable=False)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)


class Roles(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)

    write_location = db.Column(db.Boolean, unique=False)


class Mechanic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))
    email = db.Column(db.String(150))
    phone = (db.String(10))

    # Address fields
    street = db.Column(db.String(150))
    city = db.Column(db.String(150))
    state = db.Column(db.String(10))
    zip = db.Column(db.String(10))

    maintenance = db.relationship('Maintenance')


class Maintenance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    milage = db.Column(db.Integer, nullable=False)
    date_invoiced = db.Column(db.DateTime, nullable=False)
    cost_invoiced = db.Column(db.Numeric, nullable=False)

    mechanic_id = db.Column(db.Integer, db.ForeignKey('mechanic.id'))
