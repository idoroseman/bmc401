from wavefile import WaveFile
import time

class AFSK():

    def __init__(self, sample_rate = 11025, baud = 1200, lfreq = 1200, hfreq = 2200):
        self.sample_rate = sample_rate
        self.baud = baud
        self.freqs = [lfreq, hfreq]
        self.bit_durration = 1000000 / self.baud

    def saveToFile(self, filename):
        self.wav.saveToFile(filename)


    def encode(self, Messages):
        self.wav = WaveFile(self.sample_rate)
        self.bit_count = 0
        self.isHigh = False
        self.bits = []
        preamble_length = 128
        postamble_length = 64
        flags_before = 32
        flags_after = 32
        start_time = time.time()

        if isinstance(Messages, list):
            message_count = len(Messages)
        else:
            message_count = 1
            Messages = [Messages]

        total_message_length = sum([len(x.toString()) for x in Messages])

        for j in range(message_count):
            msg = Messages[j].toString()
            message_length = len(msg)

            # Write preamble
            for i in range(preamble_length):
                self.bits += [0]

            for i in range(flags_before):
                self.write_byte(0x7E, 0)

            # Create and write actual data
            for i in range(message_length):
                self.write_byte(msg[i], 1)

            for i in range(flags_after):
                self.write_byte(0x7E, 0)

            # Write postamble
            for i in range(postamble_length):
                self.bits += [0]

        for bit in self.bits:
            self.wav.playtone(self.freqs[bit], self.bit_durration)

        end_time = time.time()
        print "encoding %s messages took %s seconds" % (message_count, end_time-start_time)

    def write_bit(self, Bit, BitStuffing):
        if (BitStuffing):
            if (self.bit_count >= 5):
                self.isHigh = not self.isHigh
                self.bits += [self.isHigh]
                self.bit_count = 0
        else:
            self.bit_count = 0

        if Bit:
            # Stay with same frequency, but only for a max of 5 in a row
            self.bit_count += 1
        else:
            # 0 means swap frequency
            self.isHigh = not self.isHigh
            self.bit_count = 0
        self.bits += [self.isHigh]

    def write_byte(self, Character, BitStuffing):
        if isinstance(Character, str):
            Character = ord(Character)
        for i in range(8):
            self.write_bit(Character & 1, BitStuffing)
            Character >>= 1

