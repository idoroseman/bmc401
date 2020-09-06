import time
import logging

class Timers():
    def __init__(self, items):
        self.timeouts = items
        self.timestamps = {}
        self.state = {}
        self.triggers = []
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

    def expired(self, id):
        now = time.time()
        if id not in self.state:
            self.logger.info("added %s to states" % id)
            self.state[id] = False
        if id not in self.timeouts:
            self.logger.info("added %s to timeouts" % id)
            self.timeouts[id] = 0
            self.state[id] = False

        if id not in self.timestamps:
            self.timestamps[id] = now
            return False
        elif id in self.triggers or (self.state[id] and now - self.timestamps[id] > 60 * self.timeouts[id]):
            if id in self.triggers:
                self.triggers.remove(id)
            self.timestamps[id] = now
            return True
        else:
            return False

    def get_state(self):
        return self.state

    def handle(self, state, triggers):
        if state is not None:
            for item in state:
                self.state[item] = state[item]
#                self.logger.debug("timer %s enabled" % item if state[item] else "timer %s disabled" % item)

        if type(triggers) is list:
            if len(triggers)>0:
                self.logger.info("triggering: %s" % triggers)
                self.triggers += triggers


#########################################################################

if __name__ == "__main__":
    timers = Timers({"One": 1, "Five": 5 })
    while True:
        if timers.expired("One"):
            print("One")
        if timers.expired("Five"):
            print("Five")
        time.sleep(10)
