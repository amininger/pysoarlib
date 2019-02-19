from __future__ import print_function

import sys
import time
from threading import Thread

import Python_sml_ClientInterface as sml
from .SoarWME import SoarWME

current_time_ms = lambda: int(round(time.time() * 1000))

def parse_agent_kwargs_from_file(config_filename):
    """ Parses a config file and returns a dictionary with the parsed agent settings

    Will throw an error if the file doesn't exist
    Config file is a text file with lines of the form 'setting = value'
    It uses the same setting names as above, but with - intead of _
        e.g. agent-name = Rosie
    """
    # Read config file
    props = {}
    with open(config_filename, 'r') as fin:
        for line in fin:
            args = line.split()
            if len(args) == 3 and args[1] == '=':
                props[args[0]] = args[2]

    # Set config values
    kwargs = {}
    kwargs["agent_name"] = props.get("agent-name", "soaragent")
    kwargs["agent_source"] = props.get("agent-source", None)
    kwargs["smem_source"] = props.get("smem-source", None)

    kwargs["messages_file"] = props.get("messages-file", None)

    kwargs["verbose"] = props.get("verbose", "false").lower() == "true"
    kwargs["watch_level"] = int(props.get("watch-level", "1"))
    kwargs["spawn_debugger"] = props.get("spawn-debugger", "false").lower() == "true"
    kwargs["write_to_stdout"] = props.get("write-to-stdout", "false").lower() == "true"
    kwargs["enable_log"] = props.get("enable-log", "false").lower() == "true"

    return kwargs

class SoarAgent:
    """ A wrapper class for creating and using a soar SML Agent """
    def __init__(self, print_handler=None, config_filename=None, **kwargs):
        """ Will create a soar kernel and agent

        print_handler determines how output is printed, defaults to python print
        config_filename if specified will read config info (kwargs) from a file
            Config file is a text file with lines of the form 'setting = value'
            It uses the same setting names as above, but with - intead of _
                e.g. agent-name = Rosie

        ============== kwargs =============

        agent_name = [string] (default=soaragent)
            Name to give the SML Agent when it is created

        agent_source = [filename] (default=None)
            Soar file to source when the agent is created

        smem_source = [filename] (default=None)
            Soar file with smem add commands to source the agent is created

        verbose = true|false (default=false)
            If true, prints additional information when sourcing files

        watch_level = [int] (default=1)
            The watch level to use (controls amount of info printed, 0=none, 5=all)

        spawn_debugger = true|false (default=false)
            If true, will spawn the java soar debugger

        write_to_stdout = true|false (default=false)
            If true, will print all soar output to the given print_handler (default is python print)

        enable_log = true|false
            If true, will write all soar output to a file called agent-log.txt
        
        Note: Still need to call connect() to register event handlers
        """
        if config_filename:
            # Add settings from config file if not overridden in kwargs
            config_kwargs = parse_agent_kwargs_from_file(config_filename)
            for key, value in config_kwargs.items():
                if key not in kwargs:
                    kwargs[key] = value

        self.agent_name = kwargs.get("agent_name", "soaragent")
        self.agent_source = kwargs.get("agent_source", None)
        self.smem_source = kwargs.get("smem_source", None)

        self.verbose = kwargs.get("verbose", False)
        self.watch_level = kwargs.get("watch_level", 1)
        self.spawn_debugger = kwargs.get("spawn_debugger", False)
        self.write_to_stdout = kwargs.get("write_to_stdout", False)
        self.enable_log = kwargs.get("enable_log", False)

        self.messages_file = kwargs.get("messages_file", None)

        self.connected = False
        self.is_running = False
        self.queue_stop = False

        self.print_handler = print_handler
        if print_handler == None:
            self.print_handler = print

        self.kernel = sml.Kernel.CreateKernelInNewThread()
        self.kernel.SetAutoCommit(False)

        self.start_time = current_time_ms()
        self.time_id = None

        self.time_info = [8, 0, 0, 0, 0, 0] # [ hour, min, sec, tot-sec, real-world-sec, # steps (dc's)]
        self.time_wmes = [ SoarWME("clock-hour", 8), SoarWME("clock-min", 0), SoarWME("clock-sec", 0), SoarWME("total-secs", 0), SoarWME("seconds", 0), SoarWME("steps", 0) ]

        if self.enable_log:
            self.log_writer = open("agent-log.txt", 'w')

        self.run_event_callback_id = -1
        self.print_event_callback_id = -1
        self.init_agent_callback_id = -1
        self.connectors = {}

        self.__create_soar_agent()

    def add_connector(self, name, connector):
        """ Adds an AgentConnector to the agent """
        self.connectors[name] = connector

    def start(self):
        """ Will start the agent (uses another thread, so non-blocking) """
        if self.is_running:
            return

        self.is_running = True
        thread = Thread(target = SoarAgent.__run_thread, args = (self, ))
        thread.start()

    def stop(self):
        """ Tell the running thread to stop
        
        Note: Non-blocking, agent may run for a bit after this call finishes"""
        self.queue_stop = True

    def execute_command(self, cmd):
        """ Execute a soar command, write output to print_handler """
        self.print_handler(cmd)
        self.print_handler(self.agent.ExecuteCommandLine(cmd)  + "\n")

    def connect(self):
        """ Register event handlers for agent and connectors """
        if self.connected:
            return

        self.run_event_callback_id = self.agent.RegisterForRunEvent(
            sml.smlEVENT_BEFORE_INPUT_PHASE, SoarAgent.__run_event_handler, self)

        if self.enable_log or self.write_to_stdout:
            self.print_event_callback_id = self.agent.RegisterForPrintEvent(
                    sml.smlEVENT_PRINT, SoarAgent.__print_event_handler, self)

        self.init_agent_callback_id = self.kernel.RegisterForAgentEvent(
                sml.smlEVENT_BEFORE_AGENT_REINITIALIZED, SoarAgent.__init_agent_handler, self)

        for connector in self.connectors.values():
            connector.connect()

        self.connected = True

    def disconnect(self):
        """ Unregister event handlers for agent and connectors """
        if not self.connected:
            return

        if self.run_event_callback_id != -1:
            self.agent.UnregisterForRunEvent(self.run_event_callback_id)
            self.run_event_callback_id = -1

        if self.print_event_callback_id != -1:
            self.agent.UnregisterForPrintEvent(self.print_event_callback_id)
            self.print_event_callback_id = -1

        if self.init_agent_callback_id != -1:
            self.kernel.UnregisterForAgentEvent(self.init_agent_callback_id)
            self.init_agent_callback_id = -1

        for connector in self.connectors.values():
            connector.disconnect()

        self.connected = False

    def reset(self):
        """ Will destroy the current agent and create + source a new one """
        self.__destroy_soar_agent()
        self.__create_soar_agent()
        self.connect()

    def kill(self):
        """ Will destroy the current agent + kernel, cleans up everything """
        self.__destroy_soar_agent()
        self.kernel.Shutdown()


