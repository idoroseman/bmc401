import glob
import os
import time

from sensors.generic import BmcSensor

os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

class Ds18b20(BmcSensor):
    def setup(self):
        self.w1_base_dir = '/sys/bus/w1/devices/'
        self.w1_device_folder = glob.glob(self.w1_base_dir + '28*')[0]
        self.w1_device_file = self.w1_device_folder + '/w1_slave'


    def read_temp_raw(self):
        try:
            f = open(self.w1_device_file, 'r')
            lines = f.readlines()
            f.close()
            return lines
        except:
            return None

    def read(self):
        try:
            lines = self.read_temp_raw()
            while lines[0].strip()[-3:] != 'YES':
                time.sleep(0.2)
                lines = self.read_temp_raw()
            equals_pos = lines[1].find('t=')
            if equals_pos != -1:
                temp_string = lines[1][equals_pos + 2:]
                temp_c = float(temp_string) / 1000.0
                temp_f = temp_c * 9.0 / 5.0 + 32.0
        except:
            temp_c = 0
            self.isOk = False
        return {self.prefix + 'temp': temp_c}
