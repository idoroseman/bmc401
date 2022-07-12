import os
import glob
import time
import logging

os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')
import Adafruit_BMP.BMP085 as BMP085
import RPi.GPIO as GPIO

# see installation instruction on
#  https://learn.adafruit.com/using-the-bmp085-with-raspberry-pi/using-the-adafruit-bmp-python-library

# print('Temp = {0:0.2f} *C'.format(sensor.read_temperature()))
# print('Pressure = {0:0.2f} Pa'.format(sensor.read_pressure()))
# print('Altitude = {0:0.2f} m'.format(sensor.read_altitude()))
# print('Sealevel Pressure = {0:0.2f} Pa'.format(sensor.read_sealevel_pressure()))

# Define SPI Pins
SPICLK = 22
SPIMISO = 9
SPIMOSI = 10
SPICS = 8


class Sensors():
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        logging.getLogger("Adafruit_BMP.BMP085").setLevel(logging.WARNING)
        logging.getLogger("Adafruit_I2C.Device.Bus.1.Address.0X77").setLevel(logging.WARNING)
        try:
            self.w1_base_dir = '/sys/bus/w1/devices/'
            self.w1_device_folder = glob.glob(self.w1_base_dir + '28*')[0]
            self.w1_device_file = self.w1_device_folder + '/w1_slave'
        except:
            pass
        for retries in range(5):
          try:
            self.sensor = BMP085.BMP085()
            break
          except:
            time.sleep(1)
        self.patsea = 101325.0
        # ADC
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(SPIMOSI, GPIO.OUT)
        GPIO.setup(SPIMISO, GPIO.IN)
        GPIO.setup(SPICLK, GPIO.OUT)
        GPIO.setup(SPICS, GPIO.OUT)

    def get_data(self):
        return {
            'outside_temp': self.read_outside_temp(),
            'inside_temp': self.read_inside_temp(),
            'barometer': self.read_pressure(),
            'battery': self.read_battery(),
        }

    def read_temp_raw(self):
        try:
            f = open(self.w1_device_file, 'r')
            lines = f.readlines()
            f.close()
            return lines
        except:
            return []

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

    def read_inside_temp(self):
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

    # modified code based on an adafruit example for mcp3008
    def readadc(self, adcnum, clockpin, mosipin, misopin, cspin):
        if ((adcnum > 1) or (adcnum < 0)):
            return -1
        if (adcnum == 0):
            commandout = 0x6
        else:
            commandout = 0x7

        GPIO.output(cspin, True)

        GPIO.output(clockpin, False)  # start clock low
        GPIO.output(cspin, False)  # bring CS low

        commandout <<= 5  # we only need to send 3 bits here
        for i in range(3):
            if (commandout & 0x80):
                GPIO.output(mosipin, True)
            else:
                GPIO.output(mosipin, False)
            commandout <<= 1
            GPIO.output(clockpin, True)
            GPIO.output(clockpin, False)

        adcout = 0
        # read in one empty bit, one null bit and 10 ADC bits
        for i in range(12):
            GPIO.output(clockpin, True)
            GPIO.output(clockpin, False)
            adcout <<= 1
            if (GPIO.input(misopin)):
                adcout |= 0x1

        GPIO.output(cspin, True)

        adcout /= 2  # first bit is 'null' so drop it
        return adcout

    def read_battery(self):
        # read the analog pin
        reps = 10
        adcnum = 1
        adctot = 0
        for i in range(reps):
            read_adc = self.readadc(adcnum, SPICLK, SPIMOSI, SPIMISO, SPICS)
            adctot += read_adc
            time.sleep(0.05)
        read_adc = adctot / reps / 1.0
#        self.logger.debug("adc reading: %.2f" % read_adc)

        # convert analog reading to Volts = ADC * ( 3.33 / 1024 )
        # 3.33 tweak according to the 3v3 measurement on the Pi
        volts = read_adc * (3.33 / 1024.0) * 6
#        self.logger.debug("Battery Voltage: %.2f" % volts)
        return round(volts, 2)

if __name__ == "__main__":
    sensors = Sensors()
    print("OutTemp = {0:0.2f} *C".format(sensors.read_outside_temp()))
    print('Temp = {0:0.2f} *C'.format(sensors.read_inside_temp()))
    print('Pressure = {0:0.2f} Pa'.format(sensors.read_pressure()))
    print('Altitude = {0:0.2f} m'.format(sensors.read_alt()))
    print('Battery = {0:0.2f} m'.format(sensors.read_battery()))
