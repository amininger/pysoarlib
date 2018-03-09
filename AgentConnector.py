from __future__ import print_function

class AgentConnector(object):
    def __init__(self, agent, print_handler=None):
        self.agent = agent
        self.connected = False
        self.output_handler_ids = { }

        self.print_handler = print_handler
        if print_handler == None:
            self.print_handler = lambda message: print(message)

    def register_output_handler(self, command_name):
        self.output_handler_ids[command_name] = -1

    def connect(self):
        if self.connected:
            return

        for command_name in self.output_handler_ids:
            self.output_handler_ids[command_name] = self.agent.agent.AddOutputHandler(
                    command_name, AgentConnector.output_event_handler, self)

        self.connected = True

    def disconnect(self):
        if not self.connected:
            return

        for command_name in self.output_handler_ids:
            self.agent.agent.RemoveOutputHandler(self.output_handler_ids[command_name])
            self.output_handler_ids[command_name] = -1

        self.connected = False

    def on_init_soar(self):
        pass

    def on_input_phase(self, input_link):
        pass

    def on_output_event(self, att_name, root_id):
        pass

    @staticmethod
    def output_event_handler(self, agent_name, att_name, wme):
        try:
            if wme.IsJustAdded() and wme.IsIdentifier():
                root_id = wme.ConvertToIdentifier()
                self.on_output_event(att_name, root_id)
        except:
            self.print_handler("ERROR IN OUTPUT EVENT HANDLER")
            self.print_handler(sys.exec_info())

        self.connected = True
