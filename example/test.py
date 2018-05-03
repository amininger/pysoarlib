from pysoarlib import *
from SimpleConnector import SimpleConnector


agent = SoarAgent(AgentConfig.create_from_file("agent.config"))
agent.add_connector("simple", SimpleConnector(agent))
agent.connect()

for i in range(10):
    agent.execute_command("step")

agent.kill()
