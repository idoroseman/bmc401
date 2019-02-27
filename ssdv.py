from aprs import aprs

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


class ssdv():
    def base91_len(self, l):
        return (l*16 + 26)/13

    def base91_encode(self,data):
        olen =  self.base91_len(len(data))
        out = ['\0'] * ((len(data)*4 / 3) +10)
        while len(data) % 3 != 0:
            data += '\0'
        i = 0
        j = 0
        while i<len(data):
            octet_a = ord(data[i])
            octet_b = ord(data[i+1])
            octet_c = ord(data[i+2])
            triple = (octet_a << 0x10) + (octet_b << 0x08) + octet_c
            i += 3
            out[j+0] = b64_table[(triple >> 3 * 6) & 0x3F]
            out[j+1] = b64_table[(triple >> 2 * 6) & 0x3F]
            out[j+2] = b64_table[(triple >> 1 * 6) & 0x3F]
            out[j+3] = b64_table[(triple >> 0 * 6) & 0x3F]
            j+=4

        b64_mod_table = [ 0, 2, 1 ]
        for i in range(b64_mod_table[len(data) % 3]):
           out[self.base01_len(len(data)) - 1 - i] = '='
        return  ''.join(out)

    def transmitOnRadio(self, msg):
        print msg.toString()

    def send(self):
        with open("/Users/ido/Projects/ssdv/output.bin", "rb") as f:
            a = aprs('4x6ub',13)
            while True:
                frame = f.read(256)
                if frame == '':
                    break

                pkt_base91 = self.base91_encode(frame[6:220])  # Sync byte, CRC and FEC of SSDV not transmitted
                msg = a.create_ssdv_msg( pkt_base91)
                self.transmitOnRadio(msg)



