from van.sensors.abstracts import Sensor
from van.sensors.gps import GPS
from van.sensors.tomorrow_io import TIO


# This method will return data factories based
# on active sensors for the server to listen to.
# Every sensor running on the server should be initialized here
# If development is true, it will pass that to sensors and generate false data
def activate_sensors(development: bool = False) -> list[Sensor]:
    gps_sensor = GPS(location='/dev/ttyACM0', baud=9600, development=development)
    tio_sensor = TIO(gps_sensor, development=development)
    return [
        gps_sensor,
        tio_sensor
    ]
