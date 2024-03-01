import logging
from backup import backup_payload
from van2.sensors import DataFactory
from van2.sensors.abstracts import DataPoint

logger = logging.getLogger(__name__)


def heartbeat(payload: dict[DataFactory, list[DataPoint]]):
    backup_payload(payload)
