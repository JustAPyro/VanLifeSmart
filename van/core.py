import logging
from van.sensors import Sensor

logger = logging.getLogger(__name__)


def heartbeat(payload: dict[Sensor, list]):
    pass