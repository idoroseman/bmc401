from ax25 import ax25
from math import log

class APRS():
    def __init__(self, callsign, ssid=11, symbol='O'):
        self.callsign = callsign.upper()
        self.ssid = ssid
        self.symbol = symbol
        self.sequence_counter = 0

    def create_frame(self):
        return ax25(self.callsign, self.ssid, "APRS", 0, "WIDE1", 1, "WIDE2", 1)

    def create_location_msg(self, gps , comment, telemetry):
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
        cs = log(aprs_alt) / log(1.002) # altitude = 1.002^cs (in feet)
        frame.add_base91enc(cs, 2)
        frame.add_byte( 0x30 ) # Compression Type : current fix, NMEA GGA ( pos + alt ), origin = compressed
        frame.add_string(comment)
        # see http://he.fi/doc/aprs-base91-comment-telemetry.txt
        if telemetry:
            frame.add_byte('|')
            frame.add_base91enc(self.sequence_counter, 2)
            self.sequence_counter = (self.sequence_counter + 1) & 0x1FFF
            for i in range(len(telemetry)):
                frame.add_base91enc(telemetry[i],2)
            frame.add_byte('|')
        return frame

    def create_message_msg(self, to, msg):
        frame = self.create_frame()
        frame.add_byte(':')
        frame.add_string(to.ljust(9))
        frame.add_byte(':')
        frame.add_string(msg[:67])
        return frame

    def create_ssdv_msg(self, data):
        frame = self.create_frame()
        frame.add_byte('{')
        frame.add_byte('{')
        frame.add_byte('I')
        frame.add_string(data)
        return frame


