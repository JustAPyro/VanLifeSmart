import logging
from backup import backup_payload
from van2.sensors import Sensor
from van2.sensors.abstracts import DataPoint

logger = logging.getLogger(__name__)


def heartbeat(payload: dict[Sensor, list[DataPoint]]):
    backup_payload(payload)
