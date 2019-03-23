import os
import json
import time
import RPi.GPIO as GPIO

from aprs import APRS
from modem import AFSK
from ublox import Ublox
from dorji import Dorji
from timers import Timers
from sensors import Sensors
from camera import Camera
from ssdv import SSDV
from sstv import SSTV
from webserver import WebServer

def calc_status_bits(gpsdata, sensordata):
    bits = [ gpsdata['status'] == "i2c error",
             gpsdata['status'] == "comm error",
             gpsdata['status'] != 'fix',
             False,
             False,
             False,
             False,
             False ]
    return ''.join(['1' if val else '0' for val in bits])

def main():
    # setup
    with open('data/config.json') as fin:
        config = json.load(fin)
    images_dir = config["directories"]["images"] if "directories" in config and "images" in config["directories"] else "./images"
    tmp_dir = config["directories"]["tmp"] if "directories" in config and "tmp" in config["directories"] else "./tmp"

    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)

    GPIO.setmode(GPIO.BCM)  # Broadcom pin-numbering scheme
    GPIO.setup(config['pins']['BUZZER'], GPIO.OUT)

    aprs = APRS(config['callsign'], config['ssid'], "idoroseman.com")
    modem = AFSK()
    gps = Ublox()
    gps.start()
    radio = Dorji(config['pins'])
    radio.init()
    timers = Timers(config['timers'])
    sensors = Sensors()
    cam = Camera()
    ssdv = SSDV(config['callsign'], config['ssid'])
    sstv = SSTV()
    webserver = WebServer()
    radio.play(config['frequencies']['APRS'], 'data/boatswain_whistle.wav')

    timers.handle({"APRS": True, "SSDV": True, "SSTV": False, "BUZZER":True}, [])

    exitFlag = False
    telemetry = {}
    while not exitFlag:
      try:
        gps.loop()
        gpsdata = gps.get_data()
        sensordata = sensors.get_data()
        status_bits = calc_status_bits(gpsdata, sensordata)
        telemetry['Satellites'] = gpsdata['SatCount']
        telemetry['outside_temp'] = sensordata['outside_temp']
	telemetry['inside_temp'] = sensordata['inside_temp']
        telemetry['barometer'] = sensordata['barometer']
        telemetry['battery'] = 0
	webserver.update(gpsdata, sensordata)
        state, triggers = webserver.loop(timers.get_state())
        timers.handle(state, triggers)

        if timers.expired("APRS"):
            if gpsdata['status'] == "fix":
                print "sending location"
                frame = aprs.create_location_msg(gpsdata, telemetry, status_bits)
            else:
                print "sending only telemetry"
                frame = aprs.create_telem_data_msg(telemetry, status_bits)
            modem.encode(frame)
            modem.saveToFile(os.path.join(tmp_dir,'aprs.wav'))
            radio.play(config['frequencies']['APRS'], os.path.join(tmp_dir,'aprs.wav'))

        if timers.expired("APRS-META"):
            frame = aprs.create_telem_name_msg(telemetry)
            modem.encode(frame)
            modem.saveToFile(os.path.join(tmp_dir,'aprs.wav'))
            radio.play(config['frequencies']['APRS'], os.path.join(tmp_dir,'aprs.wav'))

	if timers.expired("Capture"):
            cam.capture()
            cam.resize((320, 256))
            cam.overlay(config['callsign'], gpsdata, sensordata)
            cam.saveToFile(os.path.join(tmp_dir,'cam1.jpg'))

        if timers.expired("SSTV"):
            cam.capture()
            cam.archive()
            cam.resize((320, 256))
            cam.overlay(config['callsign'], gpsdata, sensordata)
            cam.saveToFile(os.path.join(tmp_dir,'cam1.jpg'))
            sstv.image = cam.image
            sstv.process()
            end_time = time.time()
            sstv.saveToFile(os.path.join(tmp_dir, 'sstv.wav'))
            radio.play(config['frequencies']['SSTV'], os.path.join(tmp_dir, 'sstv.wav'))

        if timers.expired("SSDV"):
            cam.capture()
            cam.archive()
            cam.resize((320, 256))
            cam.overlay(config['callsign'], gpsdata, sensordata)
            cam.saveToFile(os.path.join(tmp_dir,'cam1.jpg'))
            ssdv.convert('tmp/cam1.jpg', 'tmp/image.ssdv')
            packets, raw = ssdv.prepare(os.path.join(tmp_dir, "image.ssdv"))
            modem.encode(packets)
            modem.saveToFile(os.path.join(tmp_dir, 'ssdv.wav'))
            radio.play(config['frequencies']['APRS'], os.path.join(tmp_dir, 'ssdv.wav'))

        if timers.expired("BUZZER"):
            GPIO.output(config['pins']['BUZZER'], GPIO.HIGH)
            time.sleep(1)
            GPIO.output(config['pins']['BUZZER'], GPIO.LOW)
            time.sleep(1)

        time.sleep(1)

      except KeyboardInterrupt:  # If CTRL+C is pressed, exit cleanly
        exitFlag = True
        gps.stop()
        break
    print "Done."

if __name__ == "__main__":
    main()
