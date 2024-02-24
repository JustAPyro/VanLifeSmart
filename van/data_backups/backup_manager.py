import json
import os


class BackupManager:
    def __init__(self, backup_location: str):
        self.folder = backup_location

        with open(f'{self.folder}/.backup') as file:
            backup = json.load(file)
        self.backup_size = 0

        self.total_size = 0

    def backup(self, data: dict) -> int:
        """
        :param data: The sensor payload you want to back up
        :return: The bytes of storage consumed by this addition to backup.
        """
        # Track the number of byte storage used by this backup
        added_size = 0

        # Open and create a backup file for each data table
        for dtype, data in data.items():

            # If we have no data for this sensor skip it
            if len(data) == 0:
                continue

            # If we have data, open a data_backup file for this sensor
            with open(f'{self.folder}/{dtype}_backup.csv', 'a') as file:

                # Write the headers
                for item in data:
                    # TODO: This is a little fragile imo
                    file.write((','.join([str(value) for value in item.values()])) + '\n')
                file.seek(0, os.SEEK_END)
                added_size = file.tell()
                self.total_size += added_size
                return added_size

    def clear(self):
        pass

    def restore(self, payload):
        for sensor in sensors:
            try:
                with open(f'van/data_backups/{sensor.sensor_type}_backup.csv', 'r') as file:
                    for line in file.readlines():
                        data_entry = sensor.from_csv(line)
                        payload[sensor.sensor_type].append(data_entry)
            except (OSError,) as e:
                print(e)
