import os

from aprs import APRS
from modem import AFSK
from ublox import ublox
from dorji import dorji

def main():
    # setup
    with open('config.json') as fin:
        config = json.load(fin)
    data_dir = config["directories"]["data"] if "directories" in config and "data" in config["directories"] else "./data"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    aprs = APRS(config['callsign'], config['ssid'])
    modem = AFSK()
    gps = ublox()
    radio = dorji()
    radio.init()
    timers = timers()
    exitFlag = False
    while not exitFlag:
      try:
        gps.loop()
        if timers.expired("APRS"):
          frame = aprs.create_location_msg(True, 32.061111, 34.874444, 100, "idoroseman.com", [])
          modem.encode(frame.toString())
          modem.saveToFile(os.path.join(data_dir,'aprs.wav'))
        time.sleep(5)
      except KeyboardInterrupt:  # If CTRL+C is pressed, exit cleanly
        exitFlag = True
        break
    print "Done."

if __name__ == "__main__":
    main()
