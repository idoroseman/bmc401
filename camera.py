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
        self.basepath = path
        self.logo = Image.open("logo.png")


    def capture(self):
        self.camera.capture(self.stream, format='jpeg')
        # "Rewind" the stream to the beginning so we can read its content
        self.stream.seek(0)
        self.image = Image.open(self.stream)


    def resize(self, newSize):
        self.image = self.image.resize(newSize, Image.ANTIALIAS)


    def overlay(self, callsign, gps):
        yellow = (255, 255, 0, 127)
        draw = ImageDraw.Draw(self.image)
        font = ImageFont.truetype("/Library/fonts/arial.ttf", 15)
        bigfont = ImageFont.truetype("/Library/fonts/arial.ttf", 40)
        draw.text((2, 2), callsign.upper(), font = bigfont, fill=(0, 0, 0, 255))
        draw.text((0, 0), callsign.upper(), font = bigfont, fill=(255, 0, 0, 255))
        draw.text((190, 5), "idoroseman.com", font=font, fill=yellow)
        draw.text((10, 160), "Lat %s" % gps['lat'], yellow, font)
        draw.text((10, 180), "Lon %s" % gps['lon'], yellow, font)
        draw.text((10, 200), "Alt %s" % gps['alt'], yellow, font)
        draw.text((10, 220), "%s" % datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), yellow, font)
        self.image.paste(self.logo, (220, 130))

    def saveToFile(self, filename):
        self.image.save(os.path.join(self.basepath, filename + ".jpg"), "JPEG")

    def loadFromFile(self, filename):
        self.image = Image.open(filename)

if __name__ == "__main__":
    cam = Camera()
    # cam.capture()
    # cam.saveToFile("picture")
    gpsdata = {'lat': 32.063331,
               'lon': 34.87216566666667,
               'alt': 129.7
               }
    cam.loadFromFile("images/ssdv.jpg")
    cam.overlay('4x6ub', gpsdata)
    cam.saveToFile("overlay")