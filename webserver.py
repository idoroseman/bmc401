#!/usr/bin/python
from flask import Flask, request, send_file, redirect, send_from_directory
from flask_restful import Resource, Api, reqparse
from flask_cors import CORS
from flask_socketio import SocketIO, send, emit

import datetime
import os
import threading
import requests
import time
import logging
import json

from timers import Timers

PORT_NUMBER = 8080

app = Flask(__name__, static_url_path='/static', static_folder='webapp/build/static/')
app.config['SECRET_KEY'] = 'secret!'

api = Api(app)
CORS(app)

socketio = SocketIO(app, cors_allowed_origins="*")

parser = reqparse.RequestParser()

def handle_state_change():
    socketio.emit("timers", timers.get_states())

timers = Timers()
timers.subscribe(handle_state_change)

#-----------------------------------------------------


class Log(Resource):
    def get(self):
        return logs

api.add_resource(Log, '/logs')

#-----------------------------------------------------

@socketio.on('connect')
def test_connect():
    emit("timers", timers.get_states())
    emit("status", {})
    emit('gps', gpsdata)
    emit('sensors', telemetry)
    with open('assets/config.json') as fin:
        config = json.load(fin)
        emit('mission', { 'name':config['name'].capitalize(), 'callsign': '-'.join([ config['callsign'], str(config['ssid'])])})

@socketio.on('timer')
def handle_timer(data):
    if data['name'] == "*":
        for name in timers.get_states():
            timers.set_state(name, False)
    else:
        timers.set_state(data['name'], data['value'])

@socketio.on('trigger')
def handle_trigger(name):
    timers.trigger(name)

#-----------------------------------------------------

def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()

@app.route('/shutdown', methods=['POST'])
def shutdown():
    print("flask shutdown")
    shutdown_server()
    return 'Server shutting down...'

#-----------------------------------------------------

@app.route('/cmnd')
def handle_cmnd():
    def clear_folder(folder):
        try:
            files = os.listdir(folder)
            for f in files:
                os.delete(folder + f)
        except:
            pass

    cmnd = request.args.get('cmnd', '')
    logging.info(cmnd)
    if cmnd == "prefilght":
        clear_folder('tmp/')
        clear_folder('images/')
    return "ok"

@app.route('/')
def index():
    try:
       return send_file('webapp/build/index.html')
    except Exception as x:
        logging.error("GET / : %s" % x)

#-----------------------------------------------------

@app.route('/imaging')
@app.route('/imaging/<sensor>')
def show(sensor='image.jpg'):
    try:
        print("tmp",sensor)
        return send_from_directory('tmp',sensor)
    except Exception as x:
        print(x)
        return send_from_directory('assets', 'testcard.jpg')

gpsdata = {'status': 'fix',
           'latDir': 'N',
           'FixType': 'A3',
           'fixTime': '163018.00',
           'lat_raw': '3203.79986',
           'lat': 0,
           'alt': 0,
           'navmode': 'flight',
           'lonDir': 'E',
           'groundSpeed': '36.2',
           'lon': 0,
           'SatCount': 0,
           'groundCourse': '123',
           'lon_raw': '03452.32994',
           'fixTimeStr': '16:30',
           'accentRate': 0.40599678574441816
           }
telemetry = {'Satellites':4,
         'outside_temp':0,
         'inside_temp':0,
         'barometer':1024,
         'Battery':5 }

state = {}
triggers = []
sysstate = "loading"
start_time = datetime.datetime.now()

# This class will handles any incoming request from
# the browser

