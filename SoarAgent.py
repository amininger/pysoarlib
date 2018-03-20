from __future__ import print_function
import sys

from threading import Thread
import time

import Python_sml_ClientInterface as sml

from SoarWME import SoarWME

current_time_ms = lambda: int(round(time.time() * 1000))

class AgentConfig:
    def __init__(self, config_file):
        # Read config file
        self.props = {}
        try:
            with open(config_file, 'r') as fin:
                for line in fin:
                    args = line.split()
                    if len(args) == 3 and args[1] == '=':
                        self.props[args[0]] = args[2]
        except EnvironmentError:
            pass

        # Set config values
        self.agent_name = self.props.get("agent-name", "rosie")
        self.agent_source = self.props.get("agent-source", None)
        self.smem_source = self.props.get("smem-source", None)

        self.messages_file = self.props.get("messages-file", None)

        self.verbose = self.props.get("verbose", "false") == "true"
        self.watch_level = int(self.props.get("watch-level", "1"))
        self.spawn_debugger = self.props.get("spawn-debugger", "false") == "true"
        self.write_to_stdout = self.props.get("write-to-stdout", "false") == "true"
        self.write_log = self.props.get("enable-log", "false") == "true"

class SoarAgent:
    def __init__(self, config_file, print_handler=None):
        self.config = AgentConfig(config_file)

        self.connected = False
        self.is_running = False
        self.queue_stop = False

        self.print_handler = print_handler
        if print_handler == None:
            self.print_handler = lambda message: print(message)

        self.kernel = sml.Kernel.CreateKernelInNewThread()
        self.kernel.SetAutoCommit(False)

        self.start_time = current_time_ms()
        self.time_id = None
        self.seconds = SoarWME("seconds", 0)
        self.steps = SoarWME("steps", 0)

        if self.config.write_log:
            self.log_writer = open("rosie-log.txt", 'w')

        self.run_event_callback_ids = []
        self.print_event_callback_id = -1
        self.init_agent_callback_id = -1
        self.connectors = {}

        self.create_soar_agent()

    def start(self):
        if self.is_running:
            return

        self.is_running = True
        thread = Thread(target = SoarAgent.run_thread, args = (self, ))
        thread.start()

    def stop(self):
        self.queue_stop = True

    def execute_command(self, cmd):
        self.print_handler(cmd)
        self.print_handler(self.agent.ExecuteCommandLine(cmd)  + "\n")

    def connect(self):
        if self.connected:
            return

        self.run_event_callback_ids.append(self.agent.RegisterForRunEvent(
            sml.smlEVENT_BEFORE_INPUT_PHASE, SoarAgent.run_event_handler, self))
        self.run_event_callback_ids.append(self.agent.RegisterForRunEvent(
            sml.smlEVENT_AFTER_INPUT_PHASE, SoarAgent.run_event_handler, self))
        self.run_event_callback_ids.append(self.agent.RegisterForRunEvent(
            sml.smlEVENT_AFTER_OUTPUT_PHASE, SoarAgent.run_event_handler, self))

        self.print_event_callback_id = self.agent.RegisterForPrintEvent(
                sml.smlEVENT_PRINT, SoarAgent.print_event_handler, self)

        self.init_agent_callback_id = self.kernel.RegisterForAgentEvent(
                sml.smlEVENT_BEFORE_AGENT_REINITIALIZED, SoarAgent.init_agent_handler, self)

        for connector in self.connectors.values():
            connector.connect()

        self.connected = True

    def disconnect(self):
        if not self.connected:
            return

        for callback_id in self.run_event_callback_ids:
            self.agent.UnregisterForRunEvent(callback_id)
        self.run_event_callback_ids = []

        if self.print_event_callback_id != -1:
            self.agent.UnregisterForPrintEvent(self.print_event_callback_id)
            self.print_event_callback_id = -1

        self.kernel.UnregisterForAgentEvent(self.init_agent_callback_id)
        self.init_agent_callback_id = -1

        for connector in self.connectors.values():
            connector.disconnect()

        self.connected = False

    def reset(self):
        self.destroy_soar_agent()
        self.create_soar_agent()
        self.connect()

    def kill(self):
        self.destroy_soar_agent()
        self.kernel.Shutdown()


