import os
import sys
import json
import datetime
import time
import _thread
import subprocess

try:
    # rpi hardware specific
    import RPi.GPIO as GPIO
    from dorji import Dorji
    from sensors import Sensors
    from camera import Camera
except Exception as x:
    print(x)

from aprs import APRS
from modem import AFSK
from ublox import Ublox
from timers import Timers
from ssdv import SSDV
from sstv import SSTV
from webserver import WebServer
import threading
import queue

CAMERAS = 1

class BalloonMissionComputer():

    def calc_status_bits(self, gpsdata, sensordata):
        bits = [True,
                False,
                False,
                False,
                gpsdata['status'] == "fix",
                gpsdata['status'] == "lost",
                gpsdata['status'] == "comm error",
                gpsdata['status'] == "i2c error"]
        return ''.join(['1' if val else '0' for val in bits])

    status_names = ['gps i2c err', "gps comm err", "gps no fix", "gps ok"]

    def calc_balloon_state(self, gpsdata):
        current_alt = float(gpsdata['alt'])
        if self.state == "init" and current_alt > 0:
            self.state = "ground"
            self.send_bulltin()
        if self.state == "ground" and current_alt > self.min_alt + 2000:
            self.state = "ascent"
            self.send_bulltin()
        if self.state == "ascent" and current_alt < self.max_alt - 2000:
            self.state = "descent"
            self.send_bulltin()
        if self.state == "descent" and current_alt < 2000:
            self.state = "landed"
            self.send_bulltin()
            self.timers.handle({'BUZZER':True}, [])

        if current_alt > self.max_alt:
            self.max_alt = current_alt
        if current_alt > 0 and current_alt < self.min_alt:
            self.min_alt = current_alt
        self.prev_alt = current_alt

    def update_datetime(self, gpsdata):
        if 'date' not in gpsdata:
            return
        now = datetime.datetime.now()
        gpstime = datetime.datetime.strptime(gpsdata['date']+ " " + gpsdata['fixTimeStr'], "%d%m%y %H:%M:%S")
        diff = int(abs((now-gpstime).total_seconds()/60))
        if diff > 100 :
           print("system time", now)
           print("gps time", gpstime)
           print("updating")
