import os

import requests

from website.models import User, TomorrowIO


def normalize_email(email: str) -> str:
    return email.strip().lower()





def create_tio(user: User,
               latitude: float = None,
               longitude: float = None,
               load_tio: bool = False):

    # Input Verification
    if not latitude or not longitude:
        raise Exception('Latitude and Longitude are required for creating a checkpoint')

    # TomorrowIO (Weather)
    # https: // docs.tomorrow.io / reference / realtime - weather
    if load_tio:
        response = requests.get('https://api.tomorrow.io/v4/weather/realtime'
                                f'?location={latitude},{longitude}'
                                f'&apikey={os.environ["TOMORROWAPI"]}')
        time = response.json()['data']['time']
        tio_data = response.json()['data']['values']
        tio = TomorrowIO(
            time=time,
            uv_index=tio_data['uvIndex'],
            humidity=tio_data['humidity'],
            wind_gust=tio_data['windGust'],
            dew_point=tio_data['dewPoint'],
            cloud_base=tio_data['cloudBase'],
            wind_speed=tio_data['windSpeed'],
            visibility=tio_data['visibility'],
            cloud_cover=tio_data['cloudCover'],
            temperature=tio_data['temperature'],
            weather_code=tio_data['weatherCode'],
            cloud_ceiling=tio_data['cloudCeiling'],
            rain_intensity=tio_data['rainIntensity'],
            snow_intensity=tio_data['snowIntensity'],
            wind_direction=tio_data['windDirection'],
            sleet_intensity=tio_data['sleetIntensity'],
            uv_health_concern=tio_data['uvHealthConcern'],
            temperature_apparent=tio_data['temperatureApparent'],
            pressure_surface_level=tio_data['pressureSurfaceLevel'],
            freezing_rain_intensity=tio_data['freezingRainIntensity'],
            precipitation_probability=tio_data['precipitationProbability'],
        )
        return tio
