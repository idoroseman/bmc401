import time

class Timers():
    def __init__(self, items):
        self.timeouts = items
        self.timestamps = {}
        self.state = {}
        self.triggers = []

    def expired(self, id):
        now = time.time()
        if id not in self.state:
            self.state[id] = False

        if id not in self.timeouts:
            #raise Exception("item %s not in timers list" % id)
            self.timeouts[id] = 0
            self.state[id] = False
        elif id not in self.timestamps:
            self.timestamps[id] = now
            return False
        elif id in self.triggers or (self.state[id] and now - self.timestamps[id] > 60 * self.timeouts[id]):
            if id in self.triggers:
                print "extracting trigger %s" % id
                self.triggers.remove(id)
            self.timestamps[id] = now
            return True
        else:
            return False

    def handle(self, state, triggers):
        self.state = state
        self.triggers += triggers


#########################################################################

if __name__ == "__main__":
    timers = Timers({"One": 1, "Five": 5 })
    while True:
        if timers.expired("One"):
            print "One"
        if timers.expired("Five"):
            print "Five"
        time.sleep(10)
