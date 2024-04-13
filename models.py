import os
from typing import Optional, List

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
import time
from sqlalchemy.types import TypeDecorator, DECIMAL
import datetime
from sqlalchemy import func, create_engine, ForeignKey, String, Column, Table
from sqlalchemy import DOUBLE
from flask_login import UserMixin


# I'm not sure if this is necessary, but as of 3/13/24 the sqlalchemy quickstart recommends it
# https://docs.sqlalchemy.org/en/20/orm/quickstart.html
class Base(DeclarativeBase):

    def as_dict(self):
        response = {}
        for col in self.__table__.columns:
            if type(getattr(self, col.name) == datetime):
                response[col.name] = getattr(self, col.name)
            else:
                reponse[col.name] = str(getattr(self, col.name))
        #return {c.name: str(getattr(self, c.name)) for c in self.__table__.columns}
        return response

    def as_list(self):
        return [str(getattr(self, c.name)) for c in self.__table__.columns]



class Role(Base):
    __tablename__ = 'role'
    id: Mapped[int] = mapped_column(primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey('vehicle.id'))
    name: Mapped[str] = mapped_column(String(40))

    view_location: Mapped[bool]
    view_weather: Mapped[bool]
    view_heartbeat: Mapped[bool]
    write_heartbeat: Mapped[bool]
    

class Follow(Base):
    __tablename__ = 'follow'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('user.id'))
    user: Mapped[List['User']] = relationship(back_populates='follows')
    vehicle_id: Mapped[int] = mapped_column(ForeignKey('vehicle.id'))
    vehicle: Mapped['Vehicle'] = relationship(back_populates='follows')
    role_id: Mapped[Optional['Role']] = mapped_column(ForeignKey('role.id'))
    role: Mapped['Role'] = relationship()


class Vehicle(Base):
    __tablename__ = 'vehicle'
    id: Mapped[int] = mapped_column(primary_key=True)
    last_heartbeat: Mapped[datetime.datetime] = mapped_column(server_default=func.now())
    next_expected_heartbeat: Mapped[Optional[datetime.datetime]]
    name: Mapped[str] = mapped_column(String(36))
    owner_id: Mapped[int] = mapped_column(ForeignKey('user.id'))
    owner: Mapped['User'] = relationship(back_populates='vehicles')

    roles: Mapped[List['Role']] = relationship()
    gps_data: Mapped[List['GPSData']] = relationship(back_populates='vehicle')
    follows: Mapped[List['Follow']] = relationship(back_populates='vehicle')

    permissions: Mapped[List['VehiclePermission']] = relationship(back_populates='vehicle')
    heartbeats: Mapped[List['Heartbeat']] = relationship(back_populates='vehicle')
    pitstops: Mapped[List['Pitstop']] = relationship(back_populates='vehicle')

class User(Base, UserMixin):
    __tablename__ = 'user'
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(320))
    username: Mapped[str] = mapped_column(String(36))
    password: Mapped[str] = mapped_column(String(150))
    vehicle_permissions: Mapped['VehiclePermission'] = relationship(back_populates='owner')
    created_on: Mapped[datetime.datetime] = mapped_column(server_default=func.now())
    vehicles: Mapped[List['Vehicle']] = relationship(back_populates='owner')
    last_activity: Mapped[datetime.datetime] = mapped_column(server_default=func.now())
    tio_data: Mapped[List['TomorrowIO']] = relationship(back_populates='owner')

    follows: Mapped[List['Follow']] = relationship(back_populates='user')



class Pitstop(Base):
    __tablename__ = 'pitstop'
    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[datetime.datetime] = mapped_column(server_default=func.now())
    vehicle_id: Mapped[Optional[int]] = mapped_column(ForeignKey('vehicle.id'))
    vehicle: Mapped[Optional['Vehicle']] = relationship(back_populates='pitstops')

    gallons_filled: Mapped[float]
    total_cost: Mapped[float]
    mileage: Mapped[int]
    filled: Mapped[bool]

class VehiclePermission(Base):
    __tablename__ = 'vehicle_permission'
    id: Mapped[int] = mapped_column(primary_key=True)

    owner_id: Mapped[int] = mapped_column(ForeignKey('user.id'))
    owner: Mapped['User'] = relationship(back_populates='vehicle_permissions')

    vehicle_id: Mapped[int] = mapped_column(ForeignKey('vehicle.id'))
    vehicle: Mapped['Vehicle'] = relationship(back_populates='permissions')




            
