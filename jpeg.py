from enum import Enum

# see:
# https://www.w3.org/Graphics/JPEG/itu-t81.pdf
# https://github.com/sullerandras/nanojpeg-python/blob/master/nanojpeg.py
# https://en.wikipedia.org/wiki/JPEG#Syntax_and_structure
# http://www.impulseadventure.com/photo/jpeg-huffman-coding.html

class Marker(Enum):
    # Start Of Frame markers, non-differential, Huffman coding
    SOF0 = 0xFFC0 # Baseline DCT
    SOF1 = 0xFFC1  # Extended sequential DCT
    SOF2 = 0xFFC2 # Progressive DCT
    SOF3 = 0xFFC3 # Lossless (sequential)
    # Start Of Frame markers, differential, Huffman coding
    SOF5 = 0xffc5 # Differential sequential DCT
    SOF6 = 0xFFC6 # Differential progressive DCT
    SOF7 = 0xFFC7 # Differential lossless (sequential)
    # Start Of Frame markers, non-differential, arithmetic coding
    SOF8 = 0xFFC8 # Reserved for JPEG extensions
    SOF9 = 0xFFC9 # Extended sequential DCT
    SOFA = 0xFFCA # Progressive DCT
    SOFB = 0xFFCB # Lossless (sequential)
    # Start Of Frame markers, differential, arithmetic coding
    SOFD = 0xffcd # Differential sequential DCT
    SOFE = 0xFFCE # Differential progressive DCT
    SOFF = 0xFFCF # Differential lossless (sequential)
    # Huffman table specification
    DHT = 0xFFC4
    # Arithmetic coding conditioning specification
    DAC = 0xFFCC
    # Restart interval termination
    RST0 = 0xFFD0
    RST1 = 0xFFD1
    RST2 = 0xFFD2
    RST3 = 0xFFD3
    RST4 = 0xFFD4
    RST5 = 0xFFD5
    RST6 = 0xFFD6
    RST7 = 0xFFD7
    # Other markers
    SOI = 0xFFD8 # Start of image
    EOI = 0xFFD9 # End of image
    SOS = 0xFFDA # Start of scan
    DQT = 0xFFDB # Define quantization table(s)
    DNL = 0xFFDC # Define number of lines
    DRI = 0xFFDD # Define restart interval
    DHP = 0xFFDE # Define hierarchical progression
    EXP = 0xFFDF # Expand reference component(s)
    # Reserved for application segments
    APP0 = 0xFFE0
    APP1 = 0xFFE1
    APP2 = 0xFFE2
    APP3 = 0xFFE3
    APP4 = 0xFFE4
    APP5 = 0xFFE5
    APP6 = 0xFFE6
    APP7 = 0xFFE7
    APP8 = 0xFFE8
    APP9 = 0xFFE9
    APPA = 0xFFEA
    APPB = 0xFFEB
    APPC = 0xFFEC
    APPD = 0xFFED
    APPE = 0xFFEE
    APPF = 0xFFEF
    # Reserved for JPEG extensions
    JPG0 = 0xFFF0
    JPG1 = 0xFFF1
    JPG2 = 0xFFF2
    JPG3 = 0xFFF3
    JPG4 = 0xFFF4
    JPG5 = 0xFFF5
    JPG6 = 0xFFF6
    JPG7 = 0xFFF7
    JPG8 = 0xFFF8
    JPG9 = 0xFFF9
    JPGA = 0xFFFA
    JPGB = 0xFFFB
    JPGC = 0xFFFC
    JPGD = 0xFFFD

    COM = 0xFFFE # Comment



# Quantisation tables

