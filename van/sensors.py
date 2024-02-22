import adafruit_dht
import board

# Initialize Devices
dht_device = adafruit_dht.DHT22(board.D4)


def get_dht_data(retries: int = 3):
    for _ in range(retries):
        try:
            return {
                'temperature': dht_device.temperature,
                'humidity': dht_device.humidity
            }
        except RuntimeError:
            continue


sensor_config = {
    'dht': {
        'get': get_dht_data,
        'polling': {'minutes': 10}
    }
}
