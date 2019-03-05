import os
import json
import time

from aprs import APRS
from modem import AFSK
from ublox import Ublox
from dorji import Dorji
from timers import Timers

def main():
    # setup
    with open('config.json') as fin:
        config = json.load(fin)
    data_dir = config["directories"]["data"] if "directories" in config and "data" in config["directories"] else "./data"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    aprs = APRS(config['callsign'], config['ssid'])
    modem = AFSK()
    gps = Ublox()
    radio = Dorji(config['pins'])
    radio.init()
    timers = Timers(config['timers'])
    exitFlag = False
    while not exitFlag:
      try:
        gps.loop()
        if timers.expired("APRS"):
          gpsdata = gps.get_data()
          frame = aprs.create_location_msg(gpsdata, "idoroseman.com", [])
          print gpsdata
          print frame
	  print frame.toString()
          modem.encode(frame.toString())
          modem.saveToFile(os.path.join(data_dir,'aprs.wav'))
          radio.freq(config['frequencies']['APRS'])
          radio.tx()
          os.system("aplay "+os.path.join(data_dir,'aprs.wav'))
          radio.rx()
        time.sleep(0.1)
      except KeyboardInterrupt:  # If CTRL+C is pressed, exit cleanly
        exitFlag = True
        gps.stop()
        break
    print "Done."

if __name__ == "__main__":
    main()
