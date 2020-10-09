from __future__ import print_function

from threading import Thread
import traceback
from time import sleep

import Python_sml_ClientInterface as sml
from .SoarWME import SoarWME

class SoarAgent():
    """ A wrapper class for creating and using a soar SML Agent """
    def __init__(self, print_handler=None, config_filename=None, **kwargs):
        """ Will create a soar kernel and agent

        print_handler determines how output is printed, defaults to python print
        config_filename if specified will read config info (kwargs) from a file
            Config file is a text file with lines of the form 'setting = value'

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

        start_running = true|false (default=false)
            If true, will immediately start the agent running

        spawn_debugger = true|false (default=false)
            If true, will spawn the java soar debugger

        write_to_stdout = true|false (default=false)
            If true, will print all soar output to the given print_handler (default is python print)

        enable_log = true|false
            If true, will write all soar output to a file given by log_filename

        log_filename = [filename] (default = agent-log.txt)
            Specify the name of the log file to write

        remote_connection = true|false (default=false)
            If true, will connect to a remote kernel instead of creating a new one
        
        Note: Still need to call connect() to register event handlers
        """

        self.print_handler = print_handler
        if print_handler == None:
            self.print_handler = print

        # Gather settings, filling in defaults as needed
        self.kwarg_keys = set(kwargs.keys())
        self.settings = kwargs
        self.config_filename = config_filename
        self._read_config_file()
        self._apply_settings()

        self.connected = False
        self.is_running = False
        self.queue_stop = False

        self.run_event_callback_id = -1
        self.print_event_callback_id = -1
        self.init_agent_callback_id = -1
        self.connectors = {}
        self.print_event_handlers = []

        if self.remote_connection:
            self.kernel = sml.Kernel.CreateRemoteConnection()
        else:
            self.kernel = sml.Kernel.CreateKernelInNewThread()
            self.kernel.SetAutoCommit(False)

        self._create_soar_agent()

    def add_connector(self, name, connector):
        """ Adds an AgentConnector to the agent """
        self.connectors[name] = connector

    def get_connector(self, name):
        """ Returns the AgentConnector with the given name, or None """
        return self.connectors.get(name, None)

    def add_print_event_handler(self, handler):
        """ calls the given handler during each soar print event, 
            where handler is a method taking a single string argument """
        self.print_event_handlers.append(handler)

    def start(self):
        """ Will start the agent (uses another thread, so non-blocking) """
        if self.is_running:
            return

        self.is_running = True
        thread = Thread(target = SoarAgent._run_thread, args = (self, ))
        thread.start()

    def stop(self):
        """ Tell the running thread to stop
        
        Note: Non-blocking, agent may run for a bit after this call finishes"""
        self.queue_stop = True

    def execute_command(self, cmd, print_res=False):
        """ Execute a soar command and return result, 
            write output to print_handler if print_res is True """
        result = self.agent.ExecuteCommandLine(cmd).strip()
        if print_res:
            self.print_handler(cmd)
            self.print_handler(result)
        return result

    def connect(self):
        """ Register event handlers for agent and connectors """
        if self.connected:
            return

        self.run_event_callback_id = self.agent.RegisterForRunEvent(
            sml.smlEVENT_BEFORE_INPUT_PHASE, SoarAgent._run_event_handler, self)

        self.print_event_callback_id = self.agent.RegisterForPrintEvent(
                sml.smlEVENT_PRINT, SoarAgent._print_event_handler, self)

        self.init_agent_callback_id = self.kernel.RegisterForAgentEvent(
                sml.smlEVENT_BEFORE_AGENT_REINITIALIZED, SoarAgent._init_agent_handler, self)

        for connector in self.connectors.values():
            connector.connect()

        self.connected = True

        if self.start_running:
            self.start()

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
        self._destroy_soar_agent()
        self._create_soar_agent()
        self.connect()

    def kill(self):
        """ Will destroy the current agent + kernel, cleans up everything """
        self._destroy_soar_agent()
        self.kernel.Shutdown()
        self.kernel = None

