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
    sudo apt install git -y
    sudo apt install python3-pip python3-setuptools -y
    sudo apt install python3-rpi.gpio python3-smbus wiringpi -y
    sudo apt install python3-picamera python-opencv python3-pil fswebcam -y
    sudo apt-get install libatlas-base-dev
    
    sudo pip3 install numpy==1.21.6
    pip3 install pyserial
    pip3 install flask flask-cors flask-socketio flask-restful
    
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

##to auto start as system deamon:

    sudo cp bmc.service /etc/systemd/system
    sudo systemctl enable bmc.service

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

* aprs-tools

    mkdir aprs-tool
    cd aprs-tool
    wget https://github.com/idoroseman/aprs-tool/releases/download/0.1/aprs-encode
    chmod +x aprs-encode     

## both wifi client and access point
https://www.raspberryconnect.com/projects/65-raspberrypi-hotspot-accesspoints/183-raspberry-pi-automatic-hotspot-and-static-hotspot-installer

    SSID RPiHotspot 
    password 1234567890
    ssh pi@192.168.50.5
    http://192.168.50.5/
