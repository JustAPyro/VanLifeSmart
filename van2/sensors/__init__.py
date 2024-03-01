from van2.sensors.abstracts import DataFactory
from van2.sensors.gps import GPS


# This method will return data factories based
# on active sensors for the server to listen to.
# Every sensor running on the server should be initialized here
# If development is true, it will pass that to sensors and generate false data
def activate_sensors(development: bool = False) -> list[DataFactory]:
    return [
        GPS(location='/dev/ttyACM0', baud=9600, development=True)
    ]
