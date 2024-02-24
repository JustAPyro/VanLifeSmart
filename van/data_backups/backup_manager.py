import json
import os


class BackupManager:
    def __init__(self, backup_location: str):
        self.folder = backup_location

        self._persistent = {
            'total_size': 0
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

    def _refresh(self):
        with open('.backup', 'w') as file:
            file.write(json.dumps(self._persistent, indent=4))

    def backup(self, data: dict) -> int:
        """
        :param data: The sensor payload you want to back up
        :return: The bytes of storage consumed by this addition to backup.
        """
        # Track the number of byte storage used by this backup
        added_size = 0

        # Open and create a backup file for each data table
        for dtype, data in data.items():
            dtype: str        # Name of the sensor
            data: list[dict]  # List of dictionary data points

            # If we have no data for this sensor skip it
            if len(data) == 0:
                continue

            # If we have data, open a data_backup file for this sensor
            with open(f'{self.folder}/{dtype}_backup.csv', 'a') as file:
                for item in data:
                    # TODO: This is a little fragile imo
                    # Join with commas the string value of each data point in this item
                    file.write((','.join([str(value) for value in item.values()])) + '\n')

                # Make sure we're at the end, then
                # save the size of the file
                # TODO: Fix bug here, why are we claiming added_size is the size of THIS backup
                file.seek(0, os.SEEK_END)
                added_size = file.tell()
                self.total_size += added_size
        return added_size

    def restore(self, payload, sensors):
        for sensor in sensors:
            try:
                with open(f'{self.folder}/{sensor.sensor_type}_backup.csv', 'r') as file:
                    for line in file.readlines():
                        data_entry = sensor.from_csv(line)
                        if data_entry:
                            payload[sensor.sensor_type].append(data_entry)
            except (OSError,) as e:
                print(e)

    def clear(self, sensors):
        for sensor in sensors:
            try:
                os.remove(f'{self.folder}/{sensor.sensor_type}_backup.csv')
            except FileNotFoundError:
                pass


