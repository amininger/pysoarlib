""" Generic Base Class for interfacing with a soar agent's input/output links

A Connector can be added to a SoarAgent and can handle input/output 
    while taking care of specific SML calls and event registering
"""

from __future__ import print_function
 
import traceback, sys

class AgentConnector(object):
    """ Base Class for handling input/output for a soar agent

    Input:
        on_input_phase will be automatically called before each input phase

    Output:
        call add_output_command to add the name of an output-link command to look for
        on_output_event will then be called if such a command is added by the agent

    Look at LanguageConnector for an example of an AgentConnector used in practice
    """
    def __init__(self, agent, print_handler=None):
        """ Initialize the Connector (but won't register event handlers until connect)

        agent should be an instance of SoarAgent
        print_handler defaults to python print, but can be customized
        """
        self.agent = agent
        self.connected = False
        self.output_handler_ids = { }

        self.print_handler = print_handler
        if print_handler == None:
            self.print_handler = print

    def add_output_command(self, command_name):
        """ Will cause the connector to handle commands with the given name on the output-link """
        if self.connected:
            self.output_handler_ids[command_name] = self.agent.agent.AddOutputHandler(
                    command_name, AgentConnector._output_event_handler, self)
        else:
            self.output_handler_ids[command_name] = -1

    def connect(self):
        """ Adds event handlers, automatically called by the SoarAgent """
        if self.connected:
            return

        for command_name in self.output_handler_ids:
            self.output_handler_ids[command_name] = self.agent.agent.AddOutputHandler(
                    command_name, AgentConnector._output_event_handler, self)

        self.connected = True

    def disconnect(self):
        """ Removes event handlers, automatically called by the SoarAgent """
        if not self.connected:
            return

        for command_name in self.output_handler_ids:
            self.agent.agent.RemoveOutputHandler(self.output_handler_ids[command_name])
            self.output_handler_ids[command_name] = -1

        self.connected = False

    def on_init_soar(self):
        """ Override to handle an init-soar event (remove references to SML objects """
        pass

    def on_input_phase(self, input_link):
        """ Override to update working memory, automatically called before each input phase """
        pass

    def on_output_event(self, command_name, root_id):
        """ Override to handle output commands with the given name (added by add_output_command) 

        root_id is the root Identifier of the command (e.g. (<output-link> ^command_name <root_id>)
        """
        pass

    @staticmethod
    def _output_event_handler(self, agent_name, att_name, wme):
        """ OutputHandler callback for when a command is put on the output link """
        try:
            if wme.IsJustAdded() and wme.IsIdentifier():
                root_id = wme.ConvertToIdentifier()
                self.on_output_event(att_name, root_id)
        except:
            self.print_handler("ERROR IN OUTPUT EVENT HANDLER")
            self.print_handler(traceback.format_exc())
            self.print_handler("--------- END ---------------")
