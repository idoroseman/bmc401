import logging

class MockGPIO(object):

    BCM = 0
    OUT = 0
    IN = 1
    LOW = 0
    HIGH = 1
    def __init__(self):
        logging.error("can not load raspberry pi GPIO module")

    @classmethod
    def setwarnings(cls, status):
        pass

    @classmethod
    def setmode(cls, mode):
        pass

    @classmethod
    def setup(cls, pin, mode):
        pass

    @classmethod
    def output(cls, pin, state):
        pass

    @classmethod
    def input(cls, pin):
        return None