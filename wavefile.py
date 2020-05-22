from binascii import unhexlify
import math

RATE = 11025
MAXRATE = 22050
BITS = 16
CHANS = 1
VOLPCT = 20
MAXSAMPLES = (300 * MAXRATE)

class WaveFile():
    def __init__(self, rate=11025, bits=16):
        self.g_rate = rate
        self.g_twopioverrate = 2.0 * math.pi / self.g_rate
        self.g_uspersample = 1000000.0 / float(self.g_rate)
        self.g_theta = 0.0
        self.g_samples = 0
        self.g_fudge = 0.0
        self.bits = bits
        temp1 = (float)(1 << (bits - 1))
        temp2 = VOLPCT / 100.0
        temp3 = temp1 * temp2
        self.g_scale = int(temp3)
        self.g_audio = [0] * MAXSAMPLES

    def info(self):
        print("Constants check:")
        print("      rate = %d" % self.g_rate)
        print("      BITS = %d" % BITS)
        print("    VOLPCT = %d" % VOLPCT)
        print("     scale = %d" % self.g_scale)
        print("   us/samp = %f" % self.g_uspersample)
        print("   2p/rate = %f" % self.g_twopioverrate)
        print()

    # playtone - - Add waveform info to audio data.New waveform data is
    # added in a phase - continuous manner according to the
    # audio frequency and duration provided.Note that the
    # audio is still in a purely hypothetical state - the
    # format of the output file is not determined until
    # the file is written, at the end of the process.
    # Also, yes, a nod to Tom Hanks.

    def playtone(self, tonefreq, tonedur):
        tonedur += self.g_fudge
        tonesamples = int((tonedur / self.g_uspersample) + 0.5)
        deltatheta = self.g_twopioverrate * tonefreq

        for i in range(tonesamples):
            self.g_samples += 1
            if (tonefreq == 0):
                self.g_audio[self.g_samples] = 32768
            else:
                voltage = 0 + (int)(math.sin(self.g_theta) * self.g_scale)
                self.g_audio[self.g_samples] = voltage
                self.g_theta += deltatheta

        self.g_fudge = tonedur - (tonesamples * self.g_uspersample)

    def saveToFile(self, filename):

        audiosize = self.g_samples * CHANS * (BITS / 8)  # bytes of audio
        totalsize = 4 + (8 + 16) + (8 + audiosize)  # audio + some headers
        byterate = self.g_rate * CHANS * BITS / 8  # audio bytes / sec
        blockalign = CHANS * BITS / 8  # total bytes / sample

        print("Writing audio data to file %s"%filename)
        print(("Got a total of [%d] samples." % self.g_samples))

        # RIFF header
        rv = []
        rv += ['R', 'I', 'F', 'F']
        # total size, audio plus some headers (LE!!)
        rv += list(unhexlify("%08x" % int(totalsize)))[::-1]  # len
        rv += ['W', 'A', 'V', 'E']
        # sub chunk 1 (format spec)
        rv += ['f', 'm', 't', ' ']
        rv += list(unhexlify("%08x" % 0x10))[::-1]  # size of chunk (LE!!)
        rv += list(unhexlify("%04x" % 1))[::-1]  # format = 1 (PCM) (LE)
        rv += list(unhexlify("%04x" % 1))[::-1]  # channels = 1 (LE)

        rv += list(unhexlify("%08x" % self.g_rate))[::-1]  # samples / channel / sec (LE!!)
        rv += list(unhexlify("%08x" % int(byterate)))[::-1]  # bytes total / sec (LE!!)
        rv += list(unhexlify("%04x" % int(blockalign)))[::-1]  # block alignment (LE!!)
        rv += list(unhexlify("%04x" % BITS))[::-1]  # bits/sample (LE)

        # sub chunk 2

        rv += ['d', 'a', 't', 'a']  # header
        rv += list(unhexlify("%08x" % int(audiosize)))[::-1]  # audio bytes total (LE!!)

        # FINALLY, the audio data itself (LE!!)
        for i in range(self.g_samples):
            v = self.g_audio[i]
            rv += [(v & 0xff), ((v >> 8) & 0xff)]

        rv = [x if type(x)==int else ord(x) for x in rv]
        with open(filename, "wb") as fout:
            fout.write(bytes(rv))

        # no trailer
        print("Done writing to audio file.")
