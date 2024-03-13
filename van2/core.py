import logging
from van2.sensors import Sensor

logger = logging.getLogger(__name__)


def heartbeat(payload: dict[Sensor, list]):
    pass