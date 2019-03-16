
class ax25():

    def __init__(self, src_callsign, src_ssid, dest_callsign, dest_ssid, path1, ttl1, path2, ttl2):
        self.frame = ''
        self.add_callsign(dest_callsign, dest_ssid)
        self.add_callsign(src_callsign, src_ssid)
        self.add_callsign(path1, ttl1)
        self.add_callsign(path2, ttl2)
        self.mark_end_of_callsigns()
        self.add_byte(0x03) # Control: 0x03 = APRS-UI frame
        self.add_byte(0xF0) # Protocol ID: 0xF0 = no layer 3 data

    def add_callsign(self, callsign, ssid):
        for i in callsign.ljust(6):
            self.frame += chr(ord(i) << 1)
        self.frame += chr((48+ssid) << 1)

    def mark_end_of_callsigns(self):

        self.frame= self.frame[:-1] + chr(ord(self.frame[-1]) | 0x01)

    def add_byte(self, v):
        if isinstance(v, int):
            self.frame += chr(v)
        else :
            self.frame += v[0]

    def add_string(self, s):
        self.frame += str(s)

    def add_base91enc(self, value, length):
        rv = ''
        for i in range(length):
          rv = chr(int(value) % 91 + 33) + rv
          value /= 91
        self.frame += rv

    def add_crc(self):
        pass

    def calc_crc(self):
        CRC = 0xffff
        for s in self.frame:
            CRC ^= ord(s)

            for j in range(8):
                if (CRC & 1):
                    CRC = (CRC >> 1) ^ 0x8408
                else:
                    CRC >>= 1
        return chr(~CRC & 0xff) +  chr(~(CRC >> 8) & 0xff)


    def toString(self):
        return  self.frame + self.calc_crc() 