class Heartbeat(Base):
    """
    This class tracks the vehicle's uptime and connectivity to server
    by tracking the server connection attempts.
    """
    # ID identifier and table name
    __tablename__ = 'heartbeat'
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Vehicle this heartbeat belongs to
    vehicle_id: Mapped[Optional[int]] = mapped_column(ForeignKey('vehicle.id'))
    vehicle: Mapped[Optional['Vehicle']] = relationship(back_populates='heartbeats')

    # If this was expected/on schedule or late
    on_schedule: Mapped[bool]

    # Successfulness of connection to server and internet
    server: Mapped[bool]
    internet: Mapped[bool]

    # Time of connection and next expected
    time_utc: Mapped[datetime.datetime]
    next_time: Mapped[datetime.datetime]
    

"""
class DHTData(Base):
    __tablename__ = 'tio'

    id: Mapped[int] = mapped_column(primary_key=True)
    sensor_name: Mapped[str]

    # The GPS location of the reading
    gps_id: Mapped[int] = mapped_column(ForeignKey("gps.id"))
    gps_data: Mapped["GPSData"] = relationship(back_populates="tio")

    # DHT records temperature and humidity
    temperature: Mapped[float]
    humidity: Mapped[float]

"""


class GPSData(Base):
    __tablename__ = 'gps'

    # Key for this GPS data point
    id: Mapped[int] = mapped_column(primary_key=True)
    # Time of recording
    utc_time: Mapped[datetime.datetime] = mapped_column(server_default=func.now())
    # Owner
    vehicle_id: Mapped[Optional[int]] = mapped_column(ForeignKey('vehicle.id'))
    vehicle: Mapped[Optional["Vehicle"]] = relationship(back_populates="gps_data")

    # Location information
    latitude: Mapped[float]
    longitude: Mapped[float]
    altitude: Mapped[float]

    # Quality of results information
    fix_quality: Mapped[str] = mapped_column(String(10))
    satellites_used: Mapped[int]
    hdop: Mapped[float]

    # Directional information (If Applicable)
    true_track: Mapped[Optional[float]]
    magnetic_track: Mapped[Optional[float]]

    # Speed (if applicable)
    ground_speed: Mapped[Optional[float]]

    tomorrow_io: Mapped['TomorrowIO'] = relationship(back_populates='gps_data')


class TomorrowIO(Base):
    """TomorrowIO API Data"""
    __tablename__ = 'tomorrow_io'

    # id
    id: Mapped[int] = mapped_column(primary_key=True)
    # Owner
    owner_id: Mapped[Optional[int]] = mapped_column(ForeignKey('user.id'))
    owner: Mapped[Optional["User"]] = relationship(back_populates="tio_data")

    utc_time: Mapped[datetime.datetime] = mapped_column(server_default=func.now())

    invalid: Mapped[bool]

    gps_id: Mapped[int] = mapped_column(ForeignKey("gps.id"))
    gps_data: Mapped["GPSData"] = relationship(back_populates="tomorrow_io")
    cloud_base: Mapped[Optional[float]]
    cloud_ceiling: Mapped[Optional[float]]
    cloud_cover: Mapped[Optional[float]]
    dew_point: Mapped[Optional[float]]
    freezing_rain_intensity: Mapped[Optional[int]]
    humidity: Mapped[Optional[int]]
    precipitation_probability: Mapped[Optional[int]]
    pressure_surface_level: Mapped[Optional[float]]
    rain_intensity: Mapped[Optional[int]]
    sleet_intensity: Mapped[Optional[int]]
    snow_intensity: Mapped[Optional[int]]
    temperature: Mapped[Optional[float]]
    temperature_apparent: Mapped[Optional[float]]
    uv_health_concern: Mapped[Optional[int]]
    uv_index: Mapped[Optional[int]]
    visibility: Mapped[Optional[float]]
    weather_code: Mapped[Optional[int]]
    wind_direction: Mapped[Optional[float]]
    wind_gust: Mapped[Optional[float]]
    wind_speed: Mapped[Optional[float]]
