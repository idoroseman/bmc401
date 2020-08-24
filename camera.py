import os
import time
from io import BytesIO
from picamera import PiCamera
from PIL import Image, ImageFont, ImageDraw
import datetime
import logging

USE_WEBCAM = True

class Camera():
    def __init__(self, path="./images"):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        if not os.path.exists(path):
            os.mkdir(path)
        if not os.path.exists('./tmp'):
            os.mkdir('./tmp')
        self.isFisheye = True
        self.border = 10 # percent
        # Create the in-memory stream
        self.stream = BytesIO()
        self.camera = PiCamera()
        #self.camera.rotation = 180
        self.camera.awb_mode = 'auto' # 'sunlight'
        time.sleep(2)
        self.basepath = path
        self.logo = Image.open("data/logo.png").convert("RGBA")
        self.mask = self.logo.copy()
        self.logo.putalpha(150)
        #opacity_level = 127
        #datas = self.logo.getdata()
        #newData = []
        #for item in datas:
        #    newData.append((0, 0, 0, opacity_level))
        #else:
        #    newData.append(item)
        #self.logo.putdata(newData)

    def capture(self):
        try:
            self.stream.seek(0)
            self.camera.capture(self.stream, format='jpeg')
            # "Rewind" the stream to the beginning so we can read its content
            self.stream.seek(0)
            self.image1 = Image.open(self.stream).convert("RGBA")
            if self.isFisheye:
                self.image1 = self.zoom(self.image1, self.border)
        except Exception as x:
            self.logger.exception(x)
            self.image1 = Image.new("RGBA", (320,256))
            red = (255, 0, 0, 255)
            draw = ImageDraw.Draw(self.image1)
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 15)
            draw.text((10,100), "ERROR", red, font);
            draw.text((10,120), x, red, font);

        try:
            if not USE_WEBCAM:
                raise Exception("no webcam")
            os.system("fswebcam -r 1024X768 -d /dev/video1 -p YUYV -S 120 --no-banner tmp/usbcam.jpg")
            self.image2 = Image.open("tmp/usbcam.jpg").convert("RGBA")
        except:
            self.image2 = Image.new("RGBA", (320,256))

    def archive(self):
        filename = datetime.datetime.now().strftime("%Y-%m-%d-%H%M")
        self.image1.convert('RGB').save(os.path.join(self.basepath, filename + "-cam1.jpg"), "JPEG")
        self.image2.convert('RGB').save(os.path.join(self.basepath, filename + "-cam2.jpg"), "JPEG")

    def select(self, id):
        self.logger.info("using camera %s "%id)
        self.cam_id = id
        if id == 0:
          self.image = self.image1
        else:
          self.image = self.image2

    def zoom(self, image, border):
        width, height = image.size   # Get dimensions
        left = (width * border)/100
        top = (height * border)/100
        right = (width * (100-border))/100
        bottom = (height * (100-border))/100
        # print(left, top, right, bottom)
        return image.crop((left, top, right, bottom))

    def resize(self, newSize):
        w, h = self.image.size
        w1, h1 = newSize
    # h1 &= 0xfff0 # image size should be multiple of 16
        w2 = int(w*h1/h)
        left = (w2 - w1)/2
        right = (w2 + w1)/2
        self.image = self.image.resize((w2, h1), Image.ANTIALIAS)
        self.image = self.image.crop((left, 0, right, h1))

    def overlay(self, callsign, gps, sensors):
        yellow = (255, 255, 0, 255)
        brown = (165,42,42)
        green = (0, 255, 0)
        layer = Image.new('RGBA', self.image.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(layer)
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 15)
        # url & date time
        draw.text((170+1, 5+1), "idoroseman.com", font=font, fill=brown)
        draw.text((170, 5), "idoroseman.com", font=font, fill=yellow)
        draw.text((170+1, 20+1), "%s" % datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), brown, font)
        draw.text((170, 20), "%s" % datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), yellow, font)
        # telemetry
        draw.rectangle(((5, 185), (155, 240)), (255, 255, 255, 90))
        if gps['status'] == "fix":
            draw.text((10, 190), "%2.4f  %2.4f" % (gps['lat'], gps['lon']), yellow, font)
        else:
            draw.text((10, 190), "GPS %s" % gps['status'], yellow, font)
        draw.text((10, 205), "%dm" % float(gps['alt']), yellow, font)
        draw.text((80, 205), ("%4.1fmb" % sensors['barometer']).rjust(8), yellow, font)
        draw.text((10, 220), "%+2.0f\N{DEGREE SIGN}C" % sensors['outside_temp'], yellow, font)
        draw.text((60, 220), "%+2.0f\N{DEGREE SIGN}C" % sensors['inside_temp'], yellow, font)
        draw.text((114, 220), "%1.1fV" % sensors['battery'], yellow, font)
        # logo
        self.image.paste(self.logo, (220, 130), self.mask)
        if self.cam_id == 0:
            draw.text((304, 5), "V", green, font)
        elif self.cam_id == 1:
            draw.text((304, 5), ">", green, font)

        del draw
        self.image = Image.alpha_composite(self.image, layer)

    def saveToFile(self, filename):
        self.image.convert('RGB').save(filename, "JPEG")

    def loadFromFile(self, filename):
        self.image = Image.open(filename)


if __name__ == "__main__":
    cam = Camera()
#    cam.capture()
#    cam.select(0)
#    cam.resize((320, 256))
    cam.loadFromFile("images/ssdv.jpg")
    cam.saveToFile("tmp/picture.jpg")
    gpsdata = {'lat': 32.063331,
               'lon': 34.87216566666667,
               'alt': 1290.7,
               'status': "test"
               }
    sensordata = {'barometer':999,
                  'outside_temp':-20,
                  'inside_temp':17
               }
    cam.overlay('4x6ub', gpsdata, sensordata)
    cam.saveToFile("tmp/overlay.jpg")