#### Internal Methods

    def __run_thread(self):
        self.agent.ExecuteCommandLine("run")
        self.is_running = False

    def __create_soar_agent(self):
        self.agent = self.kernel.CreateAgent(self.agent_name)
        if self.spawn_debugger:
            success = self.agent.SpawnDebugger(self.kernel.GetListenerPort())

        self.__source_agent()
        self.agent.ExecuteCommandLine("w " + str(self.watch_level))

    def __source_agent(self):
        self.agent.ExecuteCommandLine("smem --set database memory")
        self.agent.ExecuteCommandLine("epmem --set database memory")

        if self.smem_source != None:
            self.print_handler("------------- SOURCING SMEM ---------------")
            result = self.agent.ExecuteCommandLine("source " + self.smem_source)
            if self.verbose:
                self.print_handler(result)

        if self.agent_source != None:
            self.print_handler("--------- SOURCING PRODUCTIONS ------------")
            result = self.agent.ExecuteCommandLine("source " + self.agent_source)
            if self.verbose:
                self.print_handler(result)
        else:
            self.print_handler("agent_source not specified, no rules are being sourced")

    def __on_init_soar(self):
        for connector in self.connectors.values():
            connector.on_init_soar()
        self.start_time = current_time_ms()
        self.time_info = [8, 0, 0, 0, 0, 0]
        for wme in self.time_wmes:
            wme.remove_from_wm()
        if self.time_id:
            self.time_id.DestroyWME()
            self.time_id = None

    def __destroy_soar_agent(self):
        self.stop()
        while self.is_running:
            time.sleep(0.01)
        self.__on_init_soar()
        self.disconnect()
        if self.spawn_debugger:
            self.agent.KillDebugger()
        self.kernel.DestroyAgent(self.agent)
        self.agent = None

    @staticmethod
    def __init_agent_handler(eventID, self, info):
        try:
            self.__on_init_soar()
        except:
            self.print_handler("ERROR IN INIT AGENT")

    @staticmethod
    def __run_event_handler(eventID, self, agent, phase):
        if eventID == sml.smlEVENT_BEFORE_INPUT_PHASE:
            self.__on_input_phase()


    def __on_input_phase(self):
       try:
            if self.queue_stop:
                self.agent.StopSelf()
                self.queue_stop = False

            # Update time information
            self.time_info[2] += 5
            if self.time_info[2] >= 60:
                self.time_info[2] -= 60
                self.time_info[1] += 1
                if self.time_info[1] >= 60:
                    self.time_info[1] -= 60
                    self.time_info[0] += 1
                    if self.time_info[0] >= 24:
                        self.time_info[0] -= 24
            self.time_info[3] += 5
            self.time_info[4] = int((current_time_ms() - self.start_time)/1000)
            self.time_info[5] += 1

            for i, val in enumerate(self.time_info):
                self.time_wmes[i].set_value(val)

            # Update time wmes
            if self.time_id == None:
                self.time_id = self.agent.GetInputLink().CreateIdWME("time")
                for wme in self.time_wmes:
                    wme.add_to_wm(self.time_id)
            else:
                for wme in self.time_wmes:
                    wme.update_wm()


            for connector in self.connectors.values():
                connector.on_input_phase(self.agent.GetInputLink())

            if self.agent.IsCommitRequired():
                self.agent.Commit()
       except:
           e = sys.exc_info()
           self.print_handler("ERROR IN RUN HANDLER")
           self.print_handler(str(e[0]))
           self.print_handler(str(e[1]))
           self.print_handler(str(e[2]))


    @staticmethod
    def __print_event_handler(eventID, self, agent, message):
        try:
            if self.write_to_stdout:
                self.print_handler(message)
            if self.enable_log:
                self.log_writer.write(message)
        except:
            self.print_handler("ERROR IN PRINT HANDLER")


