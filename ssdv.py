from aprs import APRS
from base91 import encode, decode
import subprocess

# see http://tt7hab.blogspot.co.il/2017/03/ssdv-slow-scan-digital-video.html

b64_table = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H',
             'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P',
             'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X',
             'Y', 'Z', 'a', 'b', 'c', 'd', 'e', 'f',
             'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n',
             'o', 'p', 'q', 'r', 's', 't', 'u', 'v',
             'w', 'x', 'y', 'z', '0', '1', '2', '3',
             '4', '5', '6', '7', '8', '9', '+', '/']

def bytearray_to_int(b):
    rv = 0;
    for i in b:
        rv = rv*256 + ord(i)
    return rv

def base40_decode(data):
    rv = ''
    while data>0:
        s = data % 40
        data /= 40
        if s == 0:
            rv += '-'
        elif s < 11:
            rv += chr(48 + s - 1)
        elif s < 14:
            rv += '-'
        else:
            rv += chr(65 + s - 14)
    return rv

def parse_ssdv_bin():
    with open("/Users/ido/Projects/ssdv/output.bin", "rb") as f:
        count = 0
        while True:
            header = f.read(15)
            if header == '':
                break
            packet = {}
            packet['header'] = header
            packet['sync'] = ord(header[0])
            packet['packetType'] = ord(header[1])
            packet['callsign'] = base40_decode(bytearray_to_int(header[2:6]))
            packet['imageId'] = ord(header[6])
            packet['packetId'] = bytearray_to_int(header[7:9])
            packet['width'] = ord(header[9])
            packet['height'] = ord(header[10])
            packet['flags'] = ord(header[11])
            packet['mcuOffset'] = ord(header[12])
            packet['mcuIndex'] = bytearray_to_int(header[13:15])

            if ord(header[1]) == 0x66: # noremal
                packet['data'] = f.read(237)
            elif ord(header[1]) == 0x67: # no-FEC
                packet['data'] = f.read(205)
            packet['crc'] = f.read(4)


    # Prepare the output JPEG tables

SSDV_ERROR       = -1
SSDV_OK          = 0
SSDV_FEED_ME     = 1
SSDV_HAVE_PACKET = 2
SSDV_BUFFER_FULL = 3
SSDV_EOI         = 4

SSDV_TYPE_NORMAL = 0
SSDV_TYPE_NOFEC  = 1

def ssdv_enc_init(self, type, callsign, image_id):
    self.image_id = image_id
    self.callsign = self.encode_callsign(callsign)
    self.mode = S_ENCODING;
    self.type = type;
    self.ssdv_set_packet_conf(s)
    self.ddqt[0] = dtblcpy(s, std_dqt0, sizeof(std_dqt0));
    self.ddqt[1] = dtblcpy(s, std_dqt1, sizeof(std_dqt1));
    self.ddht[0][0] = dtblcpy(s, std_dht00, sizeof(std_dht00));
    self.ddht[0][1] = dtblcpy(s, std_dht01, sizeof(std_dht01));
    self.ddht[1][0] = dtblcpy(s, std_dht10, sizeof(std_dht10));
    self.ddht[1][1] = dtblcpy(s, std_dht11, sizeof(std_dht11));

    return self.SSDV_OK

def encode_ssdv(self):
    self.ssdv_enc_init( self.SSDV_TYPE_NORMAL, "4X6UB", 1)
    while True:
        c, pkt = self.ssdv_enc_get_packet()
        while c == self.SSDV_FEED_ME:
            b = self.file_in.read(128)
            if b == '' :
                break
            self.inp = b

        if c == self.SSDV_EOI:
            break
        elif c != self.SSDV_OK:
            return


class SSDV():
    def __init__(self, callsign, ssid):
        self.callsign = callsign
        self.ssid = ssid
        self.counter = 0

    def convert(self, src, dest):
        self.counter += 1
        cmd = 'utils/ssdv/ssdv -e -i %s /home/pi/bmc401/%s /home/pi/bmc401/%s' % (self.counter, src, dest)
        out = subprocess.check_output(cmd, shell=True)
        print(out)

    def prepare(self,filename):
        # 0	Sync Byte	1	0x55
        # 1	Packet Type	1	0x66 Normal mode, 0x67 No-FEC mode.
        # 2	Callsign	4	Base-40 encoded. Up to 6 characters.
        # 6	Image ID	1	Incremented by 1 for each new image.
        # 7	Packet ID	2	The packet number within the image.
        # 9	    Width	1	Width of the image in MCU blocks (pixels / 16).
        # 10	Height	1	Height of the image in MCU blocks (pixels / 16).
        # 11	Flags	1	[7:6] reserved, [5:3] JPEG quality, [2] EOI flag, [1:0] subsampling
        # 12	MCU Offset	1	Offset (bytes) to the beginning of the first MCU block in payload.
        # 13	MCU Index	2	The number of the MCU pointed to by the offset above.
        # 15	Payload	    205	Payload data.
        # 220	Checksum	4	32-bit CRC.
        # 224	FEC	32	Reed-Solomon forward error correction data.
        rv = []
        raw = []
        with open(filename, "rb") as f:
            aprs = APRS(self.callsign, self.ssid)
            while True:
                frame = f.read(256)
                if frame == '':
                    break
                # Sync byte, CRC and FEC of SSDV not transmitted
                # payload is 205 bytes, so I frame gets 103 bytes, J gets 102 bytes and a \0
                header = frame [6: 15]
                dataI = frame[15:15+103]
                dataJ = frame[15+103:15+205] + '\0'
                dataK = ''.join([chr(ord(dataI[i]) ^ ord(dataJ[i])) for i in range(len(dataI))])
                pkt_base91 = encode(header+dataI)
                msg = aprs.create_ssdv_msg('I', pkt_base91)
                raw.append("{{I"+pkt_base91)
                rv.append(msg)
                pkt_base91 = encode(header+dataJ)
                msg = aprs.create_ssdv_msg('J', pkt_base91)
                raw.append("{{J"+pkt_base91)
                rv.append(msg)
                pkt_base91 = encode(header+dataK)
                msg = aprs.create_ssdv_msg('K', pkt_base91)
                raw.append("{{K"+pkt_base91)
                rv.append(msg)

        return rv, raw





if __name__ == "__main__":
    from modem import AFSK
    from camera import Camera

    ssdv = SSDV('4x6ub', 11)
    modem = AFSK()
    cam = Camera()
    cam.capture()
    cam.resize((320,256))
    gpsdata = {'lat': 32.063331,
               'lon': 34.87216566666667,
               'alt': 129.7
               }
    cam.overlay('4x6ub', gpsdata)
    cam.saveToFile('ssdv')
    ssdv.convert('images/ssdv.jpg', 'data/image.ssdv')
    packets, raw = ssdv.prepare("data/image.ssdv")
    modem.encode(packets)
    modem.saveToFile('data/ssdv.wav')
    # with open('data/ssdv.packets', "wb") as f:
    #     for p in raw:
    #         f.write(bytearray(p+'\n'))
    print len(packets),"packets"

