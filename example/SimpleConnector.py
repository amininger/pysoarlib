import sys

from string import digits
from pysoarlib import *

class SimpleConnector(AgentConnector):
    def __init__(self, agent):
        AgentConnector.__init__(self, agent)
        self.add_output_command("increment")
        self.num = SoarWME("number", 1)

    def on_input_phase(self, input_link):
        if not self.num.is_added():
            self.num.add_to_wm(input_link)
        else:
            self.num.update_wm()

    def on_init_soar(self):
        svs_commands = []
        self.num.remove_from_wm()

    def on_output_event(self, command_name, root_id):
        if command_name == "increment":
            self.process_increment_command(root_id)
    
    def process_increment_command(self, root_id):
        number = root_id.GetChildInt("number")
        if number == None:
            self.print_handler("!!! No number provided on increment command !!!")
            root_id.CreateStringWME("status", "error")
        else:
            self.num.set_value(self.num.val + number)
            root_id.CreateStringWME("status", "success")
