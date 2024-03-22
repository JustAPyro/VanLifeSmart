import os
from typing import Optional, List

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
import time
from sqlalchemy.types import TypeDecorator
import datetime
from sqlalchemy import func, create_engine, ForeignKey, String, Column, Table
from sqlalchemy import DOUBLE
from flask_login import UserMixin


# I'm not sure if this is necessary, but as of 3/13/24 the sqlalchemy quickstart recommends it
# https://docs.sqlalchemy.org/en/20/orm/quickstart.html
class Base(DeclarativeBase):

    def as_dict(self):
        return {c.name: str(getattr(self, c.name)) for c in self.__table__.columns}

    def as_list(self):
        return [str(getattr(self, c.name)) for c in self.__table__.columns]


following = Table(
    'following',
    Base.metadata,
    Column('subject', ForeignKey('user.id')),
    Column('object', ForeignKey('user.id'))
)


class Vehicle(Base):
    __tablename__ = 'vehicle'
    id: Mapped[int] = mapped_column(primary_key=True)
    last_heartbeat: Mapped[datetime.datetime] = mapped_column(server_default=func.now())
    name: Mapped[str] = mapped_column(String(36))
    owner_id: Mapped[int] = mapped_column(ForeignKey('user.id'))
    owner: Mapped['User'] = relationship(back_populates='vehicles') 

class User(Base, UserMixin):
    __tablename__ = 'user'
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(320))
    username: Mapped[str] = mapped_column(String(36))
    password: Mapped[str] = mapped_column(String(150))
    created_on: Mapped[datetime.datetime] = mapped_column(server_default=func.now())
    vehicles: Mapped[List['Vehicle']] = relationship(back_populates='owner')
    last_activity: Mapped[datetime.datetime] = mapped_column(server_default=func.now())
    gps_data: Mapped[List['GPSData']] = relationship(back_populates='owner')
    follows = relationship('User',
                           secondary=following,
                           primaryjoin=(following.c.object == id),
                           secondaryjoin=(following.c.subject == id),
                           backref='following')

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
    owner_id: Mapped[Optional[int]] = mapped_column(ForeignKey('user.id'))
    owner: Mapped[Optional["User"]] = relationship(back_populates="gps_data")

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
    # owner
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
