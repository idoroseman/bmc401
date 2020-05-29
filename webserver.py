#!/usr/bin/python
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse
import datetime
import os

PORT_NUMBER = 8080

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
sysstate = ""
start_time = datetime.datetime.now()

# This class will handles any incoming request from
# the browser
class myHandler(BaseHTTPRequestHandler):

    # override log handler to supress logging
    def log_message(self, format, *args):
        return

    # Handler for the GET requests
    def do_GET(self):
        if self.path.endswith(".jpg"):
            f = open('tmp/' + self.path, "rb")
            self.send_response(200)
            self.send_header('Content-type', 'image/jpg')
            self.end_headers()
            self.wfile.write(f.read())
            f.close()
            return
        elif self.path.endswith(".png"):
            f = open('data/' + self.path, "rb")
            self.send_response(200)
            self.send_header('Content-type', 'image/png')
            self.end_headers()
            self.wfile.write(f.read())
            f.close()
            return
        elif self.path.endswith(".ico"):
            self.send_response(404)
            self.end_headers()
            return
        else:
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            query = urlparse(self.path).query
            query_components = dict(qc.split("=") for qc in query.split("&") if qc != "")
            for item in query_components:
                if item=='trigger':
                    triggers.append(query_components[item])
                elif item=='enable':
                    state[query_components[item]] = True
                elif item=='disable':
                    if query_components[item] == "ALL":
                        for item in state:
                          state[item]=False
                    else:
                        state[query_components[item]] = False
                elif item=="prefilght":
                    self.clear_folder('tmp/')
                    self.clear_folder('images/')

            # Send the html message
            rv = ""
            rv += """
            <html>
            <head>
                <meta http-equiv="refresh" content="30; url=/">
                <meta http-equiv="Cache-Control" content="private" />
            </head>
            <body>
            <h3>Balloon 6 Server</h3>
            <table border="0">
            """

            now = datetime.datetime.now()
            rv += """
            <tr><td>Date</td><td>%s</td></tr>
            <tr><td>Time</td><td>%s</td></tr>
            """ % (datetime.datetime.strftime(now, "%Y-%m-%d"), datetime.datetime.strftime(now, "%H:%M:%S"))

            uptime = str(now-start_time).split('.')[0]
            rv += """
            <tr><td>state</td><td>%s</td></tr>
            <tr><td>uptime</td><td>%s</td></tr>
            """ % (sysstate, uptime)

            rv += """
            <tr><td>Lat</td><td>%2.4f</td></tr>
            <tr><td>Lon</td><td>%2.4f</td></tr>
            <tr><td>Alt</td><td>%s</td></tr>
            <tr></tr>
            <tr><td>Status</td><td>%s</td></tr>
            <tr><td>Sats</td><td>%s</td></tr>""" % (gpsdata['lat'], gpsdata['lon'], gpsdata['alt'], gpsdata['status'], gpsdata['SatCount'])

            rv += """
    
            <tr></tr>
            <tr><td>Temp out</td><td>%2.1f</td></tr>
            <tr><td>Temp in</td><td>%2.1f</td></tr>
            <tr><td>Barometer</td><td>%4.1f</td></tr>
            <tr></tr>""" % (telemetry['outside_temp'], telemetry['inside_temp'], telemetry['barometer'])

            for system in state:
                try:
                    rv += "<tr><td>%s</td>" % system
                    if state[system]:
                        rv += '<td bgcolor="#80FF80">Enabled</td><td><a href="?disable=%s">Disable</a></td>' % system
                    else:
                        rv += '<td ><a href="?enable=%s">Enable</a></td><td bgcolor="#FF8080">Disabled</td>' % system
                    rv += '<td><a href="?trigger=%s">Trigger</a></td>' % system
                    rv += '</tr>'
                except KeyError as x:
                    state[x.message]=False
            rv += """
            <tr><td></td><td></td><td><a href="?disable=ALL">Disable ALL</a><td></tr>
            </table>
            <br/>
            last image <a href="?trigger=Snapshot">recapture</a><br/>
            <img src="image.jpg" width="320px"/>
            <a href="?prefilght">Clear Folders</a>
            </body>
            </html>
            """

            rv += """
            </table>
            </body>
            </html>
            """
            self.wfile.write(rv.encode('utf-8'))
            return

    def clear_folder(self, folder):
        files = os.listdir(folder)
        for f in files:
            os.delete(folder + f)


class WebServer():
    def __init__(self):
        # Create a web server and define the handler to manage the
        # incoming request
        self.server = HTTPServer(('', PORT_NUMBER), myHandler)
        print('Started httpserver on port ', PORT_NUMBER)
        self.server.timeout = 1
        # Wait forever for incoming htto requests
        #server.serve_forever()

    def update(self, gpsd, telemd, stated):
        global gpsdata
        global telemetry
        global sysstate
        gpsdata = gpsd
        telemetry= telemd
        sysstate = stated

    def loop(self, new_state):
        global state
        global triggers
        state = new_state
        self.server.handle_request()
        tmp = triggers
        triggers = []
        return state, tmp

    def close(self):
        self.server.socket.close()

if __name__ == "__main__":
    webserver = WebServer()
    while True:
        try:
            state, triggers = webserver.loop(state)
        except KeyboardInterrupt:
            webserver.close()
            break