#### Internal Methods

    def run_thread(self):
        self.agent.ExecuteCommandLine("run")
        self.is_running = False

    def create_soar_agent(self):
        self.agent = self.kernel.CreateAgent(self.config.agent_name)
        if self.config.spawn_debugger:
            success = self.agent.SpawnDebugger(self.kernel.GetListenerPort())

        self.source_agent()
        self.agent.ExecuteCommandLine("w " + str(self.config.watch_level))

    def source_agent(self):
        self.agent.ExecuteCommandLine("smem --set database memory")
        self.agent.ExecuteCommandLine("epmem --set database memory")

        if self.config.smem_source != None:
            self.print_handler("------------- SOURCING SMEM ---------------")
            result = self.agent.ExecuteCommandLine("source " + self.config.smem_source)
            if self.config.verbose:
                self.print_handler(result)

        if self.config.agent_source != None:
            self.print_handler("--------- SOURCING PRODUCTIONS ------------")
            result = self.agent.ExecuteCommandLine("source " + self.config.agent_source)
            if self.config.verbose:
                self.print_handler(result)
        else:
            self.print_handler("WARNING! agent-source not set in config file, not sourcing any rules")


    def on_init_soar(self):
        for connector in self.connectors.values():
            connector.on_init_soar()
        self.seconds.remove_from_wm()
        self.steps.remove_from_wm()
        if self.time_id:
            self.time_id.DestroyWME()
            self.time_id = None

    def destroy_soar_agent(self):
        self.stop()
        while self.is_running:
            time.sleep(0.01)
        self.on_init_soar()
        self.disconnect()
        if self.config.spawn_debugger:
            self.agent.KillDebugger()
        self.kernel.DestroyAgent(self.agent)
        self.agent = None

    @staticmethod
    def init_agent_handler(eventID, self, info):
        try:
            self.on_init_soar()
        except:
            self.print_handler("ERROR IN INIT AGENT")

    @staticmethod
    def run_event_handler(eventID, self, agent, phase):
       try:
            if eventID == sml.smlEVENT_BEFORE_INPUT_PHASE:
                if self.queue_stop:
                    agent.StopSelf()
                    self.queue_stop = False

                # Timing Info
                if self.time_id == None:
                    self.start_time = current_time_ms()
                    self.time_id = self.agent.GetInputLink().CreateIdWME("time")
                    self.seconds.set_value(0)
                    self.seconds.add_to_wm(self.time_id)
                    self.steps.set_value(0)
                    self.steps.add_to_wm(self.time_id)
                else:
                    self.seconds.set_value(int((current_time_ms() - self.start_time)/1000))
                    self.seconds.update_wm()
                    self.steps.set_value(self.steps.val + 1)
                    self.steps.update_wm()

                for connector in self.connectors.values():
                    connector.on_input_phase(self.agent.GetInputLink())

            elif eventID == sml.smlEVENT_AFTER_INPUT_PHASE or \
                    eventID == sml.smlEVENT_AFTER_OUTPUT_PHASE:
                if agent.IsCommitRequired():
                    agent.Commit()
       except:
           e = sys.exc_info()
           self.print_handler("ERROR IN RUN HANDLER")
           self.print_handler(str(e[0]))
           self.print_handler(str(e[1]))
           self.print_handler(str(e[2]))

    @staticmethod
    def print_event_handler(eventID, self, agent, message):
        try:
            self.print_handler(message)
            if self.config.write_log:
                self.log_writer.write(message)
        except:
            self.print_handler("ERROR IN PRINT HANDLER")