# class myHandler(BaseHTTPRequestHandler):
#
#     # override log handler to supress logging
#     def log_message(self, format, *args):
#         return
#
#     # Handler for the GET requests
#     def do_GET(self):
#         if self.path.endswith(".jpg"):
#             f = open('tmp/' + self.path, "rb")
#             self.send_response(200)
#             self.send_header('Content-type', 'image/jpg')
#             self.end_headers()
#             self.wfile.write(f.read())
#             f.close()
#             return
#         elif self.path.endswith(".png"):
#             f = open('assets/' + self.path, "rb")
#             self.send_response(200)
#             self.send_header('Content-type', 'image/png')
#             self.end_headers()
#             self.wfile.write(f.read())
#             f.close()
#             return
#         elif self.path.endswith(".ico"):
#             self.send_response(404)
#             self.end_headers()
#             return
#         else:
#             self.send_response(200)
#             self.send_header('Content-type', 'text/html')
#             self.end_headers()
#             query = urlparse(self.path).query
#             query_components = dict(qc.split("=") for qc in query.split("&") if qc != "")
#             for item in query_components:
#                 if item=='trigger':
#                     triggers.append(query_components[item])
#                 elif item=='enable':
#                     state[query_components[item]] = True
#                 elif item=='disable':
#                     if query_components[item] == "ALL":
#                         for item in state:
#                           state[item]=False
#                     else:
#                         state[query_components[item]] = False
#                 elif item=="prefilght":
#                     self.clear_folder('tmp/')
#                     self.clear_folder('images/')
#
#             # Send the html message
#             rv = ""
#             rv += """
#             <html>
#             <head>
#                 <meta http-equiv="refresh" content="30; url=/">
#                 <meta http-equiv="Cache-Control" content="private" />
#             </head>
#             <body>
#             <h3>Balloon 6 Server</h3>
#             <table border="0">
#             """
#
#             now = datetime.datetime.now()
#             rv += """
#             <tr><td>Date</td><td>%s</td></tr>
#             <tr><td>Time</td><td>%s</td></tr>
#             """ % (datetime.datetime.strftime(now, "%Y-%m-%d"), datetime.datetime.strftime(now, "%H:%M:%S"))
#
#             uptime = str(now-start_time).split('.')[0]
#             rv += """
#             <tr><td>state</td><td>%s</td></tr>
#             <tr><td>uptime</td><td>%s</td></tr>
#             """ % (sysstate, uptime)
#
#             rv += """
#             <tr><td>Lat</td><td>%2.4f</td></tr>
#             <tr><td>Lon</td><td>%2.4f</td></tr>
#             <tr><td>Alt</td><td>%s</td></tr>
#             <tr></tr>
#             <tr><td>Status</td><td>%s</td></tr>
#             <tr><td>Sats</td><td>%s</td></tr>""" % (gpsdata['lat'], gpsdata['lon'], gpsdata['alt'], gpsdata['status'], gpsdata['SatCount'])
#
#             rv += """
#
#             <tr></tr>
#             <tr><td>Temp out</td><td>%2.1f</td></tr>
#             <tr><td>Temp in</td><td>%2.1f</td></tr>
#             <tr><td>Barometer</td><td>%4.1f</td></tr>
#             <tr><td>Battery</td><td>%4.1f</td></tr>
#             <tr></tr>""" % (telemetry['outside_temp'], telemetry['inside_temp'], telemetry['barometer'], telemetry['battery'])
#
#             for system in state:
#                 try:
#                     rv += "<tr><td>%s</td>" % system
#                     if state[system]:
#                         rv += '<td bgcolor="#80FF80">Enabled</td><td><a href="?disable=%s">Disable</a></td>' % system
#                     else:
#                         rv += '<td ><a href="?enable=%s">Enable</a></td><td bgcolor="#FF8080">Disabled</td>' % system
#                     rv += '<td><a href="?trigger=%s">Trigger</a></td>' % system
#                     rv += '</tr>'
#                 except KeyError as x:
#                     state[x.message]=False
#             rv += """
#             <tr><td></td><td></td><td><a href="?disable=ALL">Disable ALL</a><td></tr>
#             </table>
#             <br/>
#             last image <a href="?trigger=Snapshot">recapture</a><br/>
#             <img src="image.jpg" width="320px"/>
#             <a href="?prefilght">Clear Folders</a>
#             </body>
#             </html>
#             """
#
#             rv += """
#             </table>
#             </body>
#             </html>
#             """
#             self.wfile.write(rv.encode('utf-8'))
#             return
#
#     def clear_folder(self, folder):
#         files = os.listdir(folder)
#         for f in files:
#             os.delete(folder + f)


class WebServer():
    def __init__(self):
        self.server = threading.Thread(target=socketio.run, args=[app], kwargs={'host': '0.0.0.0', 'port':PORT_NUMBER})
        self.server.start()

    def update(self, gpsd, telemd, state):
        global gpsdata
        global telemetry
        global sysstate
        gpsdata = gpsd
        telemetry= telemd
        sysstate = sysstate

        socketio.emit('gps', gpsdata)
        socketio.emit('sensors', telemetry)

        now = datetime.datetime.now()
        status = {
            'date': datetime.datetime.strftime(now, "%Y-%m-%d"),
            'time': datetime.datetime.strftime(now, "%H:%M:%S"),
            'uptime':str(now-start_time).split('.')[0],
            'appstate': sysstate
        }
        socketio.emit('status', status)

    def close(self):
        r = requests.post('http://localhost:5000/shutdown')
        self.server.join()

    def report(self, data):
        socketio.emit('debug', data)

    def snapshot(self):
        socketio.emit("snapshot", None)

    def log(self, msg):
        socketio.emit("log", msg.strip())

if __name__ == "__main__":
    webserver = WebServer()

    sensord= {
        'tempout': 17.2,
        'tempin': -2,
        'barometer': 1000,
        'battery': 3.4
    }
    while True:
        time.sleep(1)
        webserver.update(gpsdata, sensord, "test")

