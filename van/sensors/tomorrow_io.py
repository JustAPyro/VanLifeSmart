import os
from typing import Optional

import requests
from requests.exceptions import ConnectionError
from models import Base, GPSData, TomorrowIO
from van.sensors.abstracts import Sensor


class TIO(Sensor):
    def __init__(self, gps, development):
        super().__init__(development=development)
        self.gps = gps

    def get_data(self) -> Optional[Base]:
        # Get the most recent GPSData from the database
        gps: GPSData = self.gps.get_data()

        try:
            response = requests.get(
                url=f'https://api.tomorrow.io/v4/weather/realtime'
                    f'?location={gps.latitude},{gps.longitude}'
                    f'&apikey={os.getenv("TOMORROW_IO_KEY")}',
                headers={
                    "accept": "application/json"}
            )
        except ConnectionError:
            return None

        # TODO: Handle case; No GPS Points
        # TODO: Handle case; GPS points are old

        if response.status_code != 200:
            return None

        tio = response.json()['data']['values']
        return TomorrowIO(
            gps_data=gps,
            invalid=self.development,
            cloud_base=tio['cloudBase'],
            cloud_ceiling=tio['cloudCeiling'],
            cloud_cover=tio['cloudCover'],
            dew_point=tio['dewPoint'],
            freezing_rain_intensity=tio['freezingRainIntensity'],
            humidity=tio['humidity'],
            precipitation_probability=tio['precipitationProbability'],
            pressure_surface_level=tio['pressureSurfaceLevel'],
            rain_intensity=tio['rainIntensity'],
            sleet_intensity=tio['sleetIntensity'],
            snow_intensity=tio['snowIntensity'],
            temperature=tio['temperature'],
            temperature_apparent=tio['temperatureApparent'],
            uv_health_concern=tio['uvHealthConcern'],
            uv_index=tio['uvIndex'],
            visibility=tio['visibility'],
            weather_code=tio['weatherCode'],
            wind_direction=tio['windDirection'],
            wind_gust=tio['windGust'],
            wind_speed=tio['windSpeed'],
        )

    @property
    def data_type(self) -> str:
        return 'TomorrowIO'
