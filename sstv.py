import math
from binascii import unhexlify
from PIL import Image

RATE    = 11025
MAXRATE = 22050
BITS    = 16
CHANS   = 1
VOLPCT  = 20
MAXSAMPLES = (180 * MAXRATE)

SSTVImageSize = (320, 256)

class SSTV():
    def __init__(self):
        pass

    def process(self, image):

        self.image = image.convert('RGB')
        self.image = self.image.resize(SSTVImageSize, Image.ANTIALIAS)


        temp1 = (float)(1 << (BITS - 1))
        temp2 = VOLPCT / 100.0
        temp3 = temp1 * temp2
        self.g_scale = int(temp3)

        self.g_rate = RATE
        self.g_twopioverrate = 2.0 * math.pi / self.g_rate
        self.g_uspersample = 1000000.0 / float(self.g_rate)

        self.g_theta = 0.0
        self.g_samples = 0
        self.g_fudge = 0.0

        self.g_audio = [0] * MAXSAMPLES


        print "Constants check:"
        print "      rate = %d" % self.g_rate
        print "      BITS = %d" % BITS
        print "    VOLPCT = %d" % VOLPCT
        print "     scale = %d" % self.g_scale
        print "   us/samp = %f" % self.g_uspersample
        print "   2p/rate = %f" % self.g_twopioverrate
        print

        self.addvisheader()
        self.buildaudio()
        self.addvistrailer()

    # playtone - - Add waveform info to audio data.New waveform data is
    # added in a phase - continuous manner according to the
    # audio frequency and duration provided.Note that the
    # audio is still in a purely hypothetical state - the
    # format of the output file is not determined until
    # the file is written, at the end of the process.
    # Also, yes, a nod to Tom Hanks.

    def playtone(self,  tonefreq,  tonedur ):
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

        self.g_fudge = tonedur - ( tonesamples * self.g_uspersample )

    # addvisheader - - Add the specific audio tones that make up the
    # Martin 1 VIS header to the audio data.Basically,
    # this just means lots of calls to playtone().

    def addvisheader(self):
        print("Adding VIS header to audio data.")

        # bit of silence
        self.playtone(0, 500000)

        # attention tones
        self.playtone(1900, 100000)
        self.playtone(1500, 100000)
        self.playtone(1900, 100000)
        self.playtone(1500, 100000)
        self.playtone(2300, 100000)
        self.playtone(1500, 100000)
        self.playtone(2300, 100000)
        self.playtone(1500, 100000)

        # VIS lead, break, mid, start
        self.playtone(1900, 300000)
        self.playtone(1200, 10000)
        # self.playtone(1500, 300000)
        self.playtone(1900, 300000)
        self.playtone(1200, 30000)

        # VIS data bits(Martin 1)
        self.playtone(1300, 30000)
        self.playtone(1300, 30000)
        self.playtone(1100, 30000)
        self.playtone(1100, 30000)
        self.playtone(1300, 30000)
        self.playtone(1100, 30000)
        self.playtone(1300, 30000)
        self.playtone(1100, 30000)

        # VIS stop
        self.playtone(1200, 30000)

    # addvistrailer - - Add tones for VIS trailer to audio stream.
    # More calls to playtone().

    def addvistrailer(self):

        print("Adding VIS trailer to audio data.")

        self.playtone(2300, 300000)
        self.playtone(1200, 10000)
        self.playtone(2300, 100000)
        self.playtone(1200, 30000)

        # bit of silence
        self.playtone(0, 500000)

        print("Done adding VIS trailer to audio data.")

    # toneval -- Map an 8-bit value to a corresponding number between
    #            1500 and 2300, on a simple linear scale. This is used
    #            to map an 8-bit color intensity (I know, wrong word)
    #            to an audio frequency. This is the lifeblood of SSTV.

    def toneval ( self,  colorval ):
        return ( ( 800 * colorval ) / 256 ) + 1500

    # buildaudio -- Primary code for converting image data to audio.
    #               Reads color data for individual pixels from a libGD
    #               object, calls toneval() to convert the color data
    #               to an audio frequency, then calls playtone() to add
    #               that to the audio data. This routine assumes an image
    #               320 wide x 256 tall x 24 bit colorspace (8 bits each
    #               for R, G, and B).
    #
    #               In Martin 1, the image data is sent one row at a time,
    #               once for green, once for blue, and once for red. There
    #               is a separator tone between each channel's audio, and
    #               a sync tone at the beginning of each new row. This
    #               routine handles the sep/sync details as well.

    def buildaudio (self):
        r = [0] * 320
        g = [0] * 320
        b = [0] * 320

        print( "Adding image to audio data." )
        pixels, lines = SSTVImageSize
        for y in range(lines):

            # printf( "Row [%d] Sample [%d].\n" , y , g_samples ) ;

            # read image data
            for x in range(pixels):
                r[x], g[x], b[x] = self.image.getpixel((x, y))

            # add row markers to audio
            self.playtone( 1200 , 4862 )             # sync
            self.playtone( 1500 ,  572 )             # porch

            # each pixel is 457.6us long in Martin 1

            # add audio for green channel for this row
            for v in g:
                self.playtone( self.toneval( v ) , 457.6 )

            self.playtone( 1500 , 572 )            # separator tone

            # blue channel
            for v in b:
                self.playtone( self.toneval( v ) , 457.6 )

            self.playtone( 1500 , 572 )             # separator tone

            # red channel
            for v in r:
                self.playtone( self.toneval( v ), 457.6 )

            self.playtone( 1500 , 572 )


        print( "Done adding image to audio data." )

    def writefile_wav (self, filename):

        audiosize  = self.g_samples * CHANS * (BITS / 8)  # bytes of audio
        totalsize  = 4 + (8 + 16) + (8 + audiosize)       # audio + some headers
        byterate   = self.g_rate * CHANS * BITS / 8       # audio bytes / sec
        blockalign = CHANS * BITS / 8                     # total bytes / sample
        
        print( "Writing audio data to file." )
        print( "Got a total of [%d] samples." % self.g_samples )

        # RIFF header
        rv = []
        rv += ['R', 'I', 'F', 'F']
        # total size, audio plus some headers (LE!!)
        rv += list(unhexlify("%08x" % (totalsize)))[::-1]  # len
        rv += ['W', 'A', 'V', 'E']
        # sub chunk 1 (format spec)
        rv += ['f', 'm', 't', ' ']
        rv += list(unhexlify("%08x" % 0x10))[::-1]  # size of chunk (LE!!)
        rv += list(unhexlify("%04x" % 1))[::-1]     # format = 1 (PCM) (LE)
        rv += list(unhexlify("%04x" % 1))[::-1]     # channels = 1 (LE)


        rv += list(unhexlify("%08x" % self.g_rate))[::-1]  # samples / channel / sec (LE!!)
        rv += list(unhexlify("%08x" % byterate))[::-1]     # bytes total / sec (LE!!)
        rv += list(unhexlify("%04x" % blockalign))[::-1]   # block alignment (LE!!)
        rv += list(unhexlify("%04x" % BITS))[::-1]         # bits/sample (LE)

        # sub chunk 2

        rv += ['d', 'a', 't', 'a']                       # header
        rv += list(unhexlify("%08x" % audiosize))[::-1]  # audio bytes total (LE!!)

        # FINALLY, the audio data itself (LE!!)
        for  i in range(self.g_samples):
            v = self.g_audio[i]
            rv += [(v & 0xff), ((v >> 8) & 0xff)]

        with open(filename, "wb") as fout:
            fout.write(bytearray(rv))

        # no trailer
        print( "Done writing to audio file." )

if __name__ == "__main__":
    im = Image.open('images/TestCard.jpg')
    sstv = SSTV()
    sstv.process(im)
    sstv.writefile_wav('data/sstv.wav')
