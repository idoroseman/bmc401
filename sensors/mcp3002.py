import time
from sensors.generic import BmcSensor
try:
    import RPi.GPIO as GPIO
except:
    from mockgpio import MockGPIO as GPIO

# Define SPI Pins
SPICLK = 22
SPIMISO = 9
SPIMOSI = 10
SPICS = 8

class Mcp3002(BmcSensor):
    def setup(self):
        # ADC
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(SPIMOSI, GPIO.OUT)
            GPIO.setup(SPIMISO, GPIO.IN)
            GPIO.setup(SPICLK, GPIO.OUT)
            GPIO.setup(SPICS, GPIO.OUT)
        except:
            pass

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

    def read(self):
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
        return {self.prefix+"V": round(volts, 2)}