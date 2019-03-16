import time

class Timers():
    def __init__(self, items):
        self.timeouts = items
        self.timestamps = {}

    def expired(self, id):
        now = time.time()
        if id not in self.timeouts:
            #raise Exception("item %s not in timers list" % id)
            pass
        elif id not in self.timestamps:
            self.timestamps[id] = now
            return False
        elif now - self.timestamps[id] > 60 * self.timeouts[id]:
            self.timestamps[id] = now
            return True
        else:
            return False




#########################################################################

if __name__ == "__main__":
    timers = timers({"One": 1, "Five": 5 })
    while True:
        if timers.expired("One"):
            print "One"
        if timers.expired("Five"):
            print "Five"
        time.sleep(10)