# Standard Huffman tables
ac0 = {1: [], 2: [1, 2], 3: [3], 4: [0, 4, 17], 5: [5, 18, 33], 6: [49, 65], 7: [6, 19, 81, 97], 8: [7, 34, 113], 9: [20, 50, 129, 145, 161], 10: [8, 35, 66, 177, 193], 11: [21, 82, 209, 240], 12: [36, 51, 98, 114], 13: [], 14: [], 15: [130], 16: [9, 10, 22, 23, 24, 25, 26, 37, 38, 39, 40, 41, 42, 52, 53, 54, 55, 56, 57, 58, 67, 68, 69, 70, 71, 72, 73, 74, 83, 84, 85, 86, 87, 88, 89, 90, 99, 100, 101, 102, 103, 104, 105, 106, 115, 116, 117, 118, 119, 120, 121, 122, 131, 132, 133, 134, 135, 136, 137, 138, 146, 147, 148, 149, 150, 151, 152, 153, 154, 162, 163, 164, 165, 166, 167, 168, 169, 170, 178, 179, 180, 181, 182, 183, 184, 185, 186, 194, 195, 196, 197, 198, 199, 200, 201, 202, 210, 211, 212, 213, 214, 215, 216, 217, 218, 225, 226, 227, 228, 229, 230, 231, 232, 233, 234, 241, 242, 243, 244, 245, 246, 247, 248, 249, 250]}
ac1 = {1: [], 2: [0, 1], 3: [2], 4: [3, 17], 5: [4, 5, 33, 49], 6: [6, 18, 65, 81], 7: [7, 97, 113], 8: [19, 34, 50, 129], 9: [8, 20, 66, 145, 161, 177, 193], 10: [9, 35, 51, 82, 240], 11: [21, 98, 114, 209], 12: [10, 22, 36, 52], 13: [], 14: [225], 15: [37, 241], 16: [23, 24, 25, 26, 38, 39, 40, 41, 42, 53, 54, 55, 56, 57, 58, 67, 68, 69, 70, 71, 72, 73, 74, 83, 84, 85, 86, 87, 88, 89, 90, 99, 100, 101, 102, 103, 104, 105, 106, 115, 116, 117, 118, 119, 120, 121, 122, 130, 131, 132, 133, 134, 135, 136, 137, 138, 146, 147, 148, 149, 150, 151, 152, 153, 154, 162, 163, 164, 165, 166, 167, 168, 169, 170, 178, 179, 180, 181, 182, 183, 184, 185, 186, 194, 195, 196, 197, 198, 199, 200, 201, 202, 210, 211, 212, 213, 214, 215, 216, 217, 218, 226, 227, 228, 229, 230, 231, 232, 233, 234, 242, 243, 244, 245, 246, 247, 248, 249, 250]}
dc0 = {1: [], 2: [0], 3: [1, 2, 3, 4, 5], 4: [6], 5: [7], 6: [8], 7: [9], 8: [10], 9: [11], 10: [], 11: [], 12: [], 13: [], 14: [], 15: [], 16: []}
dc1 = {1: [], 2: [0, 1, 2], 3: [3], 4: [4], 5: [5], 6: [6], 7: [7], 8: [8], 9: [9], 10: [10], 11: [11], 12: [], 13: [], 14: [], 15: [], 16: []}

