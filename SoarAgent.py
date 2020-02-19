from __future__ import print_function

from threading import Thread
import traceback
from time import sleep

import subprocess

import Python_sml_ClientInterface as sml
from .SoarWME import SoarWME
from .TimeInfo import TimeInfo

def parse_agent_settings_from_file(config_filename):
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
                props[args[0].replace("-", "_")] = args[2]

    # Set config values
    settings = {}
    settings["source_config"] = props.get("source_config", None)
    settings["agent_name"] = props.get("agent_name", "soaragent")
    settings["agent_source"] = props.get("agent_source", None)
    settings["smem_source"] = props.get("smem_source", None)

    settings["messages_file"] = props.get("messages_file", None)

    settings["verbose"] = props.get("verbose", "false").lower() == "true"
    settings["watch_level"] = int(props.get("watch_level", "1"))
    settings["spawn_debugger"] = props.get("spawn_debugger", "false").lower() == "true"
    settings["write_to_stdout"] = props.get("write_to_stdout", "false").lower() == "true"
    settings["enable_log"] = props.get("enable_log", "false").lower() == "true"
    settings["log_filename"] = props.get("log_filename", "agent-log.txt")
    settings["reconfig_on_launch"] = props.get("reconfig_on_launch", "false").lower() == "true"

    for prop in props:
        if prop not in settings:
            settings[prop] = props[prop]

    return settings

class SoarAgent():
    """ A wrapper class for creating and using a soar SML Agent """
    def __init__(self, print_handler=None, config_filename=None, **kwargs):
        """ Will create a soar kernel and agent

        print_handler determines how output is printed, defaults to python print
        config_filename if specified will read config info (kwargs) from a file
            Config file is a text file with lines of the form 'setting = value'
            It uses the same setting names as above, but with - intead of _
                e.g. agent-name = Rosie

        ============== kwargs =============

        source_config = [string]
            The file used to configure this agent (Rosie-specific configuration)

        reconfig_on_launch = true|false (default=false)
            If true, the agent will use the Rosie java configuration tool to re-generate the agent before continuing

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

        log_filename = [filename]
            Specify the name of the log file to write
        
        Note: Still need to call connect() to register event handlers
        """

        self.print_handler = print_handler
        if print_handler == None:
            self.print_handler = print

        self.config_filename = config_filename

        self.settings = kwargs
        self.overridden_settings = kwargs.keys()
        self._parse_config_file()

        self.agent_name = kwargs.get("agent_name", "soaragent")
        self.agent_source = kwargs.get("agent_source", None)
        self.smem_source = kwargs.get("smem_source", None)

        self.verbose = kwargs.get("verbose", False)
        self.watch_level = kwargs.get("watch_level", 1)
        self.spawn_debugger = kwargs.get("spawn_debugger", False)
        self.write_to_stdout = kwargs.get("write_to_stdout", False)
        self.enable_log = kwargs.get("enable_log", False)
        self.log_filename = kwargs.get("log_filename", "agent-log.txt")

        self.messages_file = kwargs.get("messages_file", None)

        self.connected = False
        self.is_running = False
        self.queue_stop = False
        self.dc_sleep = 0.0

        self.kernel = sml.Kernel.CreateKernelInNewThread()
        self.kernel.SetAutoCommit(False)

        if self.enable_log:
            self.log_writer = open(self.log_filename, 'w')

        self.run_event_callback_id = -1
        self.print_event_callback_id = -1
        self.init_agent_callback_id = -1
        self.connectors = {}

        self.time_info = TimeInfo()

        self._create_soar_agent()

    def add_connector(self, name, connector):
        """ Adds an AgentConnector to the agent """
        self.connectors[name] = connector

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

    def execute_command(self, cmd):
        """ Execute a soar command, write output to print_handler """
        self.print_handler(cmd)
        self.print_handler(self.agent.ExecuteCommandLine(cmd).strip())

    def get_command_result(self, cmd):
        """ Execute a soar command, then result the result as a string """
        return self.agent.ExecuteCommandLine(cmd)

    def connect(self):
        """ Register event handlers for agent and connectors """
        if self.connected:
            return

        self.run_event_callback_id = self.agent.RegisterForRunEvent(
            sml.smlEVENT_BEFORE_INPUT_PHASE, SoarAgent._run_event_handler, self)

        if self.enable_log or self.write_to_stdout:
            self.print_event_callback_id = self.agent.RegisterForPrintEvent(
                    sml.smlEVENT_PRINT, SoarAgent._print_event_handler, self)

        self.init_agent_callback_id = self.kernel.RegisterForAgentEvent(
                sml.smlEVENT_BEFORE_AGENT_REINITIALIZED, SoarAgent._init_agent_handler, self)

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
        self._destroy_soar_agent()
        self._create_soar_agent()
        self.connect()

    def kill(self):
        """ Will destroy the current agent + kernel, cleans up everything """
        self._destroy_soar_agent()
        self.kernel.Shutdown()


#### Internal Methods

    def _parse_config_file(self):
        """ Parses the rosie config file and adds everything in self.settings unless in the overriden list """
        if self.config_filename is not None:
            # Add settings from config file if not overridden in kwargs
            config_settings = parse_agent_settings_from_file(self.config_filename)
            for key, value in config_settings.items():
                if key not in self.overridden_settings:
                    self.settings[key] = value


    def _run_thread(self):
        self.agent.ExecuteCommandLine("run")
        self.is_running = False

    def _create_soar_agent(self):
        if self.settings['source_config'] is not None and self.settings["reconfig_on_launch"]:
            # Rerun the configuration tool and re-source the config file
            self.print_handler("RUNNING CONFIGURATOR: " + self.settings['source_config'])
            subprocess.check_output(['java', 'edu.umich.rosie.tools.config.RosieAgentConfigurator', self.settings['source_config']])
            self._parse_config_file()

        self.agent = self.kernel.CreateAgent(self.agent_name)
        if self.spawn_debugger:
            success = self.agent.SpawnDebugger(self.kernel.GetListenerPort())

        self._source_agent()
        self.agent.ExecuteCommandLine("w " + str(self.watch_level))

    def _source_agent(self):
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

    def _on_init_soar(self):
        for connector in self.connectors.values():
            connector.on_init_soar()

        self.time_info.remove_from_wm()
        self.time_info.reset_time()

    def _destroy_soar_agent(self):
        self.stop()
        while self.is_running:
            sleep(0.01)
        self._on_init_soar()
        self.disconnect()
        if self.spawn_debugger:
            self.agent.KillDebugger()
        self.kernel.DestroyAgent(self.agent)
        self.agent = None

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
        if self.dc_sleep > 0:
            sleep(self.dc_sleep)
        try:
            if self.queue_stop:
                self.agent.StopSelf()
                self.queue_stop = False

            self.time_info.tick(5)
            self.time_info.update_wm(input_link)

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
        except:
            self.print_handler("ERROR IN PRINT HANDLER")
            self.print_handler(traceback.format_exc())


