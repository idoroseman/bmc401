#!/usr/bin/env python
import os
import sys
import time
import serial
import RPi.GPIO as GPIO
import json
import logging

class Dorji():
    def __init__(self, pins):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        self.pin = pins
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)

        GPIO.setup(self.pin['PD'], GPIO.OUT)
        GPIO.setup(self.pin['PTT'], GPIO.OUT)
        GPIO.setup(self.pin['HILO'], GPIO.OUT)
        GPIO.setup(self.pin['LED2'], GPIO.OUT)

        GPIO.output(self.pin['PTT'], GPIO.HIGH)  # LOW = TX, HIGH = RX
        GPIO.output(self.pin['PD'], GPIO.HIGH)  # LOW = Sleep, HIGH = Normal
        GPIO.output(self.pin['HILO'], GPIO.LOW)  # LOW = 0.5W, Float = 1W

        os.system('gpio -g mode 18 alt5')  # sets GPIO 18 pin to ALT 5 mode = GPIO_GEN1

        self.ser = serial.Serial(
            port='/dev/serial0',
            baudrate=9600,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            timeout=1,
            write_timeout=1
        )

        self.isOK = False
        self.verbose = True
        self.init()

    def cmnd(self, data):
        while True:
            try:
                if self.verbose:
                    self.logger.debug(">%s"% data.strip())
                self.ser.write(data.encode())
                time.sleep(1)
                x = self.ser.readline().decode("UTF-8")
                if self.verbose:
                    self.logger.debug("<%s" % x.strip())
                if x.startswith('+') or x.startswith("S="):
                    self.isOK = True
                    break;
                self.logger.debug("retry cmnd send")
            except Exception as x:
                self.logger.exception(x)

    def init(self):
        self.logger.info("radio init")
        self.cmnd('AT+DMOCONNECT\r\n')

    def scan(self, freq):
        self.logger.info("radio scan %s" % freq)
        self.cmnd("S+%.4f\r\n" % freq)

    def freq(self, freq):
        self.logger.info("radio freq %s" % freq)
        self.cmnd("AT+DMOSETGROUP=0,%.4f,%.4f,0000,4,0000\r\n" % (freq, freq))

    def tx(self):
        self.logger.info("radio tx")
        GPIO.output(self.pin['PD'], GPIO.HIGH)
        GPIO.output(self.pin['PTT'], GPIO.LOW)
        GPIO.output(self.pin['LED2'], GPIO.HIGH)

    def rx(self):
        self.logger.info("radio rx")
        GPIO.output(self.pin['PD'], GPIO.HIGH)
        GPIO.output(self.pin['PTT'], GPIO.HIGH)
        GPIO.output(self.pin['LED2'], GPIO.LOW)

    def standby(self):
        self.logger.info("radio standby")
        GPIO.output(self.pin['PD'], GPIO.LOW)
        GPIO.output(self.pin['PTT'], GPIO.HIGH)

    def power(self, level):
        self.logger.info("radio power %s" % level)
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
    with open('data/config.json') as fin:
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
        radio.play(config['frequencies']['APRS'], 'data/boatswain_whistle.wav')
    elif sys.argv[1] == "play":
        radio.play(config['frequencies']['APRS'], sys.argv[2])
    else:
        print("unknown")

# GPIO.cleanup() # cleanup all GPIO
