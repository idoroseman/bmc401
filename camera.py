import os
import time
from io import BytesIO
from picamera import PiCamera
from PIL import Image

class Camera():
    def __init__(self, path="./images"):
		# Create the in-memory stream
		self.stream = BytesIO()
		self.camera = PiCamera()
		self.basepath = path

    def capture(self):
		self.camera.capture(self.stream, format='jpeg')
		# "Rewind" the stream to the beginning so we can read its content
		self.stream.seek(0)
		self.image = Image.open(self.stream)

	def resize(self, newSize):
		self.image = self.image.resize(newSize, Image.ANTIALIAS)

	def saveToFile(self, filename):
		self.image.save(os.path.join(self.basepath,filename + ".jpg"), "JPEG")

if __name__ == "__main__":
    cam = Camera()
    cam.capture()

    cam.saveToFile("picture")
