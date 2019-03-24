from unittest import TestCase
from main import BalloonMissionComputer
from timers import Timers

class TestCalc_balloon_state(TestCase):


    def test_calc_balloon_state(self):
        bmc = BalloonMissionComputer()
        bmc.timers = Timers({ "BUZZER": 1 })
        bmc.state = "init"
        bmc.max_alt = 0
        bmc.min_alt = 9999999
        self.assertEqual("init", bmc.state )

        # while no gps
        bmc.calc_balloon_state({'alt': 0})
        self.assertEqual("init", bmc.state)

        # first altitute from gps
        bmc.calc_balloon_state( {'alt':150} )
        self.assertEqual("ground", bmc.state )

        # first alt over 2000m
        bmc.calc_balloon_state( {'alt':1500} )
        self.assertEqual("ground", bmc.state )
        bmc.calc_balloon_state( {'alt':2500} )
        self.assertEqual("ascent", bmc.state )

        # reaching the top
        bmc.calc_balloon_state({'alt': 30000})
        self.assertEqual("ascent", bmc.state)

        # falling down
        bmc.calc_balloon_state({'alt': 10000})
        self.assertEqual("descent", bmc.state)

        # approaching land
        # falling down
        bmc.calc_balloon_state({'alt': 1900})
        self.assertEqual("landed", bmc.state)
        self.assertTrue(bmc.timers.state["BUZZER"])