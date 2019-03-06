#!/usr/bin/python
from traceback import print_exc
import threading
import time
import io
import fcntl
try:
    import smbus
except:
    pass

verbose = False
printFix = False
im_lost = "lost"
im_good = "fix"
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
    def __init__(self, onNMEA, onUBLOX):
        threading.Thread.__init__(self)
        self.onNMEA = onNMEA
        self.onUBLOX = onUBLOX
        # setup i2c
        I2C_SLAVE = 0x0703
        self.fr = io.open("/dev/i2c-" + str(bus), "r+b", buffering=0)
        self.fw = io.open("/dev/i2c-" + str(bus), "w+b", buffering=0)
        # set device address
        fcntl.ioctl(self.fr, I2C_SLAVE, device)
        fcntl.ioctl(self.fw, I2C_SLAVE, device)
        self.exitFlag = False

    def stop(self):
        self.exitFlag = True

    def send_bytes(self, buffer):
        data = bytearray(len(buffer))
        data[0:] = buffer[0:]
        try:
            self.fw.write(data)
        except:
            print("i2c write error")

    def read_byte(self):
        ch = 255
        while ch == 255:
            try:
                if self.exitFlag:
                    return ch
                ch = self.fr.read(1)
                if ch == 255:
                    time.sleep(0.1)
            except IOError as x:
                time.sleep(0.1)
        return ch

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
        print "Starting Communication Thread"
        rxNMEA = False
        rxUBLOX = False
        response = ""
        ch = ' '
        while not self.exitFlag:
            try:
                prev_ch = ch
                ch = self.read_byte()
                if rxNMEA:
                    if ch == '\n' or ch == '\r':
                        self.parse_nmea(response)
                        response = ""
                        rxNMEA = False
                    else:
                        response += chr(ord(ch) & 0x7f)
                elif rxUBLOX:
                    response.append(ord(ch))
                    if len(response) >= 8 and len(response) == 8 + response[4]:
                        self.parse_ublox(response)
                        response = ""
                        rxUBLOX = False
                elif ord(prev_ch) == 0xB5 and ord(ch) == 0x62:
                    rxUBLOX = True
                    response = [ord(prev_ch), ord(ch)]
                elif ch == '$':
                    rxNMEA = True
                    response = ch
            except Exception as x:
                print("Exception: %s" % x)
                print_exc()
        print "Exiting Communication Thread"


#########################################################################
#                       handlers
#########################################################################

