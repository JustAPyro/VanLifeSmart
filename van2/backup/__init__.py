import os

from van2.sensors import DataFactory
from van2.sensors.abstracts import DataPoint


def backup_payload(payload: dict[DataFactory, list[DataPoint]]):
    for sensor, data in payload.items():
        file_path = os.path.abspath(f'{os.getenv("VLS_INSTALL")}/van2/data/backups/{sensor.data_type}.csv')
        print(file_path)
        print(data)
        with open(file_path, 'a') as file:
            for item in data:
                file.write(item.to_line()+'\n')