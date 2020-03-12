from pysoarlib import *

class SimpleConnector(AgentConnector):
    def __init__(self, agent):
        AgentConnector.__init__(self, agent)
        self.add_output_command("increase-number")
        self.num = SoarWME("number", 0)

    def on_input_phase(self, input_link):
        if not self.num.is_added():
            self.num.add_to_wm(input_link)
        else:
            self.num.update_wm()

    def on_init_soar(self):
        self.num.remove_from_wm()

    def on_output_event(self, command_name, root_id):
        if command_name == "increase-number":
            self.process_increase_command(root_id)
    
    def process_increase_command(self, root_id):
        number = root_id.GetChildInt("number")
        if number:
            self.num.set_value(self.num.val + number)
        root_id.AddStatusComplete()

agent = SoarAgent(agent_source="test-agent.soar", write_to_stdout=True)
agent.add_connector("simple", SimpleConnector(agent))
agent.connect()

agent.execute_command("run 12")

agent.kill()