class JPEG():
    component_name = {1:'Y', 2:'Cb', 3:'Cr', 4:'I', 5:'Q'}
    def __init__(self, filename):
        with open(filename, "rb") as binary_file:
            self.data = bytearray(binary_file.read())
        self.index = 0
        self.q_tab = [None, None, None, None]
        self.huff_tab = {}
        self.huff_tab['dc'] = [dc0, dc1, None, None]
        self.huff_tab['ac'] = [ac0, ac1, None, None]
        self.components = {}
        self.decode_markers()
        self.reservoir_bits = 0
        self.reservoir_length = 0

    def read_u16(self):
        rv = (self.data[self.index] << 8) | self.data[self.index+1]
        self.index += 2
        return rv

    def read_segment(self):
        if self.data[self.index] != 0xff:
            raise Exception("marker no found")
        marker = self.read_u16()
        if marker in range(0xffd0,0xffda) :
            size = 0
        else:
            size = self.read_u16() -2
        data = self.data[self.index:self.index + size ]
        self.index += size
        return (Marker(marker), data)

    def parse_app0(self,data):
        self.jfif = {}
        self.jfif['identifier']  = data[0:4].decode()
        self.jfif['revision'] = '%d.%d' % (data[5], data[6])
        self.jfif['units'] = data[7]
        self.jfif['X-density'] = (data[8] << 8) | data[9]
        self.jfif['Y-density'] = (data[10] << 8) | data[11]
        self.jfif['ThumbnailWidth'] = data[12]
        self.jfif['ThumbnailHeight'] = data[13]
        print(self.jfif)

    def parse_sof0(self,data):
        self.frame = {}
        self.frame['precision'] = data[0]
        self.frame['height'] = (data[1] << 8) | data[2]
        self.frame['width'] = (data[3] << 8) | data[4]
        self.frame['components_count'] = data[5]
        print("frame", self.frame)
        for i in range(self.frame['components_count']):
            id = data[3*i+6]
            tmp = {'name':self.component_name[id], 'hfactor':(data[3*i+7] >> 4) & 0x04, 'vfactor':data[3*i+7] & 0x04, 'q_tab':data[3*i+8], 'dc_predict':0}
            self.components[id] = tmp
            print("component %s: %s" % (id, tmp))

    def parse_dqt(self, data):
        precision = (data[0] >> 4) & 0x0f
        table_id = data[0] & 0x0f
        # this is an ugly short cut. doesn't support precision == 1 (16 but values)
        self.q_tab[table_id] = list(data[1:65])

    def parse_dht(self, data):
        while len(data) > 0:
            rv = {}
            if data[0]>>4 == 0:
                table_class = 'dc'
            else:
                table_class = 'ac'
            table_id = data[0] & 0x0f
            lengths = list(data[1:17])
            HUFFVAL = {}
            p = 17;
            for i in range(16):
                l = lengths[i]
                HUFFVAL[i+1] = list(data[p:p+l])
                p += l
            self.huff_tab[table_class][table_id] = HUFFVAL
            data = data[p:]

    def parse_sos(self, data):
        rv = {}
        components_count = data[0]
        for i in range(components_count):
            id = data[2*i+1]
            self.components[id]['dc_tab'] = (data[2*i+2] >> 4) & 0x0f
            self.components[id]['ac_tab'] = data[2*i+2] & 0x0f

    def check_enougth_bits(self, n):
        while (self.reservoir_length < n):
            self.reservoir_bits <<= 8
            self.reservoir_bits |= self.data[self.index]
            # print "%02x " % self.assets[self.index],
            self.reservoir_length += 8
            if self.data[self.index] == 0xff and self.data[self.index+1] == 0x00: # de-stuff
                self.index += 1
            self.index += 1

    def peek_bits(self, n):
        self.check_enougth_bits(n)
        mask = (1 << n) - 1
        rv = (self.reservoir_bits >> (self.reservoir_length - n)) & mask
        return rv

    def read_bits(self, n):
        rv = self.peek_bits(n)
        self.reservoir_length -= n
        return rv

    # code is an array with one element, since we need to return the code to the caller
    def read_vlc(self, vlc_tab):
        buff = self.peek_bits(16)
        code = 0
        for code_len in range(1,17):
            for value in vlc_tab[code_len]:
                # print "{0:b} vs {1:b} value {2:x} len {3}".format(buff >> (16-code_len) , code , value, code_len)
                if buff >> (16-code_len) == code :
                    self.read_bits(code_len)
                    extra_bits_needed = value & 0x0f
                    additional_bits = 0
                    if extra_bits_needed > 0 :
                        additional_bits = self.read_bits(extra_bits_needed)
                        if (additional_bits < (1 << (extra_bits_needed - 1))): # negative values
                            additional_bits += ((-1) << extra_bits_needed) + 1
                    return (value , additional_bits)
                code += 1
            code <<= 1

    def decode_block(self, component):
        block = [0] * 64
        index = 0
        # dc value
        diff, value = self.read_vlc(self.huff_tab['dc'][component['dc_tab']])
        if diff != 0:
            component['dc_predict'] += value
        block[0] = component['dc_predict'] # * self.q_tab[component['q_tab']][0]
        # ac zig-zag
        while True:
            temp, value = self.read_vlc(self.huff_tab['ac'][component['ac_tab']])
            rle = temp >> 4
            bits = temp & 0x04
            if rle == 0 and bits == 0:
                break  # EOB
            if (bits == 00 and (rle != 0x0F)):
                raise Exception()
            index += rle + 1
            if index > 63:
                raise Exception()
            block[self.zigzag[index]] = value * self.q_tab[component['q_tab']][index]
            if index >= 63:
                break
        return block


    def decode_scan(self):
        blocks = []
        y_blocks_count = self.frame['height'] / (8*(self.components[1]['vfactor'] + 1))
        x_blocks_count = self.frame['width'] / (8*(self.components[1]['hfactor'] + 1))
        while True:
            for block_y in range(y_blocks_count):
                for block_x in range(x_blocks_count):
                    block = ()
                    for i in self.components:
                        block += (self.decode_block(self.components[i]), )
                    blocks += [block]
            # flush reservoir bits
            self.index -= (self.reservoir_length / 8)
            self.reservoir_length = 0
            self.reservoir_bits = 0
            # check for End of Image marker
            if self.data[self.index] == 0xff:
                marker = self.read_u16()
                if Marker(marker) == Marker.EOI:
                    break

    def decode_markers(self):
        while (True):
            marker, data = self.read_segment()
            # print "marker %04x %s size %s" % (marker.value, marker, len(assets))
            # print assets
            if marker == Marker.APP0:
                self.parse_app0(data)
            elif marker == Marker.SOF0:
                self.parse_sof0(data)
            elif marker == Marker.DQT:
                self.parse_dqt(data)
            elif marker == Marker.DHT:
                self.parse_dht(data)
            elif marker == Marker.SOS:  # eoi
                self.parse_sos(data)
                break

    def decode(self):
        self.decode_scan()

jpeg = JPEG('/assets/huff_simple0.jpg')
jpeg.decode()