
import logging


class Sensors():
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

    def get_data(self):
        return {
            'outside_temp': self.read_outside_temp(),
            'inside_temp': self.read_inside_temp(),
            'barometer': self.read_pressure(),
            'battery': self.read_battery(),
        }




if __name__ == "__main__":
    sensors = Sensors()
    print("OutTemp = {0:0.2f} *C".format(sensors.read_outside_temp()))
    print('Temp = {0:0.2f} *C'.format(sensors.read_inside_temp()))
    print('Pressure = {0:0.2f} Pa'.format(sensors.read_pressure()))
    print('Altitude = {0:0.2f} m'.format(sensors.read_alt()))
    print('Battery = {0:0.2f} m'.format(sensors.read_battery()))
