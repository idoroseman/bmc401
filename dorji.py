#!/usr/bin/env python
import os
import sys
import time
import serial
import RPi.GPIO as GPIO

# Pin Definitions
pins = {
  'PTT'  : 17,  # LOW = TX, HIGH = RX
  'PD'   : 27,  # LOW = Sleep, HIHJ = Normal
  'HILO' : 22   # LOW = 0.5W, Float = 1W
  }

class dorji():
    def __init__(self,pins):
        self.pin = pins
	GPIO.setwarnings(False)
	GPIO.setmode(GPIO.BCM)

        GPIO.setup(self.pin['PD'], GPIO.OUT)
	GPIO.setup(self.pin['PTT'], GPIO.OUT)
	GPIO.setup(self.pin['HILO'], GPIO.OUT)

        os.system('gpio -g mode 18 alt5') # sets GPIO 18 pin to ALT 5 mode = GPIO_GEN1

	self.ser = serial.Serial(
            port='/dev/serial0',
            baudrate = 9600,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            timeout=1,
	    write_timeout=1
           )

        self.isOK = False
        self.init()


    def cmnd(self, data):
        try:
          while True:
            self.ser.write(data)
            time.sleep(1)
            x=self.ser.readline()
            print x
            if x.startswith('+') or x.startswith("S="):
                self.isOK = True
                break;
        except KeyboardInterrupt:
            pass

    def init(self):
        GPIO.output(self.pin['PTT'], GPIO.HIGH)
        GPIO.output(self.pin['PD'], GPIO.HIGH)
	GPIO.output(self.pin['HILO'], GPIO.LOW)
        self.cmnd('AT+DMOCONNECT\r\n')

    def scan(self, freq):
        self.cmnd("S+%.4f\r\n" % freq)

    def freq(self, freq):
        self.cmnd("AT+DMOSETGROUP=0,%.4f,%.4f,0000,4,0000\r\n" % (freq, freq))

    def tx(self):
        GPIO.output(self.pin['PD'], GPIO.HIGH)
        GPIO.output(self.pin['PTT'], GPIO.LOW)

    def rx(self):
        GPIO.output(self.pin['PD'], GPIO.HIGH)
        GPIO.output(self.pin['PTT'], GPIO.HIGH)

    def standby(self):
        GPIO.output(self.pin['PD'], GPIO.LOW)
        GPIO.output(self.pin['PTT'], GPIO.HIGH)

    def power(self, level):
        GPIO.setup(self.pin['HILO'], GPIO.OUT)
        if level == "high":
            GPIO.output(self.pin['HILO'], GPIO.HIGH)
        elif level == "low":
            GPIO.output(self.pin['HILO'], GPIO.LOW)

##################################################

if __name__ == "__main__":
    radio = dorji(pins)
    if len(sys.argv) == 1:
        print "no arguments"
    elif sys.argv[1] == "init":
        print "init"
        radio.init()
    elif sys.argv[1] == "scan":
        freq = float(sys.argv[2])
        print "scan %.4f" % freq
	radio.scan(freq)
    elif sys.argv[1] == "freq":
        freq = float(sys.argv[2])
        print "freq %.4f" % freq
        radio.freq(freq)
    elif sys.argv[1] == "tx":
        print "tx"
	radio.tx()
    elif sys.argv[1] == "rx":
        print "rx"
        radio.rx()
    elif sys.argv[1] == "stby":
        print "standby"
	radio.standby()
    elif sys.argv[1] == "power":
        print "power %s" % sys.argv[2]
        radio.power(sys.argv[2])
    else:
        print "unknown"

# GPIO.cleanup() # cleanup all GPIO

