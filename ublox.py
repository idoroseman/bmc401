#!/usr/bin/python3
from traceback import print_exc
import threading
import logging
import math
import time
import io
import json
import fcntl
try:
    import RPi.GPIO as GPIO
except:
    print("no real gpio")
    from mockgpio import MockGPIO as GPIO
try:
    import smbus
except:
    print("error loading smbus")

verbose = False
printFix = False
im_lost = "lost"
im_good = "fix"
no_comm = "comm error"
no_i2c  = "i2c error"

#  Dynamic Model 6 – Airborne (aboce 12km)
setNavCmnd = [0xB5, 0x62, 0x06, 0x24, 0x24, 0x00, 0xFF, 0xFF, 0x06,
              0x03, 0x00, 0x00, 0x00, 0x00, 0x10, 0x27, 0x00, 0x00,
              0x05, 0x00, 0xFA, 0x00, 0xFA, 0x00, 0x64, 0x00, 0x2C,
              0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
              0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x16, 0xDC]
bus = 1
device = 0x42

#########################################################################
#                    comm thread
#########################################################################

# sudo bash -c "echo options i2c_bcm2708 baudrate=50000 > /etc/modprobe.d/i2c.conf"

class communicationThread(threading.Thread):
    def __init__(self, onNMEA, onUBLOX, onError):
        threading.Thread.__init__(self)
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        self.onNMEA = onNMEA
        self.onUBLOX = onUBLOX
        self.onError = onError

        # setup i2c
        print("init i2c")
        try:
            I2C_SLAVE = 0x0703
            self.fr = io.open("/dev/i2c-" + str(bus), "r+b", buffering=0)
            self.fw = io.open("/dev/i2c-" + str(bus), "w+b", buffering=0)
            # set device address
            fcntl.ioctl(self.fr, I2C_SLAVE, device)
            fcntl.ioctl(self.fw, I2C_SLAVE, device)
            self.isOk = True
        except Exception as x:
            self.onError(f"gps i2c error: {x}")
            self.isOk = False

        self.exitFlag = False
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

    def stop(self):
        self.exitFlag = True

    def send_bytes(self, buffer):
        data = bytearray(len(buffer))
        data[0:] = buffer[0:]
        try:
            self.fw.write(data)
        except Exception as x:
            self.logger.error(f"i2c write error: {x}")

    def read_byte(self):
        ch = 255
        while ch == 255:
            try:
                if self.exitFlag:
                    return 255
                ch = self.fr.read(1)
                if ch == 255:
                    time.sleep(0.1)
            except IOError as x:
                time.sleep(0.1)
        return ch[0]

    def calc_nmea_chksum(self, line):
        calc_cksum = 0
        for s in line[1:]:
            calc_cksum ^= ord(s)
        return hex(calc_cksum)

    def calc_ublox_chksum(self, buffer):
        l = buffer[4]
        a, b = 0, 0
        for x in buffer[2:6 + l]:
            a = (a + x) & 0xff
            b = (b + a) & 0xff
        return a & 0xff, b & 0xff

    def parse_nmea(self, line):
        if line.count('*') != 1:
            return
        msg, chksum = line.split('*')
        calc = self.calc_nmea_chksum(msg)
        if calc == "0x" + chksum:
            self.onNMEA(msg)

    def parse_ublox(self, buffer):
        a, b = self.calc_ublox_chksum(buffer)
        if a == buffer[-2] and b == buffer[-1]:
            self.onUBLOX(buffer)

    def run(self):
        self.logger.info("Starting Communication Thread")
        rxNMEA = False
        rxUBLOX = False
        response = ""
        ch = ' '
        while not self.exitFlag:
            try:
                prev_ch = ch
                ch = self.read_byte()
                if rxNMEA:
                    if ch in [10, 13]:
                        self.parse_nmea(response)
                        response = ""
                        rxNMEA = False
                    else:
                        response += chr(ch & 0x7f)
                elif rxUBLOX:
                    response.append(ch)
                    if len(response) >= 8 and len(response) == 8 + response[4]:
                        self.parse_ublox(response)
                        response = ""
                        rxUBLOX = False
                elif prev_ch == 0xB5 and ch == 0x62:
                    rxUBLOX = True
                    response = [prev_ch, ch]
                elif ch == ord('$'):
                    rxNMEA = True
                    response = chr(ch)
            except AttributeError:
                self.stop()
            except Exception as x:
                self.logger.exception(("Exception: %s" % x))
                print_exc()
        self.logger.info("Exiting Communication Thread")


#########################################################################
#                       handlers
#########################################################################