class Ublox():
    def __init__(self, cb=None):
        self.cb = cb

        self.isInFlightMode = False

        self.lastFixTime = time.time()
        self.lastAltTime = 0
        self.prev_alt = 0.0
        self.GPSDAT = {"status": "init", "navmode": "unknown",
                       "lat_raw":"0.00", "lat": "0.00", "lon_raw":"0.00", "lon": "0.00", "alt": "0",
                       "fixTime": "000000", "FixType": "?", "SatCount": 0,
                       "accentRate": 0, 'groundSpeed':"?", 'groundCourse':"?"}

    def start(self):
        if self.bit() == 0:
          self.comm_thread = communicationThread(self.nmea_handler, self.ublox_handler)
          self.comm_thread.start()
        else:
          raise Exception("GPS not connected")

    def bit(self):
        rv = 0
        try:
            bus = smbus.SMBus(1)
            bus.read_byte(device)
        except:
            rv |= 0x01
        return rv

    def stop(self):
        self.exitFlag = True
        self.comm_thread.stop()

    def get_data(self):
        return self.GPSDAT

    def set_status(self, new_status):
        if self.GPSDAT['status'] != new_status:
          print "gps status changed from %s to %s" % (self.GPSDAT['status'], new_status)
        self.GPSDAT['status']=new_status

    def loop(self):
        if not self.isInFlightMode:
            print("set flight mode !")
            self.comm_thread.send_bytes(setNavCmnd)
            time.sleep(1)
        elapsed = time.time() - self.lastFixTime
        if elapsed > 2 * 60:
            self.set_status( im_lost )
            self.update_files()
            self.lastFixTime = time.time()

    def update_files(self, filename="gps"):
        try:
            self.GPSDAT['fixTimeStr'] = self.GPSDAT['fixTime'][0:2] + ':' + self.GPSDAT['fixTime'][2:4]

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
            self.GPSDAT['alt'] = float(self.GPSDAT['alt'])
        except Exception as x:
            print ("bad data while calc files: %s" % x)
            return

        if printFix:
          print("-----------------")
          print("Lat %.4f" % self.GPSDAT['lat'])
          print("Lon %.4f" % self.GPSDAT['lon'])
          print("Alt %s" % self.GPSDAT["alt"])
          print("Fix Time %s" % self.GPSDAT['fixTimeStr'])
          print("Status %s" % self.GPSDAT["status"])
          print("Nav Mode %s" % self.GPSDAT["navmode"])
          print("Fix Mode %s" % self.GPSDAT["FixType"])
          print("satellites %s" % self.GPSDAT["SatCount"])
          print("ascent rate %s" % self.GPSDAT["accentRate"])
          print("ground course %s" % self.GPSDAT['groundCourse'])
          print("ground speed %s" % self.GPSDAT['groundSpeed'])
          print
        lastFixTime = time.time()

    def tokenize(self, tokens, titles):
        rv = {}
        for i, k in enumerate(titles):
            if i>=len(tokens) :
                break
            rv[k] = tokens[i]
        return rv

    def parse_gnrmc(self, tokens):
        RMCDAT = self.tokenize(tokens,
                               ['strType', 'fixTime', 'status', 'lat_raw', 'latDir',
                                'lon_raw', 'lonDir', 'groundSpeed', 'groundCourse',
                                'date', 'mode'])
        if RMCDAT["lat_raw"] == "":
            return False
        for i, k in enumerate(['fixTime', 'lat_raw', 'latDir', 'lon_raw', 'lonDir', 'groundSpeed', 'groundCourse']):
            self.GPSDAT[k] = RMCDAT[k]
        return True

    def parse_gngga(self, tokens):
        GGADAT = self.tokenize(tokens,
                               ['strType', 'fixTime',
                                'lat_raw', 'latDir', 'lon_raw', 'lonDir',
                                'fixQual', 'numSat', 'horDil',
                                'alt', 'altUnit', 'galt', 'galtUnit',
                                'DPGS_updt', 'DPGS_ID'])
        if GGADAT["lat_raw"] == "":
            return False
        for i, k in enumerate(['fixTime', 'lat_raw', 'latDir', 'lon_raw', 'lonDir', 'alt']):
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
        tokens = line.split(',')
        cmnd = tokens[0][1:]
        if cmnd == "GNTXT":
            pass
        elif cmnd == "GNRMC":
            if verbose:
              print("fix:  %s" % line)
            if self.parse_gnrmc(tokens):
                self.set_status( im_good )
            self.update_files()
        elif cmnd == "GNGGA":
            if verbose:
		print("fix:  %s" % line)
            if self.parse_gngga(tokens):
                self.set_status(im_good)
            now = time.time()
            delta_time = now - self.lastAltTime
            if self.lastAltTime == 0:
                self.lastAltTime = now
                self.prev_alt = float(self.GPSDAT["alt"])
                self.GPSDAT['accentRate'] = 0
            elif delta_time > 10:
                delta_alt = float(self.GPSDAT["alt"]) - self.prev_alt
                accent = delta_alt / delta_time
                if verbose:
                    print("%s m / %s sec = %s" % (delta_alt, delta_time, accent))
                self.GPSDAT["accentRate"] = 0.7 * self.GPSDAT["accentRate"] + 0.3 * accent
                self.lastAltTime = now
                self.update_files()
        elif cmnd == "GNGSA":
            if verbose:
		print("stts: %s" % line)
            self.parse_gngsa(tokens)
        else:
            if verbose:
                print("nmea: %s" % line)

    def ublox_handler(self, buffer):
        ack = [181, 98, 5, 1, 2, 0, 6, 36, 50, 91]
        if buffer == ack:
            print("got ACK !")
            self.GPSDAT["navmode"] = "flight"
            self.isInFlightMode = True
            self.update_files()
        else:
            if verbose:
                print("ublox: %s" % buffer)


#########################################################################
#                      M A I N
#########################################################################

if __name__ == "__main__":
    printFix = True
    gps = Ublox()
    gps.start()
    while True:
        try:
            gps.loop()
            time.sleep(5)
        except KeyboardInterrupt:  # If CTRL+C is pressed, exit cleanly
            gps.stop()
            break
        except Exception as x:
            print x
    print "Done."
