import logging

class BmcSensor(object):
    def __init__(self, prefix=None):
        self.prefix = prefix + '_' if prefix else ""
        try:
            self.setup()
            self.isOk = True
        except Exception as x:
            logging.error(x)
            self.isOk = False

    def setup(self):
        raise NotImplementedError

    def bit(self):
        raise NotImplementedError

    def read(self):
        raise NotImplementedError