#!/usr/bin/python
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from urlparse import urlparse

PORT_NUMBER = 80

gpsdata = {'status': 'fix',
           'latDir': 'N',
           'FixType': 'A3',
           'fixTime': '163018.00',
           'lat_raw': '3203.79986',
           'lat': 32.063331,
           'alt': 129.7,
           'navmode': 'flight',
           'lonDir': 'E',
           'groundSpeed': '36.2',
           'lon': 34.87216566666667,
           'SatCount': 4,
           'groundCourse': '123',
           'lon_raw': '03452.32994',
           'fixTimeStr': '16:30',
           'accentRate': 0.40599678574441816
           }
telemetry = {'Satellites':4,
         'TemperatureIn':26,
         'TemperatureOut':26,
         'Pressure':1024,
         'Battery':5 }

systems = {"APRS", "SSDV", "SSTV"}
state = {}
triggers = []

# This class will handles any incoming request from
# the browser
class myHandler(BaseHTTPRequestHandler):

    # Handler for the GET requests
    def do_GET(self):
        if self.path.endswith(".jpg"):
            f = open('images/' + self.path, "rb")
            self.send_response(200)
            self.send_header('Content-type', 'image/png')
            self.end_headers()
            self.wfile.write(f.read())
            f.close()
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
                    state[query_components[item]] = False
            # Send the html message
            rv = ""
            rv += """
            <html>
            <head>
                <meta http-equiv="refresh" content="30">
            </head>
            <body>
            <h3>Ballon 5 Server</h3>
            <table border="0">
            """

            rv += """
            <tr><td>Lat</td><td>%2.4f</td></tr>
            <tr><td>Lon</td><td>%2.4f</td></tr>
            <tr><td>Alt</td><td>%s</td></tr>
            <tr></tr>
            <tr><td>Status</td><td>%s</td></tr>
            <tr><td>Sats</td><td>%s</td></tr>""" % (gpsdata['lat'], gpsdata['lon'], gpsdata['alt'], gpsdata['status'], gpsdata['SatCount'])

            rv += """
    
            <tr></tr>
            <tr><td>Temp in</td><td>%2.1f</td></tr>
            <tr><td>Temp out</td><td>%2.1f</td></tr>
            <tr><td>Barometer</td><td>%4.1f</td></tr>
            <tr></tr>""" % (telemetry['TemperatureOut'], telemetry['TemperatureIn'], telemetry['Pressure'])

            for system in systems:
                try:
                    rv += "<tr><td>%s</td>" % system
                    if state[system]:
                        rv += '<td>Enabled</td><td><a href="?disable=%s">Disable</a></td>' % system
                    else:
                        rv += '<td><a href="?enable=%s">Enable</a></td><td>Disabled</td>' % system
                    rv += '<td><a href="?trigger=%s">Trigger</a></td>' % system
                    rv += '</tr>'
                except KeyError as x:
                    state[x.message]=False

            rv += """
            </table>
            <br/>
            last image <a href="?refresh=image">refresh</a><br/>
            <img src="picture.jpg"/></td></tr>
            </body>
            </html>
            """

            rv += """
            </table>
            </body>
            </html>
            """
            self.wfile.write(rv)
            return

class WebServer():
    def __init__(self):
        # Create a web server and define the handler to manage the
        # incoming request
        self.server = HTTPServer(('', PORT_NUMBER), myHandler)
        print 'Started httpserver on port ', PORT_NUMBER
        self.server.timeout = 1
        # Wait forever for incoming htto requests
        #server.serve_forever()

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