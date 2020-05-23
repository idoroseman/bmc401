# balloon mission computer 4.01

this is a rewrite of my raspberry pi high altitude balloon software.
while previous version was a mix of c and bash scripts, this time it's written in python (as much as possible) so better data flow is possible

## new features include ##

2020:
- ported to python3
- raspberry pi zero hardware
- rewrote aprs modem in rust for speed

2019:
- SSDV over APRS
- better monitoring and build in tests
- web based remote control for ground operation

## installation prerequisits on raspberry pi
    sudo apt-get install git
    sudo apt-get install python3-pip
    sudo apt-get install python3-setuptools
    sudo apt-get install python3-rpi.gpio
    sudo apt-get install python3-smbus
    sudo apt-get install wiringpi
    sudo apt-get install python3-picamera
    sudo apt-get install python3-pil
    sudo apt-get install fswebcam
    pip3 install pyserial
    
### installing adafruit bmp085 support
    git clone https://github.com/adafruit/Adafruit_Python_BMP.git
    cd Adafruit_Python_BMP/
    sudo python3 setup.py install
    
### slowing down i2c baudrate
    sudo nano /boot/config.txt
find line

    dtparam=i2c_arm=on
and change to 

    dtparam=i2c_arm=on,i2c_arm_baudrate=32000

## building other needed software
    mkdir utils
    cd utils

* SSDV *
    git clone https://github.com/fsphil/ssdv
    cd ssdv
    make

* PiSSTV *
    git clone https://github.com/AgriVision/pisstv
    cd pisstv
    sudo apt-get install libgd-dev 
    sudo apt-get install libmagic-dev 
    gcc -lm -lgd -lmagic -o pisstv pisstv.c

