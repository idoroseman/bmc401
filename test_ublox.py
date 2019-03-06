from unittest import TestCase
from ublox import Ublox

class TestUblox(TestCase):
    def test_parse_gngga(self):
        gps = Ublox()
        test_input = [ '$GNGGA,130706.00,3203.82887,N,03452.29882,E,1,08,1.79,99.4,M,17.4,M,,',
                       '$GNGGA,130702.00,3203.82879,N,03452.29869,E,1,07,1.79,99.9,M,17.4,M,,',

                       '$GNGGA,124436.00,3203.8585,N,03452.29945,E,1,12,0.91,87.6,M,17.4,M3',
                       '$GNGGA,115233.003203.82821,N,03452.30067,E,1,12,1.41,89.4,M17.4,M,,' ]
        for line in test_input:
            tokens = line.split(',')
            try:
                rv = gps.parse_gngga(tokens)
            except:
                self.fail()
