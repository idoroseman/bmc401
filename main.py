import os
import json
import time

from aprs import APRS
from modem import AFSK
from ublox import Ublox
from dorji import Dorji
from timers import Timers
from sensors import Sensors
from camera import Camera
from ssdv import SSDV
from sstv import SSTV

def calc_status_bits(gpsdata, sensordata):
    bits = [ gpsdata['status'] == "i2c error",
             gpsdata['status'] == "comm error",
             False,
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

    exitFlag = False
    telemetry = {}
    while not exitFlag:
      try:
        gps.loop()
        gpsdata = gps.get_data()
        sensordata = sensors.get_data()
        status_bits = calc_status_bits(gpsdata, sensordata)
        telemetry['Satellites'] = gpsdata['SatCount']
        telemetry['TemperatureOut'] = sensors.read_outside_temp()

        if timers.expired("APRS"):
            if gpsdata['status'] == "fix":
                print "sending location"
                frame = aprs.create_location_msg(gpsdata, telemetry)
            else:
                print "sending only telemetrt"
                frame = aprs.create_telem_data_msg(telemetry, status_bits)
            modem.encode(frame)
            modem.saveToFile(os.path.join(tmp_dir,'aprs.wav'))
            radio.freq(config['frequencies']['APRS'])
            radio.tx()
            os.system("aplay "+os.path.join(tmp_dir,'aprs.wav'))
            radio.rx()

        if timers.expired("APRS-META"):
            frame = aprs.create_telem_name_msg(telemetry)
            modem.encode(frame)
            modem.saveToFile(os.path.join(tmp_dir,'aprs.wav'))
            radio.freq(config['frequencies']['APRS'])
            radio.tx()
            os.system("aplay "+os.path.join(tmp_dir,'aprs.wav'))
            radio.rx()

        if timers.expired("SSTV"):
            cam.capture()
            cam.archive()
            cam.resize((320, 256))
            cam.overlay(config['callsign'], gpsdata, sensordata)
            sstv.image = cam.image
            sstv.process()
            end_time = time.time()
            sstv.saveToFile(os.path.join(tmp_dir, 'sstv.wav'))
            radio.freq(config['frequencies']['SSTV'])
            radio.tx()
            os.system("aplay " + os.path.join(tmp_dir, 'sstv.wav'))
            radio.rx()

        if timers.expired("SSDV"):
            cam.capture()
            cam.archive()
            cam.resize((320, 256))
            cam.overlay(config['callsign'], gpsdata, sensordata)
            cam.saveToFile(os.path.join(tmp_dir,'ssdv.jpg'))
            ssdv.convert('tmp/ssdv.jpg', 'tmp/image.ssdv')
            packets, raw = ssdv.prepare(os.path.join(tmp_dir, "image.ssdv"))
            modem.encode(packets)
            modem.saveToFile(os.path.join(tmp_dir, 'ssdv.wav'))
            radio.freq(config['frequencies']['APRS'])
            radio.tx()
            os.system("aplay " + os.path.join(tmp_dir, 'ssdv.wav'))
            radio.rx()

        time.sleep(1)

      except KeyboardInterrupt:  # If CTRL+C is pressed, exit cleanly
        exitFlag = True
        gps.stop()
        break
    print "Done."

if __name__ == "__main__":
    main()