#           os.system('date -s %s' % gpstime.isoformat())
           proc = subprocess.Popen(["date", "-s %s" % gpstime.isoformat()], stdout=subprocess.PIPE, shell=True)
           (out, err) = proc.communicate()
           print("program output:", out)
           print("program error:", err)
           #todo: verify we have premissions

    def send_bulltin(self):
        try:
            print("state changed to %s" % self.state)
            frame = self.aprs.create_message_msg("BLN1BALON", "changed state to %s" % self.state)
            self.modem.encode(frame)
            self.modem.saveToFile(os.path.join(self.tmp_dir, 'aprs.wav'))
            self.radio_queue(self.config['frequencies']['APRS'], os.path.join(self.tmp_dir, 'aprs.wav'))
        except:
            pass

    def capture_image(self, archive=True):
        self.cam.capture()
        if archive:
          self.cam.archive()

    def prep_image(self, id, gpsdata, sensordata):
        self.cam.select(id)
        self.cam.resize((320, 256))
        self.cam.overlay(self.config['callsign'], gpsdata, sensordata)
        self.cam.saveToFile(os.path.join(self.tmp_dir,"image.jpg"))

    def process_ssdv(self):
        self.ssdv.convert('tmp/image.jpg', 'tmp/image.ssdv')
        packets = self.ssdv.prepare(os.path.join(self.tmp_dir, "image.ssdv"))
        modem = AFSK()
        modem.encode(packets)
        modem.saveToFile(os.path.join(self.tmp_dir, 'ssdv.wav'))
        self.timers.handle(None, ["PLAY-SSDV"])

    def process_sstv(self):
        self.sstv.image = self.cam.image
        self.sstv.process()
        self.sstv.saveToFile(os.path.join(self.tmp_dir, 'sstv.wav'))
        self.timers.handle(None, ["PLAY-SSTV"])

    def setup(self):
        # setup
        with open('data/config.json') as fin:
            self.config = json.load(fin)
        self.images_dir = self.config["directories"]["images"] if "directories" in self.config and "images" in self.config["directories"] else "./images"
        self.tmp_dir = self.config["directories"]["tmp"] if "directories" in self.config and "tmp" in self.config["directories"] else "./tmp"

        if not os.path.exists(self.tmp_dir):
            os.makedirs(self.tmp_dir)

        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)  # Broadcom pin-numbering scheme
        GPIO.setup(self.config['pins']['BUZZER'], GPIO.OUT)
        GPIO.setup(self.config['pins']['LED1'], GPIO.OUT)
        GPIO.setup(self.config['pins']['LED2'], GPIO.OUT)

        self.aprs = APRS(self.config['callsign'], self.config['ssid'], "idoroseman.com")
        self.modem = AFSK()
        self.gps = Ublox()
        self.gps.start()
        self.radio = Dorji(self.config['pins'])
        self.radio.init()
        self.radio_q = queue.Queue()
        self.radio_thread = threading.Thread(target=self.radio_worker)
        self.radio_thread.start()
        self.timers = Timers(self.config['timers'])
        self.sensors = Sensors()
        self.cam = Camera()
        self.ssdv = SSDV(self.config['callsign'], self.config['ssid'])
        self.sstv = SSTV()
        self.webserver = WebServer()
        self.radio_queue(self.config['frequencies']['APRS'], 'data/boatswain_whistle.wav')

        self.timers.handle({"APRS": True, "APRS-META":True, "Imaging": True,"Buzzer": False, 'Capture': True}, [])

        self.imaging_counter = 1
        self.state = "init"
        self.min_alt = sys.maxsize
        self.max_alt = 0
        self.prev_alt = 0
        self.send_bulltin()

    def run(self):
        telemetry = {}
        exitFlag = False
        while not exitFlag:
            try:
                self.gps.loop()
                gpsdata = self.gps.get_data()
                self.calc_balloon_state(gpsdata)
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
                self.webserver.update(gpsdata, sensordata, self.state)
                state, triggers = self.webserver.loop(self.timers.get_state())
                self.timers.handle(state, triggers)
                self.update_datetime(gpsdata)

                if self.timers.expired("APRS"):
                    if gpsdata['status'] == "fix":
                        print("sending location")
                        frame = self.aprs.create_location_msg(gpsdata, telemetry, status_bits)
                    else:
                        print("sending only telemetry")
                        frame = self.aprs.create_telem_data_msg(telemetry, status_bits, gpsdata['alt'])
                    self.modem.encode(frame)
                    self.modem.saveToFile(os.path.join(self.tmp_dir, 'aprs.wav'))
                    self.radio_queue(self.config['frequencies']['APRS'], os.path.join(self.tmp_dir, 'aprs.wav'))
                    with open(os.path.join(self.tmp_dir, "flight.log"), 'a+') as f:
                        merged = dict()
                        merged.update(gpsdata)
                        merged.update(sensordata)
                        merged['datatime'] = datetime.datetime.now().isoformat()
                        f.write(json.dumps(merged, indent=2))
                        f.write(',\n')

                if self.timers.expired("APRS-META"):
                    frame = self.aprs.create_telem_name_msg(telemetry, self.status_names)
                    self.modem.encode(frame)
                    self.modem.saveToFile(os.path.join(self.tmp_dir, 'aprs.wav'))
                    self.radio_queue(self.config['frequencies']['APRS'], os.path.join(self.tmp_dir, 'aprs.wav'))

                if self.timers.expired("Capture"):
                    self.capture_image()

                if self.timers.expired("Snapshot"):
                    self.imaging_counter += 1
                    cam_select = self.imaging_counter % CAMERAS
                    self.capture_image(archive=False)
                    self.prep_image(cam_select, gpsdata, sensordata)

                if self.timers.expired("Imaging"):
                    self.imaging_counter += 1
                    cam_select = self.imaging_counter % CAMERAS
                    cam_system = self.imaging_counter % (CAMERAS+1)
                    self.capture_image(archive=False)
                    self.prep_image(cam_select, gpsdata, sensordata)
                    if cam_system == 0:
                        self.process_sstv()
                    else:
                        _thread.start_new_thread(self.process_ssdv, () )

                if self.timers.expired("PLAY-SSDV"):
                    self.radio_queue(self.config['frequencies']['APRS'], os.path.join(self.tmp_dir, 'ssdv.wav'))

                if self.timers.expired("PLAY-SSTV"):
                        self.radio_queue(self.config['frequencies']['APRS'], os.path.join("data", 'switching_to_sstv.wav'))
                        self.radio_queue(self.config['frequencies']['SSTV'], os.path.join("data", 'starting_sstv.wav'))
                        self.radio_queue(self.config['frequencies']['SSTV'], os.path.join(self.tmp_dir, 'sstv.wav'))

                if self.timers.expired("Buzzer"):
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
            except Exception as x:
                print("unhandled exception")
                print(x)
        print("Done.")

    def radio_queue(self, freq, filename):
        self.radio_q.put({'freq':freq, 'filename':filename})

    def radio_worker(self):
        while True:
            item = self.radio_q.get()
            self.radio.play(item['freq'], item['filename'])
            self.radio_q.task_done()

if __name__ == "__main__":
    bmc = BalloonMissionComputer()
    bmc.setup()
    bmc.run()
