from unittest import TestCase
from main import calc_balloon_state

class TestCalc_balloon_state(TestCase):
    def test_calc_balloon_state(self):
        calc_balloon_state(150)
        self.fail()
