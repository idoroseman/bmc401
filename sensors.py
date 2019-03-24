import os
import glob
import time

os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')
import Adafruit_BMP.BMP085 as BMP085


# see installation instruction on
#  https://learn.adafruit.com/using-the-bmp085-with-raspberry-pi/using-the-adafruit-bmp-python-library

# print('Temp = {0:0.2f} *C'.format(sensor.read_temperature()))
# print('Pressure = {0:0.2f} Pa'.format(sensor.read_pressure()))
# print('Altitude = {0:0.2f} m'.format(sensor.read_altitude()))
# print('Sealevel Pressure = {0:0.2f} Pa'.format(sensor.read_sealevel_pressure()))

class Sensors():
    def __init__(self):
        self.w1_base_dir = '/sys/bus/w1/devices/'
        self.w1_device_folder = glob.glob(self.w1_base_dir + '28*')[0]
        self.w1_device_file = self.w1_device_folder + '/w1_slave'
        self.sensor = BMP085.BMP085()
        self.patsea = 101325.0

    def get_data(self):
        return {
            'outside_temp': self.read_outside_temp(),
            'inside_temp': self.read_inside_temp(),
            'barometer': self.read_pressure()
        }

    def read_temp_raw(self):
        f = open(self.w1_device_file, 'r')
        lines = f.readlines()
        f.close()
        return lines

    def read_pressure(self):
	pressure = None
        while pressure is None:
          try:
            self.sensor.read_temperature()
            pressure = self.sensor.read_pressure() / 100.0
          except:
            pass
        return pressure

    def read_inside_temp(self):
        temp = None
        while temp is None:
            try:
                temp = self.sensor.read_temperature()
            except:
                pass
        return temp


    def calibrate_alt(self, alt):
        # alt in meters
        self.patsea = self.sensor.read_sealevel_pressure(alt)


    def reat_alt(self):
        return sensor.read_altitude(self.patsea)


    def read_outside_temp(self):
        lines = self.read_temp_raw()
        while lines[0].strip()[-3:] != 'YES':
            time.sleep(0.2)
            lines = self.read_temp_raw()
        equals_pos = lines[1].find('t=')
        if equals_pos != -1:
            temp_string = lines[1][equals_pos + 2:]
            temp_c = float(temp_string) / 1000.0
            temp_f = temp_c * 9.0 / 5.0 + 32.0
            return temp_c


if __name__ == "__main__":
    sensors = Sensors()
    print(sensors.read_outside_temp())