#### Internal Methods
    def _read_config_file(self):
        """ Will read the given config file and update self.settings as necessary (wont overwrite kwarg settings)

        config_filename is a text file with lines of the form 'setting = value'"""

        # Add any settings in the config file (if it exists)
        try:
            with open(self.config_filename, 'r') as fin:
                config_args = [ line.split() for line in fin ]

            for args in config_args:
                if len(args) == 3 and args[1] == '=':
                    key = args[0].replace("-", "_")
                    # Add settings from config file if not overridden in kwargs
                    if key not in self.kwarg_keys:
                        self.settings[key] = args[2]
        except IOError:
            pass

    def _apply_settings(self):
        """ Set up the SoarAgent object by copying settings or filling in default values """
        self.agent_name = self.settings.get("agent_name", "soaragent")
        self.agent_source = self.settings.get("agent_source", None)
        self.smem_source = self.settings.get("smem_source", None)

        self.verbose = self._parse_bool_setting("verbose", False)
        self.watch_level = int(self.settings.get("watch_level", 1))
        self.remote_connection = self._parse_bool_setting("remote_connection", False)
        self.spawn_debugger = self._parse_bool_setting("spawn_debugger", False)
        self.start_running = self._parse_bool_setting("start_running", False)
        self.write_to_stdout = self._parse_bool_setting("write_to_stdout", False)
        self.enable_log = self._parse_bool_setting("enable_log", False)
        self.log_filename = self.settings.get("log_filename", "agent-log.txt")

    def _parse_bool_setting(self, name, default):
        if name not in self.settings:
            return default
        val = self.settings[name]
        if type(val) == str:
            return val.lower() == "true"
        return val

    def _run_thread(self):
        self.agent.ExecuteCommandLine("run")
        self.is_running = False

    def _create_soar_agent(self):
        if self.enable_log:
            self.log_writer = open(self.log_filename, 'w')

        if self.remote_connection:
            self.agent = self.kernel.GetAgentByIndex(0)
        else:
            self.agent = self.kernel.CreateAgent(self.agent_name)
            self._source_agent()

        if self.spawn_debugger:
            success = self.agent.SpawnDebugger(self.kernel.GetListenerPort())

        self.agent.ExecuteCommandLine("w " + str(self.watch_level))

    def _source_agent(self):
        self.agent.ExecuteCommandLine("smem --set database memory")
        self.agent.ExecuteCommandLine("epmem --set database memory")

        if self.smem_source != None:
            self.print_handler("------------- SOURCING SMEM ---------------")
            result = self.agent.ExecuteCommandLine("source " + self.smem_source)
            if self.verbose:
                self.print_handler(result)
            else:
                self._summarize_smem_source(result)

        if self.agent_source != None:
            self.print_handler("--------- SOURCING PRODUCTIONS ------------")
            result = self.agent.ExecuteCommandLine("source " + self.agent_source + " -v")
            if self.verbose:
                self.print_handler(result)
            else:
                self._summarize_source(result)
        else:
            self.print_handler("agent_source not specified, no rules are being sourced")

    # Prints a summary of the smem source command instead of every line (verbose = false)
    def _summarize_smem_source(self, printout):
        summary = []
        n_added = 0
        for line in printout.split('\n'):
            if line == "Knowledge added to semantic memory.":
                n_added += 1
            else:
                summary.append(line)
        self.print_handler('\n'.join(summary))
        self.print_handler("Knowledge added to semantic memory. [" + str(n_added) + " times]")

    # Prints a summary of the agent source command instead of every line (verbose = false)
    def _summarize_source(self, printout):
        summary = []
        for line in printout.split('\n'):
            if line.startswith("Sourcing"):
                continue
            if line.startswith("warnings is now"):
                continue
            # Line is only * or # characters
            if all(c in "#* " for c in line):
                continue
            summary.append(line)
        self.print_handler('\n'.join(summary))

    def _on_init_soar(self):
        for connector in self.connectors.values():
            connector.on_init_soar()

    def _destroy_soar_agent(self):
        self.stop()
        while self.is_running:
            sleep(0.01)
        self._on_init_soar()
        self.disconnect()
        if self.spawn_debugger:
            self.agent.KillDebugger()
        if not self.remote_connection:
            self.kernel.DestroyAgent(self.agent)
        self.agent = None
        if self.enable_log:
            self.log_writer.close()
            self.log_writer = None

    @staticmethod
    def _init_agent_handler(eventID, self, info):
        try:
            self._on_init_soar()
        except:
            self.print_handler("ERROR IN INIT AGENT")
            self.print_handler(traceback.format_exc())

    @staticmethod
    def _run_event_handler(eventID, self, agent, phase):
        if eventID == sml.smlEVENT_BEFORE_INPUT_PHASE:
            self._on_input_phase(agent.GetInputLink())

    def _on_input_phase(self, input_link):
        try:
            if self.queue_stop:
                self.agent.StopSelf()
                self.queue_stop = False


            for connector in self.connectors.values():
                connector.on_input_phase(input_link)

            if self.agent.IsCommitRequired():
                self.agent.Commit()
        except:
            self.print_handler("ERROR IN RUN HANDLER")
            self.print_handler(traceback.format_exc())


    @staticmethod
    def _print_event_handler(eventID, self, agent, message):
        try:
            if self.write_to_stdout:
                message = message.strip()
                self.print_handler(message)
            if self.enable_log:
                self.log_writer.write(message)
                self.log_writer.flush()
            for ph in self.print_event_handlers:
                ph(message)
        except:
            self.print_handler("ERROR IN PRINT HANDLER")
            self.print_handler(traceback.format_exc())


