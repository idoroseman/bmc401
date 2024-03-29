#!/usr/bin/env python3
import os
import sys
import time
import serial
try:
    import RPi.GPIO as GPIO
except:
    from mockgpio import MockGPIO as GPIO
import json
import logging

class Dorji():
    def __init__(self, pins):
        logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        self.pin = pins
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)

        GPIO.setup(self.pin['PD'], GPIO.OUT)
        GPIO.setup(self.pin['PTT'], GPIO.OUT)
        GPIO.setup(self.pin['HILO'], GPIO.IN)
        GPIO.setup(self.pin['LED2'], GPIO.OUT)

        GPIO.output(self.pin['PTT'], GPIO.HIGH)  # LOW = TX, HIGH = RX
        GPIO.output(self.pin['PD'], GPIO.HIGH)  # LOW = Sleep, HIGH = Normal
#       power pin :  LOW = 0.5W, Float = 1W, HIGH causes insain power consumption !

        os.system('gpio -g mode 18 alt5')  # sets GPIO 18 pin to ALT 5 mode = GPIO_GEN1


        try:
            self.ser = serial.Serial(
                port='/dev/ttyS0',
                baudrate=9600,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS,
                timeout=1,
                write_timeout=1
            )
        except:
            self.ser = None

        self.isOK = False
        self.verbose = True
        self.init()

    def cmnd(self, data):
        if self.ser is None:
            return
        retries = 3
        while retries>0:
            try:
                self.logger.debug(">%s"% data.strip())
                self.ser.write(data.encode())
                time.sleep(1)
                x = self.ser.readline().decode("UTF-8")
                self.logger.debug("<%s" % x.strip())
                if x.startswith('+') or x.startswith("S="):
                    self.isOK = True
                    break
                self.logger.debug("retry cmnd send")
                retries -= 1
            except Exception as x:
                self.logger.error(x)
                break

    def init(self):
        self.logger.debug("radio init")
        self.cmnd('AT+DMOCONNECT\r\n')
        self.cmnd('AT+SETFILTER=0,0,0\r\n')

    def scan(self, freq):
        self.logger.debug("radio scan %s" % freq)
        self.cmnd("S+%.4f\r\n" % freq)

    def freq(self, freq):
        self.logger.debug("radio freq %s" % freq)
        self.cmnd("AT+DMOSETGROUP=0,%.4f,%.4f,0000,4,0000\r\n" % (freq, freq))

    def tx(self):
        self.logger.debug("radio tx")
        GPIO.output(self.pin['PD'], GPIO.HIGH)
        GPIO.output(self.pin['PTT'], GPIO.LOW)
        GPIO.output(self.pin['LED2'], GPIO.HIGH)


    def rx(self):
        self.logger.debug("radio rx")
        GPIO.output(self.pin['PD'], GPIO.HIGH)
        GPIO.output(self.pin['PTT'], GPIO.HIGH)
        GPIO.output(self.pin['LED2'], GPIO.LOW)

    def standby(self):
        self.logger.debug("radio standby")
        GPIO.output(self.pin['PD'], GPIO.LOW)
        GPIO.output(self.pin['PTT'], GPIO.HIGH)

    def power(self, level):
        self.logger.debug("radio power %s" % level)
        GPIO.setup(self.pin['HILO'], GPIO.OUT)
        if level == "high":
            GPIO.output(self.pin['HILO'], GPIO.HIGH)
        elif level == "low":
            GPIO.output(self.pin['HILO'], GPIO.LOW)

    def play(self, freq, filename):
        self.freq(freq)
        self.tx()
        time.sleep(1)
        os.system("aplay " + filename)
        self.rx()


##################################################

if __name__ == "__main__":
    # Pin Definitions
    with open('../assets/config.json') as fin:
        config = json.load(fin)
        pins = config['pins']

    radio = Dorji(pins)
    if len(sys.argv) == 1:
        print("no arguments")
    elif sys.argv[1] == "init":
        radio.init()
    elif sys.argv[1] == "scan":
        freq = float(sys.argv[2])
        radio.scan(freq)
    elif sys.argv[1] == "freq":
        freq = float(sys.argv[2])
        radio.freq(freq)
    elif sys.argv[1] == "tx":
        radio.tx()
    elif sys.argv[1] == "rx":
        radio.rx()
    elif sys.argv[1] == "stby":
        radio.standby()
    elif sys.argv[1] == "power":
        radio.power(sys.argv[2])
    elif sys.argv[1] == "test":
        radio.play(config['frequencies']['APRS'], 'assets/boatswain_whistle.wav')
    elif sys.argv[1] == "play":
        radio.play(config['frequencies']['APRS'], sys.argv[2])
    else:
        print("unknown")

# GPIO.cleanup() # cleanup all GPIO
