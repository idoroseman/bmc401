from ax25 import ax25
from math import log

class APRS():
    def __init__(self, callsign, ssid=11, comment='', symbol='O'):
        self.callsign = callsign.upper()
        self.ssid = ssid
        self.symbol = symbol
        self.comment = comment
        self.sequence_counter = 0
        self.dest = "APE6UB"  # was "APRS"

    def create_frame(self):
        return ax25(self.callsign, self.ssid, self.dest, 0, "WIDE1", 1, "WIDE2", 1)

    def create_location_msg(self, gps , telemetry=None, status='00000000', comment=None ):
        if comment==None:
            comment=self.comment
        # see Chapter 9: Compressed Position Report Data Formats
        # Convert the min.dec coordinates to APRS compressed format
        aprs_lat = 900000000 - gps['lat'] * 10000000
        aprs_lat = aprs_lat / 26 - aprs_lat / 2710 + aprs_lat / 15384615
        aprs_lon = 900000000 + gps['lon'] * 10000000 / 2
        aprs_lon = aprs_lon / 26 - aprs_lon / 2710 + aprs_lon / 15384615
        #  convert from meter to feet
        aprs_alt = float(gps['alt']) * 32808 / 10000

        frame = self.create_frame()
        frame.add_byte('!') # real-time report without timestamp
        frame.add_byte('/') # Symbol Table Identifier
        frame.add_base91enc(aprs_lat, 4)
        frame.add_base91enc(aprs_lon, 4)
        frame.add_byte(self.symbol) # symbol code: BALLOON

        # Course / Speed
        try:
            course = float(gps['groundCourse'])
            speed = float(gps['groundSpeed'])
            c = course / 4
            if speed > 1:
              s = log(speed + 1) / log( 1.08 )
            else:
              s = 0
            frame.add_byte(33+int(c))
            frame.add_byte(33+int(s))
            frame.add_byte(0x20)
        except Exception as x:
            frame.add_string("   ")

        if aprs_alt > 0:
            frame.add_string("/A=%06d" % aprs_alt)
        #   cs = log(aprs_alt) / log(1.002) # altitude = 1.002^cs (in feet)
        #   frame.add_base91enc(cs, 2)
        #   frame.add_byte( 0x38 ) # Compression Type : current fix, NMEA GGA ( pos + alt ), origin = compressed
        # else:
        #   frame.add_string("   ")

        # see http://he.fi/doc/aprs-base91-comment-telemetry.txt
        if telemetry:
            frame.add_byte('|')
            frame.add_base91enc(self.sequence_counter, 2)
            self.sequence_counter = (self.sequence_counter + 1) & 0x1FFF
            for i in telemetry:
                frame.add_base91enc(telemetry[i],2)
            frame.add_base91enc(int(status, 2), 2)
            frame.add_byte('|')
        frame.add_string(comment)
        return frame

    def create_telem_data_msg(self, telemetry, status='00000000', alt=None, comment=None):
        if comment==None:
            comment=self.comment
        frame = self.create_frame()
        frame.add_byte('T')
        frame.add_byte('#')
        frame.add_string("%03d" % self.sequence_counter)
        self.sequence_counter = (self.sequence_counter + 1) & 0x1FFF
        frame.add_byte(',')
        for i in telemetry:
            frame.add_string(telemetry[i])
            frame.add_byte(',')
        frame.add_string(status)
        if alt is not None:
            frame.add_string("/A=%06d" % aprs_alt)
        frame.add_byte(' ')
        frame.add_string(comment)
        return frame

    def create_telem_name_msg(self, telemetry, binary_names = None):
        frame = self.create_frame()
        frame.add_byte(":")
        me = self.callsign + '-' + str(self.ssid)
        me = me.encode("ascii")
        frame.add_string(me.ljust(9))
        frame.add_byte(":")
        frame.add_string("PARM.")
        frame.add_string(",".join(telemetry.keys()))
        return frame

    def create_message_msg(self, to, msg):
        frame = self.create_frame()
        frame.add_byte(':')
        frame.add_string(to.ljust(9))
        frame.add_byte(':')
        frame.add_string(msg[:67])
        return frame

    def create_ssdv_msg(self, id, data):
        frame = self.create_frame()
        frame.add_byte('{')
        frame.add_byte('{')
        frame.add_byte(id)
        frame.add_string(data)
        return frame


if __name__ == "__main__":
    from modem import AFSK
    gpsdata = {'status': 'fix',
               'latDir': 'N',
               'FixType': 'A3',
               'fixTime': '163018.00',
               'lat_raw': '3203.79986',
               'lat': 32.063331,
               'alt': 129.7,
               'navmode': 'flight',
               'lonDir': 'E',
               'groundSpeed': '36.2',
               'lon': 34.87216566666667,
               'SatCount': 4,
               'groundCourse': '123',
               'lon_raw': '03452.32994',
               'fixTimeStr': '16:30',
               'accentRate': 0.40599678574441816
               }
    telemetry = {'Satellites':4,
	     'TemperatureIn':26,
             'TemperatureOut':26,
             'Pressure':1024,
             'Battery':5 }
    aprs = APRS('4x6ub', 11)
    frame = aprs.create_location_msg(gpsdata, "idoroseman.com", telemetry)
    #frame = aprs.create_telem_name_msg(telemetry)
    # print frame.toString()
    modem = AFSK()
    modem.encode(frame)
    modem.saveToFile('data/aprs.wav')

