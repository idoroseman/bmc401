import os

from aprs import APRS
from modem import AFSK

data_dir = "./data"
def main():
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    aprs = APRS('4x6ub', 1)
    modem = AFSK()
    frame = aprs.create_location_msg(True, 32.061111, 34.874444, 100, "idoroseman.com", [])
    modem.encode(frame.toString())
    modem.saveToFile(os.path.join(data_dir,'aprs.wav'))


if __name__ == "__main__":
    main()