
import time
import datetime
current_time_ms = lambda: int(round(time.time() * 1000))

from .AgentConnector import AgentConnector
from .SoarWME import SoarWME

class TimeConnector(AgentConnector):
    """ An agent connector that will maintain time info on the input-link 
    
        The input link will look like:
        (<il> ^time <t>)
        (<t> ^seconds <secs> # real-time seconds elapsed since start of agent
             ^milliseconds <ms> # real-time milliseconds elapsed since start
             ^steps <steps> # number of decision cycles since start of agent
             ^clock <clock>)
        (<clock> ^hour <hr> # 0-23
                 ^minute <min> # 0-59
                 ^second <sec> # 0-59
                 ^millisecond <ms> # 0-999
                 ^epoch <sec> # Unix epoch time in seconds)

        Also, if using a simulated clock, the agent can send the following output-command:
        (<out> ^set-time <st>) (<st> ^hour <h> ^minute <min> ^second <sec>)

        Settings: 
            clock_include_ms: bool [default=True]
                If true, includes milliseconds with both elapsed time and clock time
            sim_clock: bool [default=False]
                If true, uses a simulated clock that starts at 8AM and advances a fixed amount every DC
                If false, will use the local real time
            clock_step_ms: int [default=5000]
                If using the simulated clock, this is the number of milliseconds it will increase every DC

    """
    def __init__(self, client, clock_include_ms=True, sim_clock=False, clock_step_ms=50, **kwargs):
        """ Initializes the connector with the time info

        clock_include_ms - If True: will include millisecond resolution on clock/elapsed
            (Setting to false will mean fewer changes to the input-link, slightly faster)
        sim_clock - If False: clock uses real-time. If True: clock is simulated
        clock_step_ms - If sim_clock=True, this is how much the clock advances every DC
        """
        AgentConnector.__init__(self, client)

        self.include_ms = clock_include_ms
        self.sim_clock = sim_clock
        self.clock_step_ms = int(clock_step_ms)

        self.time_id = None
        self.seconds = SoarWME("seconds", 0) # number of real-time seconds elapsed since start of agent
        self.milsecs = SoarWME("milliseconds", 0) # number of real-time milliseconds elapsed since start of agent
        self.steps = SoarWME("steps", 0)     # number of decision cycles the agent has taken

        # Output Link Command: (<out> ^set-time <st>) (<st> ^hour <h> ^minute <min> ^second <sec>)
        self.add_output_command("set-time")

        # Clock info, hour minute second millisecond
        self.clock_id = None
        self.clock_info = [0, 0, 0, 0, 0]
        self.clock_wmes = [ SoarWME("hour", 0), SoarWME("minute", 0), SoarWME("second", 0), SoarWME("millisecond", 0), SoarWME("epoch", 0) ]
        self.reset_time()

    def advance_clock(self, num_ms):
        """ Advances the simulated clock by the given number of milliseconds """
        self.clock_info[3] += num_ms
        # MS
        if self.clock_info[3] >= 1000:
            self.clock_info[2] += self.clock_info[3] // 1000
            self.clock_info[4] += self.clock_info[3] // 1000
            self.clock_info[3] = self.clock_info[3] % 1000
            # Seconds
            if self.clock_info[2] >= 60:
                self.clock_info[1] += self.clock_info[2] // 60
                self.clock_info[2] = self.clock_info[2] % 60
                # Minutes
                if self.clock_info[1] >= 60:
                    self.clock_info[0] += self.clock_info[1] // 60
                    self.clock_info[1] = self.clock_info[1] % 60
                # Hours
                self.clock_info[0] = self.clock_info[0] % 24

    def update_clock(self):
        """ Updates the clock with the real time """
        localtime = time.localtime()
        self.clock_info[0] = localtime.tm_hour
        self.clock_info[1] = localtime.tm_min
        self.clock_info[2] = localtime.tm_sec
        self.clock_info[3] = current_time_ms() % 1000
        self.clock_info[4] = int(time.time())

    def reset_time(self):
        """ Resets the time info """
        # If simulating clock, default epoch is Jan 1, 2020 at 8 AM
        default_epoch = int(time.mktime(datetime.datetime(2020, 1, 1, 8, 0, 0, 0).timetuple()))
        self.clock_info = [8, 0, 0, 0, default_epoch] # [ hour, min, sec, ms, epoch ]
        self.milsecs.set_value(0)
        self.seconds.set_value(0)
        self.steps.set_value(0)
        self.start_time = current_time_ms()

    def on_init_soar(self):
        self._remove_from_wm()
        self.reset_time()

    def set_time(self, hour, min, sec=0, ms=0):
        if not self.sim_clock:
            return
        self.clock_info[0] = hour
        self.clock_info[1] = (0 if min is None else min)
        self.clock_info[2] = (0 if sec is None else sec)
        self.clock_info[3] = ms
        self.clock_info[4] = int(time.mktime(datetime.datetime(2020, 1, 1, hour, min, sec, ms).timetuple()))

    def on_input_phase(self, input_link):
        # Update the global timers (time since agent start)
        self.milsecs.set_value(int(current_time_ms() - self.start_time))
        self.seconds.set_value(int((current_time_ms() - self.start_time)/1000))
        self.steps.set_value(self.steps.get_value() + 1)

        # Update the clock, either real-time or simulated
        if self.sim_clock:
            self.advance_clock(self.clock_step_ms)
        else:
            self.update_clock()

        # Update working memory
        if self.time_id is None:
            self._add_to_wm(input_link)
        else:
            self._update_wm()

    def on_output_event(self, command_name, root_id):
        if command_name == "set-time":
            self.process_set_time_command(root_id)
    
    def process_set_time_command(self, time_id):
        h = time_id.GetChildInt('hour')
        m = time_id.GetChildInt('minute')
        s = time_id.GetChildInt('second')
        self.set_time(h, m, s)
        time_id.CreateStringWME('status', 'complete')

    ### Internal methods

    def _add_to_wm(self, parent_id):
        self.time_id = parent_id.CreateIdWME("time")
        if self.include_ms:
            self.milsecs.add_to_wm(self.time_id)
        self.seconds.add_to_wm(self.time_id)
        self.steps.add_to_wm(self.time_id)

        self.clock_id = self.time_id.CreateIdWME("clock")
        for i, wme in enumerate(self.clock_wmes):
            if i == 3 and not self.include_ms:
                continue
            wme.set_value(self.clock_info[i])
            wme.add_to_wm(self.clock_id)

    def _update_wm(self):
        if self.include_ms:
            self.milsecs.update_wm()
        self.seconds.update_wm()
        self.steps.update_wm()
        for i, wme in enumerate(self.clock_wmes):
            wme.set_value(self.clock_info[i])
            wme.update_wm()

    def _remove_from_wm(self):
        if self.time_id is None:
            return
        for wme in self.clock_wmes:
            wme.remove_from_wm()
        self.milsecs.remove_from_wm()
        self.seconds.remove_from_wm()
        self.steps.remove_from_wm()
        self.time_id.DestroyWME()
        self.time_id = None
        self.clock_id = None

