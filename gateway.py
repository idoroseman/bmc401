from base91 import encode, decode
import requests
import datetime
import base64
import binascii

# Offset	Name	Size	Description
# 0	    Sync Byte	    1	0x55 - May be preceded by one or more sync bytes
# 1	    Packet Type	    1	0x66 - Normal mode (224 byte packet + 32 byte FEC)
#                           0x67 - No-FEC mode (256 byte packet)
# 2	    Callsign	    4	Base-40 encoded callsign. Up to 6 digits
# 6	    Image ID	    1	Normally beginning at 0 and incremented by 1 for each new image
# 7	    Packet ID	    2	The packet number, beginning at 0 for each new image (big endian)
# 9	    Width	        1	Width of the image in MCU blocks (pixels / 16) 0 = Invalid
# 10	Height	        1	Height of the image in MCU blocks (pixels / 16) 0 = Invalid
# 11	Flags	        1	00qqqexx: 00 = Reserved, qqq = JPEG quality level (0-7 XOR 4), e = EOI flag (1 = Last Packet), xx = Subsampling Mode
# 12	MCU offset  	1	Offset in bytes to the beginning of the first MCU block in the payload, or 0xFF if none present
# 13	MCU index	    2	The number of the MCU pointed to by the offset above (big endian), or 0xFFFF if none present
# 15	Payload         205	Payload data
# 220	Checksum	    4	32-bit CRC
# 224	FEC	            32	Reed-Solomon forward error correction data. Normal mode only (0x66)

class aprs2ssdv():
    def __init__(self, callsign):
        self.packets = {}
        self.headers = {}
        self.callsign = callsign
        self.ssdv_url = "http://ssdv.habhub.org/api/v0/packets"

    def merge(self, header, i, j):
        pre = ''.join([chr(x) for x in [0x55, 0x66]])
        cs = ''.join([chr(x) for x in [0x02, 0x6B, 0x55, 0x8D ]])
        data =  pre+cs+header+i+j[:-1]
        crc = binascii.crc32(data[1:])
        data += chr((crc>>24) & 0xff)
        data += chr((crc>>16) & 0xff)
        data += chr((crc>>8) & 0xff)
        data += chr((crc) & 0xff)
        data += ''.join(['\0'] * 32) # fec
        return data

    def upload(self, packet):
        packet_dict = {
            "type": "packet",
            "packet": base64.b64encode(packet),
            "encoding": "base64",
            # Because .isoformat() doesnt give us the right format... (boo)
            "received": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "receiver": self.callsign,
        }
        r = requests.post(self.ssdv_url, json=packet_dict)
        print r,r.text

    def process(self, line):
        data = decode(line[3:])
        packet_type = line[2]
        image_id = data[0]
        packet_id = data[1] * 0x100 + data[2]
        w = data[3]
        h = data[4]
        flags = data[5]
        mcu_offset = data[6]
        mcu_index = data[7] * 0x100 + data[8]
        hash = "%4s%2s" % (image_id, packet_id)
        if hash not in self.packets:
            self.packets[hash] = {}
        if hash not in self.headers:
            self.headers[hash] = data[0:9]
        elif data[0:9] != self.headers[hash]:
            print "header ", data[0:9], self.headers[hash]
        self.packets[hash][packet_type] = data[9:]
        keys = "".join(self.packets[hash].keys())
        if keys == "IJ":
            packet = self.merge(self.headers[hash], self.packets[hash]['I'], self.packets[hash]['J'])
            self.upload(packet)
        elif keys == "IK":
            data = ''.join([chr(self.packets[hash]['I'][i] ^ self.packets[hash]['K'][i]) for i in range(len(self.packets[hash]['K']))])
            packet = self.merge(self.headers[hash], self.packets[hash]['I'], data)
            self.upload(packet)
        elif keys == "KJ":
            data = ''.join([chr(self.packets[hash]['J'][i] ^ self.packets[hash]['K'][i]) for i in range(len(self.packets[hash]['K']))])
            packet = self.merge(self.headers[hash], data, self.packets[hash]['J'])
            self.upload(packet)


########################################################################################################################

if __name__ == "__main__":
    a2s = aprs2ssdv('4x6ub')
    cnt = 0
    with open('data/ssdv.packets') as fin:
        while True:
            line = fin.readline()
            if line=="":
                break
            cnt += 1
            # emulate droped packets
            if cnt % 5 == 0:
                continue
            a2s.process(line)
