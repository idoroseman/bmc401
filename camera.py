import os
import time
from io import BytesIO
from picamera import PiCamera
from PIL import Image, ImageFont, ImageDraw
import datetime


class Camera():
    def __init__(self, path="./images"):
        # Create the in-memory stream
        self.stream = BytesIO()
        self.camera = PiCamera()
        self.camera.awb_mode = 'sunlight'
        time.sleep(2)
        self.basepath = path
        self.logo = Image.open("logo.png").convert("RGBA")
        self.mask = self.logo.copy()
        self.logo.putalpha(150)

    def capture(self):
        self.camera.capture(self.stream, format='jpeg')
        # "Rewind" the stream to the beginning so we can read its content
        self.stream.seek(0)
        self.image = Image.open(self.stream).convert("RGBA")

    def archive(self):
        self.saveToFile(datetime.datetime.datetime.now().strftime("%Y-%m-%d %H%M"))

    def resize(self, newSize):
        self.image = self.image.resize(newSize, Image.ANTIALIAS)

    def overlay(self, callsign, gps, sensors):
        yellow = (255, 255, 0, 127)
        layer = Image.new('RGBA', self.image.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(layer)
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 15)
        bigfont = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 40)
        # callsign
        draw.text((2, 2), callsign.upper(), font=bigfont, fill=(0, 0, 0, 192))
        draw.text((0, 0), callsign.upper(), font=bigfont, fill=(255, 0, 0, 192))
        # url & date time
        draw.text((170, 5), "idoroseman.com", font=font, fill=yellow)
        draw.text((170, 25), "%s" % datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), yellow, font)
        # telemetry
        draw.rectangle(((5, 155), (150, 240)), (255, 255, 255, 64))
        draw.text((10, 160), "Lat %2.4f" % gps['lat'], yellow, font)
        draw.text((10, 180), "Lon %2.4f" % gps['lon'], yellow, font)
        draw.text((10, 200), "Alt %s" % gps['alt'], yellow, font)
        draw.text((10, 220), "%4.1fhPa" % 1234, yellow, font)
        draw.text((100, 220), u"%+2.0f\N{DEGREE SIGN}C" % sensors['outside_temp'], yellow, font)
        # logo
        self.image.paste(self.logo, (220, 130), self.mask)
        del draw
        self.image = Image.alpha_composite(self.image, layer)

    def saveToFile(self, filename):
        self.image.save(os.path.join(self.basepath, filename + ".jpg"), "JPEG")

    def loadFromFile(self, filename):
        self.image = Image.open(filename)


if __name__ == "__main__":
    cam = Camera()
    cam.capture()
    cam.resize((320, 256))
    #    cam.loadFromFile("images/ssdv.jpg")
    cam.saveToFile("picture")
    gpsdata = {'lat': 32.063331,
               'lon': 34.87216566666667,
               'alt': 129.7
               }
    cam.overlay('4x6ub', gpsdata)
    cam.saveToFile("overlay")
