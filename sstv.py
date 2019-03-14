from PIL import Image
import time
from wavefile import WaveFile

class SSTV():
    def __init__(self):
        pass

    def process(self, image):

        self.image = image.convert('RGB')
        self.image = self.image.resize(SSTVImageSize, Image.ANTIALIAS)
        self.wav = WaveFile()
        self.wav.info()
        self.playtone = self.wav.playtone

        self.addvisheader()
        self.buildaudio()
        self.addvistrailer()


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

    def toneval(self, colorval):
        return ((800 * colorval) / 256) + 1500

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

    def buildaudio(self):
        r = [0] * 320
        g = [0] * 320
        b = [0] * 320

        print("Adding image to audio data.")
        pixels, lines = SSTVImageSize
        for y in range(lines):

            # printf( "Row [%d] Sample [%d].\n" , y , g_samples ) ;

            # read image data
            for x in range(pixels):
                r[x], g[x], b[x] = self.image.getpixel((x, y))

            # add row markers to audio
            self.playtone(1200, 4862)  # sync
            self.playtone(1500, 572)  # porch

            # each pixel is 457.6us long in Martin 1

            # add audio for green channel for this row
            for v in g:
                self.playtone(self.toneval(v), 457.6)

            self.playtone(1500, 572)  # separator tone

            # blue channel
            for v in b:
                self.playtone(self.toneval(v), 457.6)

            self.playtone(1500, 572)  # separator tone

            # red channel
            for v in r:
                self.playtone(self.toneval(v), 457.6)

            self.playtone(1500, 572)

        print("Done adding image to audio data.")




if __name__ == "__main__":
    im = Image.open('images/TestCard.jpg')
    sstv = SSTV()
    start_time = time.time()
    sstv.process(im)
    end_time = time.time()
    sstv.wav.writefile_wav('data/sstv.wav')
    print "%s seconds" % (end_time-start_time)