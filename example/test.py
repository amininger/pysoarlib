from pysoarlib import *
from SimpleConnector import SimpleConnector


agent = SoarAgent(config_filename="agent.config")
agent.add_connector("simple", SimpleConnector(agent))
agent.connect()

for i in range(10):
    agent.execute_command("step")

agent.kill()
