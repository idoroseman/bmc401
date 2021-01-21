import time
import logging

# singelton pattern by https://python-3-patterns-idioms-test.readthedocs.io/en/latest/Singleton.html

class Borg:
    _shared_state = {}
    def __init__(self):
        self.__dict__ = self._shared_state

class Timers(Borg):
    def __init__(self, items={}):
        Borg.__init__(self)
        # initiate only once
        if not hasattr(self, "timeouts"):
            self.timeouts = {}
            self.timestamps = {}
            self.state = {}
            self.triggers = []
        self.timeouts.update(items)

        if not hasattr(self, "logger"):
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

    def set_state(self, name, enabled):
        self.state[name] = enabled

    def trigger(self, name):
        if name not in self.triggers:
            self.triggers.append(name)

#     def get_state(self):
#         return self.state
#
#     def handle(self, state, triggers):
#         if state is not None:
#             for item in state:
#                 self.state[item] = state[item]
# #                self.logger.debug("timer %s enabled" % item if state[item] else "timer %s disabled" % item)
#
#         if type(triggers) is list:
#             if len(triggers)>0:
#                 self.logger.info("triggering: %s" % triggers)
#                 self.triggers += triggers


#########################################################################

if __name__ == "__main__":
    timers = Timers({"One": 0.1, "Four": 0.25, "Five": 0.5 })
    timers.set_state("One", True)
    timers.set_state("Five", True)
    while True:
        if timers.expired("One"):
            print("One")
        if timers.expired("Five"):
            print("Five")
        time.sleep(1)
        print("tick")
