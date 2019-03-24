import os
import json
import time
import thread
import RPi.GPIO as GPIO

from aprs import APRS
from modem import AFSK
from ublox import Ublox
from dorji import Dorji
from timers import Timers
from sensors import Sensors
from camera import Camera
from ssdv import SSDV
from sstv import SSTV
from webserver import WebServer


class BalloonMissionComputer():

    def calc_status_bits(self, gpsdata, sensordata):
        bits = [gpsdata['status'] == "i2c error",
                gpsdata['status'] == "comm error",
                gpsdata['status'] == 'fix',
                False,
                False,
                False,
                False,
                False]
        return ''.join(['1' if val else '0' for val in bits])

    self.status_names = ['gps i2c err', "gps comm err", "gps fix"]

    def calc_balloon_state(self, gpsdata):
        if 'alt' not in calc_balloon_state.__dict__:
            calc_balloon_state.alt = 0
        if 'maxalt' not in calc_balloon_state.__dict__:
            calc_balloon_state.maxalt = 0
        if 'state' not in calc_balloon_state.__dict__:
            calc_balloon_state.state = "ground"
        if calc_balloon_state.state == "ground" and gpsdata['alt'] > 2000:
            calc_balloon_state.state = "ascent"
        if calc_balloon_state.state == "ground" and gpsdata['alt'] < calc_balloon_state.maxalt - 2000:
            calc_balloon_state.state = "descent"
        if calc_balloon_state.state == "descent" and gpsdata['alt'] < 2000:
            calc_balloon_state.state = "landed"
        if gpsdata['alt'] > calc_balloon_state.maxalt:
            calc_balloon_state.maxalt = gpsdata['alt']
        calc_balloon_state.alt = gpsdata['alt']

    def capture_image(self, gpsdata, sensordata, archive=True):
        self.cam.capture()
        if archive:
          self.cam.archive()
        self.cam.resize((320, 256))
        self.cam.overlay(self.config['callsign'], gpsdata, sensordata)
        self.cam.saveToFile(os.path.join(self.tmp_dir, 'cam1.jpg'))

    def process_ssdv(self):
        self.ssdv.convert('tmp/cam1.jpg', 'tmp/image.ssdv')
        packets, raw = self.ssdv.prepare(os.path.join(self.tmp_dir, "image.ssdv"))
        self.modem.encode(packets)
        self.modem.saveToFile(os.path.join(self.tmp_dir, 'ssdv.wav'))
        self.timers.handle(None, ["SSDV-PLAY"])

    def process_sstv(self):
        self.sstv.image = self.cam.image
        self.sstv.process()
        self.sstv.saveToFile(os.path.join(self.tmp_dir, 'sstv.wav'))
        self.timers.handle(None, ["SSTV-PLAY"])

    def setup(self):
        # setup
        with open('data/config.json') as fin:
            self.config = json.load(fin)
        self.images_dir = config["directories"]["images"] if "directories" in config and "images" in config[
            "directories"] else "./images"
        self.tmp_dir = config["directories"]["tmp"] if "directories" in config and "tmp" in config[
            "directories"] else "./tmp"

        if not os.path.exists(self.tmp_dir):
            os.makedirs(self.tmp_dir)

        GPIO.setmode(GPIO.BCM)  # Broadcom pin-numbering scheme
        GPIO.setup(self.config['pins']['BUZZER'], GPIO.OUT)
        GPIO.setup(self.config['pins']['LED1'], GPIO.OUT)
        GPIO.setup(self.config['pins']['LED2'], GPIO.OUT)

        self.aprs = APRS(config['callsign'], config['ssid'], "idoroseman.com")
        self.modem = AFSK()
        self.gps = Ublox()
        self.gps.start()
        self.radio = Dorji(config['pins'])
        self.radio.init()
        self.timers = Timers(config['timers'])
        self.sensors = Sensors()
        self.cam = Camera()
        self.ssdv = SSDV(config['callsign'], config['ssid'])
        self.sstv = SSTV()
        self.webserver = WebServer()
        self.radio.play(config['frequencies']['APRS'], 'data/boatswain_whistle.wav')

        self.timers.handle({"APRS": True, "SSDV": True, "SSTV": False, "BUZZER": True}, [])

    def run(self):
        telemetry = {}
        exitFlag = False
        while not exitFlag:
            try:
                self.gps.loop()
                gpsdata = self.gps.get_data()
                if gpsdata['status'] == "fix" and gpsdata['alt'] > 0:
                    self.sensors.calibrate_alt(gpsdata['alt'])
                if gpsdata['status'] != "fix":
                    gpsdata['alt'] = self.sensors.read_pressure()
                sensordata = self.sensors.get_data()
                status_bits = self.calc_status_bits(gpsdata, sensordata)
                telemetry['Satellites'] = gpsdata['SatCount']
                telemetry['outside_temp'] = sensordata['outside_temp']
                telemetry['inside_temp'] = sensordata['inside_temp']
                telemetry['barometer'] = sensordata['barometer']
                telemetry['battery'] = 0
                self.webserver.update(gpsdata, sensordata)
                state, triggers = self.webserver.loop(self.timers.get_state())
                self.timers.handle(state, triggers)

                if self.timers.expired("APRS"):
                    if gpsdata['status'] == "fix":
                        print "sending location"
                        frame = self.aprs.create_location_msg(gpsdata, telemetry, status_bits)
                    else:
                        print "sending only telemetry"
                        frame = self.aprs.create_telem_data_msg(telemetry, status_bits, gpsdata['alt'])
                    self.modem.encode(frame)
                    self.modem.saveToFile(os.path.join(self.tmp_dir, 'aprs.wav'))
                    self.radio.play(self.config['frequencies']['APRS'], os.path.join(self.tmp_dir, 'aprs.wav'))

                if self.timers.expired("APRS-META"):
                    frame = self.aprs.create_telem_name_msg(telemetry, self.status_names)
                    self.modem.encode(frame)
                    self.modem.saveToFile(os.path.join(self.tmp_dir, 'aprs.wav'))
                    self.radio.play(self.config['frequencies']['APRS'], os.path.join(self.tmp_dir, 'aprs.wav'))

                if self.timers.expired("Capture"):
                    self.capture_image(gpsdata, sensordata, archive=False)

                if self.timers.expired("SSTV"):
                    self.capture_image(gpsdata, sensordata)
                    self.process_sstv()

                if self.timers.expired("SSTV-PLAY"):
                        self.radio.play(self.config['frequencies']['SSTV'], os.path.join(self.tmp_dir, 'sstv.wav'))

                if self.timers.expired("SSDV"):
                    self.capture_image(gpsdata, sensordata)
                    thread.start_new_thread(self.process_ssdv)

                if self.timers.expired("SSDV-PLAY"):
                    self.radio.play(config['frequencies']['APRS'], os.path.join(self.tmp_dir, 'ssdv.wav'))

                if timers.expired("BUZZER"):
                    for i in range(3):
                        GPIO.output(self.config['pins']['BUZZER'], GPIO.HIGH)
                        time.sleep(0.5)
                        GPIO.output(self.config['pins']['BUZZER'], GPIO.LOW)
                        time.sleep(0.5)

                time.sleep(1)

            except KeyboardInterrupt:  # If CTRL+C is pressed, exit cleanly
                exitFlag = True
                self.gps.stop()
                break
        print "Done."


if __name__ == "__main__":
    main = BalloonMissionComputer()
    main.setup()
    main.run()