class Ublox():
    def __init__(self, cb=None):
        self.cb = cb

        self.isInFlightMode = False
        self.comm_thread = None

        self.lastFixTime = time.time()
        self.lastCommTime = time.time()
        self.lastAltTime = 0
        self.prev_alt = 0.0
        self.GPSDAT = {"status": "init", "navmode": "unknown",
                       "lat_raw":"0.00", "lat": "0.00", "lon_raw":"0.00", "lon": "0.00", "alt": "0",
                       "fixTime": "000000", "FixType": "?", "SatCount": 0,
                       "accentRate": 0, 'groundSpeed':"?", 'groundCourse':"?"}
        self.sim_alt = 30000 / 2.0
        self.sim_v = math.pi / (2 * 60 * 60)
        self.sim_t = 0.0

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)  # Broadcom pin-numbering scheme

    def bit(self):
        for retry in range(5):
          try:
            bus = smbus.SMBus(1)
            bus.read_byte(device)
            return False
          except NameError:
              return True
          except Exception as x:
            time.sleep(1)
        return True

    def gps_reset(self):
        if self.comm_thread is not None:
            self.comm_thread.stop()
        with open('assets/config.json') as fin:
            config = json.load(fin)
        self.logger.warning("GPS Reset!")
        GPIO.setup(config['pins']['GPS_RST'], GPIO.OUT)
        GPIO.output(config['pins']['GPS_RST'], GPIO.LOW)
        time.sleep(1)
        GPIO.output(config['pins']['GPS_RST'], GPIO.HIGH)
        self.isInFlightMode = False
        self.comm_thread = communicationThread(self.nmea_handler, self.ublox_handler, self.error_handler)
        self.comm_thread.start()

    def start(self):
        self.gps_reset()
        print("i2c bit:", "error" if self.bit() else "ok")


    def stop(self):
        self.comm_thread.stop()

    def get_data(self):
        return self.GPSDAT

    def set_status(self, new_status):
        if self.GPSDAT['status'] != new_status:
          self.logger.info("gps status changed from %s to %s" % (self.GPSDAT['status'], new_status))
        self.GPSDAT['status']=new_status

    def housekeeping(self):
        if not self.comm_thread.isOk:
            self.set_status( no_i2c )
            return
        if not self.isInFlightMode:
            self.logger.info("set flight mode !")
            self.comm_thread.send_bytes(setNavCmnd)
            time.sleep(5)
        elapsed = time.time() - self.lastFixTime
        if elapsed > 2 * 60:
            self.GPSDAT['SatCount'] = -1
            self.set_status( im_lost )
            self.update_files()
            self.lastFixTime = time.time()
            # check for hardware failure
            if time.time() - self.lastCommTime > 5 * 60:
                self.set_status( no_comm )
            if self.bit():
                self.set_status( no_i2c )
                self.gps_reset()

    def update_files(self, filename="gps"):
        try:
            self.sim_t += self.sim_v
