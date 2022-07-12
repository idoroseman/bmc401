import logging
import time

from sensors.generic import BmcSensor
try:
    import Adafruit_BMP.BMP085 as BMP085
except:
    pass


# see installation instruction on
#  https://learn.adafruit.com/using-the-bmp085-with-raspberry-pi/using-the-adafruit-bmp-python-library

# print('Temp = {0:0.2f} *C'.format(sensor.read_temperature()))
# print('Pressure = {0:0.2f} Pa'.format(sensor.read_pressure()))
# print('Altitude = {0:0.2f} m'.format(sensor.read_altitude()))
# print('Sealevel Pressure = {0:0.2f} Pa'.format(sensor.read_sealevel_pressure()))


class Bmp085(BmcSensor):
    def setup(self):
        logging.getLogger("Adafruit_BMP.BMP085").setLevel(logging.WARNING)
        logging.getLogger("Adafruit_I2C.Device.Bus.1.Address.0X77").setLevel(logging.WARNING)
        for retries in range(5):
          try:
            self.sensor = BMP085.BMP085()
            break
          except:
            time.sleep(1)
        self.patsea = 101325.0


    def read_pressure(self):
        pressure = 900
        for retry in range(5):
            try:
                self.sensor.read_temperature()
                pressure = self.sensor.read_pressure() / 100.0
                break
            except:
                pass
        return pressure

    def read_temp(self):
        temp = 0
        for retry in range(5):
            try:
                temp = self.sensor.read_temperature()
                break
            except:
                pass
        return temp


    def calibrate_alt(self, alt):
        # alt in meters
        try:
          self.patsea = self.sensor.read_sealevel_pressure(float(alt))
        except:
          pass

    def read_alt(self):
        return self.sensor.read_altitude(self.patsea)

    def read(self):
        return {self.prefix+"barometer": self.read_pressure(),
                self.prefix+"temp": self.read_temp()}

