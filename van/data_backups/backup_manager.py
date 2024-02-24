import json
import os


class BackupManager:
    def __init__(self, backup_location: str):
        self.folder = backup_location

        self._persistent = {
            'total_size': 0,
            'sensor_backups': {}
        }

        # This block of code will either load the values from the .backup file
        # to the persistent dict OR if the file doesn't exist it will create it
        # and load persistent into it. Either way, the effect at the end is that
        # self.persistent values will... persist.
        try:
            with open('.backup', 'r') as file:
                self._persistent = json.load(file)
        except FileNotFoundError:
            with open('.backup', 'w') as file:
                file.write(json.dumps(self._persistent, indent=4))

    @property
    def total_size(self):
        return self._persistent['total_size']

    @total_size.setter
    def total_size(self, value):
        self._persistent['total_size'] = value
        self._refresh()

    def add_sensor_backups(self, sensor: str, qty: int):
        if sensor not in self._persistent['sensor_backups']:
            self._persistent['sensor_backups'][sensor] = qty
        else:
            self._persistent['sensor_backups'][sensor] += qty
        self._refresh()

    def backup(self, data: dict) -> int:
        """
        :param data: The sensor payload you want to back up
        :return: The bytes of storage consumed by this addition to backup.
        """
        # Track the number of byte storage used by this backup
        added_size = 0

        # Open and create a backup file for each data table
        for dtype, data in data.items():
            data_points = 0

            # If we have no data for this sensor skip it
            if len(data) == 0:
                continue

            # If we have data, open a data_backup file for this sensor
            with open(f'{self.folder}/{dtype}_backup.csv', 'a') as file:

                # Write the headers
                for item in data:
                    data_points += 1
                    # TODO: This is a little fragile imo
                    file.write((','.join([str(value) for value in item.values()])) + '\n')
                file.seek(0, os.SEEK_END)
                added_size = file.tell()
                self.total_size += added_size
                self.add_sensor_backups(dtype, data_points)
                return added_size

    def clear(self):
        pass

    def restore(self, payload, sensors):
        for sensor in sensors:
            try:
                with open(f'van/data_backups/{sensor.sensor_type}_backup.csv', 'r') as file:
                    for line in file.readlines():
                        data_entry = sensor.from_csv(line)
                        payload[sensor.sensor_type].append(data_entry)
            except (OSError,) as e:
                print(e)

    def _refresh(self):
        with open('.backup', 'w') as file:
            file.write(json.dumps(self._persistent, indent=4))
