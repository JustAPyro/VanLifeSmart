import os
from typing import Optional

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
import time
from sqlalchemy.types import TypeDecorator
import datetime
from sqlalchemy import func, create_engine, ForeignKey
from sqlalchemy import DOUBLE


# I'm not sure if this is necessary, but as of 3/13/24 the sqlalchemy quickstart recommends it
# https://docs.sqlalchemy.org/en/20/orm/quickstart.html
class Base(DeclarativeBase):
    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def as_list(self):
        return [getattr(self, c.name) for c in self.__table__.columns]

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

    # Location information
    latitude: Mapped[float]
    longitude: Mapped[float]
    altitude: Mapped[float]

    # Quality of results information
    fix_quality: Mapped[str]
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
