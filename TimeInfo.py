
import time
current_time_ms = lambda: int(round(time.time() * 1000))

from .WMInterface import WMInterface
from .SoarWME import SoarWME

class TimeInfo(WMInterface):
    def __init__(self):
        WMInterface.__init__(self)

        self.time_id = None
        self.seconds = SoarWME("seconds", 0) # number of real-time seconds elapsed since start of agent
        self.steps = SoarWME("steps", 0)     # number of decision cycles the agent has taken

        # Clock info, simulates a 24-hour clock tied to dc's as opposed to real-world time (advances some # of seconds every dc)
        self.clock_id = None
        self.clock_wmes = [ SoarWME("hour", 0), SoarWME("minute", 0), SoarWME("second", 0), SoarWME("elapsed-seconds", 0) ]
        self.reset_time()

    # Resets the time info
    def reset_time(self):
        self.clock_info = [8, 0, 0, 0] # [ hour, min, sec, tot-sec ]
        self.seconds.set_value(0)
        self.steps.set_value(0)
        self.start_time = current_time_ms()

    # Updates timers and advances the simulated clock n seconds
    def tick(self, num_secs=5):
        # Update clock
        self.clock_info[2] += num_secs
        if self.clock_info[2] >= 60:
            self.clock_info[2] -= 60
            self.clock_info[1] += 1
            if self.clock_info[1] >= 60:
                self.clock_info[1] -= 60
                self.clock_info[0] += 1
                if self.clock_info[0] >= 24:
                    self.clock_info[0] -= 24
        self.clock_info[3] += num_secs

        self.seconds.set_value(int((current_time_ms() - self.start_time)/1000))
        self.steps.set_value(self.steps.get_value() + 1)

    ### Internal methods

    def _add_to_wm_impl(self, parent_id):
        self.time_id = parent_id.CreateIdWME("time")
        self.seconds.add_to_wm(self.time_id)
        self.steps.add_to_wm(self.time_id)

        self.clock_id = self.time_id.CreateIdWME("clock")
        for i, wme in enumerate(self.clock_wmes):
            wme.set_value(self.clock_info[i])
            wme.add_to_wm(self.clock_id)

    def _update_wm_impl(self):
        self.seconds.update_wm()
        self.steps.update_wm()
        for i, wme in enumerate(self.clock_wmes):
            wme.set_value(self.clock_info[i])
            wme.update_wm()

    def _remove_from_wm_impl(self):
        for wme in self.clock_wmes:
            wme.remove_from_wm()
        self.time_id.DestroyWME()
        self.time_id = None
        self.clock_id = None

