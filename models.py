import os
from typing import Optional

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
import time
from sqlalchemy.types import TypeDecorator
import datetime
from sqlalchemy import func, create_engine
from sqlalchemy import DOUBLE


def as_dict(self):
    return {c.name: getattr(self, c.name) for c in self.__table__.columns}


# I'm not sure if this is necessary, but as of 3/13/24 the sqlalchemy quickstart recommends it
# https://docs.sqlalchemy.org/en/20/orm/quickstart.html
class Base(DeclarativeBase):
    pass


class GPSData(Base):
    __tablename__ = 'gps'

    # Key for this GPS data point
    id: Mapped[int] = mapped_column(primary_key=True)

    # Time of recording
    time: Mapped[datetime.datetime] = mapped_column(server_default=func.now())

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