#            self.logger.info( "sim %f %f %f" % (self.sim_v, self.sim_t, self.sim_alt*(1-math.cos(self.sim_t))))

            self.GPSDAT['fixTimeStr'] = self.GPSDAT['fixTime'][0:2] + ':' + self.GPSDAT['fixTime'][2:4] + ':' + self.GPSDAT['fixTime'][4:6]

            # Change latitue and longitude to decimal degrees format
            longitude = self.GPSDAT["lon_raw"] 
            latitude = self.GPSDAT["lat_raw"]
            # calculate
            degrees_lon = float(longitude[:3])
            fraction_lon = float(longitude[3:]) / 60
            degrees_lat = float(latitude[:2])
            fraction_lat = float(latitude[2:]) / 60
            DD_longitude = degrees_lon + fraction_lon  # longitude (decimal degrees)
            DD_latitude = degrees_lat + fraction_lat  # latitude (decimal degrees)
            self.GPSDAT['lat'] = DD_latitude
            self.GPSDAT['lon'] = DD_longitude
            if 'alt_raw' in self.GPSDAT:
                self.GPSDAT['alt'] = float(self.GPSDAT['alt_raw']) # + self.sim_alt * (1-math.cos(self.sim_t))
        except Exception as x:
            self.logger.exception(x)
            self.logger.error("bad assets while calc files")
            return

        if printFix:
          self.logger.info("-----------------")
          self.logger.info("Lat %.4f" % self.GPSDAT['lat'])
          self.logger.info("Lon %.4f" % self.GPSDAT['lon'])
          self.logger.info("Alt %s" % self.GPSDAT["alt"])
          self.logger.info("Fix Time %s" % self.GPSDAT['fixTimeStr'])
          self.logger.info("Status %s" % self.GPSDAT["status"])
          self.logger.info("Nav Mode %s" % self.GPSDAT["navmode"])
          self.logger.info("Fix Mode %s" % self.GPSDAT["FixType"])
          self.logger.info("satellites %s" % self.GPSDAT["SatCount"])
          self.logger.info("ascent rate %s" % self.GPSDAT["accentRate"])
          self.logger.info("ground course %s" % self.GPSDAT['groundCourse'])
          self.logger.info("ground speed %s" % self.GPSDAT['groundSpeed'])
          self.logger.info("")
        self.lastFixTime = time.time()

    def tokenize(self, tokens, titles):
        rv = {}
        for i, k in enumerate(titles):
          try:
            if i>=len(tokens) :
                break
            rv[k] = tokens[i]
          except Exception as x:
            self.logger.error(i,k)
            self.logger.error(",".join(tokens))
            self.logger.exception(x)
        return rv

    def parse_gnrmc(self, tokens):
        RMCDAT = self.tokenize(tokens,
                               ['strType', 'fixTime', 'status', 'lat_raw', 'latDir',
                                'lon_raw', 'lonDir', 'groundSpeed', 'groundCourse',
                                'date', 'mode'])
        if RMCDAT["lat_raw"] == "":
            return False
        for i, k in enumerate(['fixTime', 'lat_raw', 'latDir', 'lon_raw', 'lonDir', 'groundSpeed', 'groundCourse', 'date']):
            self.GPSDAT[k] = RMCDAT[k]
        return True

    def parse_gngll(self, tokens):
        GGADAT = self.tokenize(tokens,
                               ['strType', 
                                'lat_raw', 'latDir', 'lon_raw', 'lonDir',
                                'fixTime', 'status', 'modeInd'
                               ])
        if GGADAT["lat_raw"] == "":
            return False
        for i, k in enumerate(['fixTime', 'lat_raw', 'latDir', 'lon_raw', 'lonDir']):
            self.GPSDAT[k] = GGADAT[k]
        return True

    def parse_gngga(self, tokens):
        GGADAT = self.tokenize(tokens,
                               ['strType', 'fixTime',
                                'lat_raw', 'latDir', 'lon_raw', 'lonDir',
                                'fixQual', 'numSat', 'horDil',
                                'alt_raw', 'altUnit', 'galt', 'galtUnit',
                                'DPGS_updt', 'DPGS_ID'])
        if GGADAT["lat_raw"] == "":
            return False
        for i, k in enumerate(['fixTime', 'lat_raw', 'latDir', 'lon_raw', 'lonDir', 'alt_raw']):
            self.GPSDAT[k] = GGADAT[k]
        return True

    def parse_gngsa(self, tokens):
        self.GPSDAT["FixType"] = tokens[1] + tokens[2]
        count = 0
        for id in tokens[3:14]:
            if id != "":
                count += 1
        self.GPSDAT["SatCount"] = count
        return True

    def nmea_handler(self, line):
        if verbose:
            self.logger.debug("nmea:"+line)
        self.lastCommTime = time.time()
        tokens = line.split(',')
        cmnd = tokens[0][1:]
        if cmnd in ["GNTXT", "GLGSV", "GPGSV"]:
            pass
        elif cmnd == "GNRMC":
            if verbose:
              self.logger.debug(("fix:  %s" % line))
            if self.parse_gnrmc(tokens):
                self.set_status( im_good )
            self.update_files()
        elif cmnd in ["GNGLL","GPGLL"]:
            if verbose:
                self.logger.debug("fix:  %s" % line)
            if self.parse_gngll(tokens):
                self.set_status(im_good)
        elif cmnd == "GNGGA":
            if verbose:
                self.logger.debug(("fix:  %s" % line))
            if self.parse_gngga(tokens):
                self.set_status(im_good)
            try:
                try:
                  alt = float(self.GPSDAT["alt_raw"])
                except:
                  self.logger.error("bad alt %s replacing with %s" %(self.GPSDAT['alt_alt'], self.prev_alt))
                  alt = self.prev_alt
                  self.GPSDAT['alt_raw'] = self.prev_alt
                if abs(alt-self.prev_alt) > 10000:
                  alt = self.prev_alt
                now = time.time()
                delta_time = now - self.lastAltTime
                if self.lastAltTime == 0:
                    self.lastAltTime = now
                    self.prev_alt = alt
                    self.GPSDAT['accentRate'] = 0
                elif delta_time > 10:
                    delta_alt = float(self.GPSDAT["alt"]) - float(self.prev_alt)
                    accent = delta_alt / delta_time
                    if verbose:
                        self.logger.debug(("%s m / %s sec = %s" % (delta_alt, delta_time, accent)))
                    self.GPSDAT["accentRate"] = 0.7 * self.GPSDAT["accentRate"] + 0.3 * accent
                    self.lastAltTime = now
                    self.update_files()
            except:
                pass
        elif cmnd == "GNGSA":
            if verbose:
                self.logger.debug(("stts: %s" % line))
            self.parse_gngsa(tokens)
        else:
            if verbose:
                self.logger.debug(("nmea unparsed: %s" % line))

    def ublox_handler(self, buffer):
        ack = [181, 98, 5, 1, 2, 0, 6, 36, 50, 91]
        if buffer == ack:
            self.logger.debug("got ACK !")
            self.GPSDAT["navmode"] = "flight"
            self.isInFlightMode = True
            self.update_files()
        else:
            if verbose:
                self.logger.info(("ublox: %s" % buffer))

    def error_handler(self, status):
        pass

#########################################################################
#                      M A I N
#########################################################################

if __name__ == "__main__":
    printFix = True
    gps = Ublox()
    gps.start()
    while True:
        try:
            gps.housekeeping()
            print(gps.GPSDAT)
            time.sleep(5)
        except KeyboardInterrupt:  # If CTRL+C is pressed, exit cleanly
            gps.stop()
            break
        except Exception as x:
            print(x)
    print("Done.")
