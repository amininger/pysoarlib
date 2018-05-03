from pysoarlib import *

from SimpleAgent import SimpleAgent

agent = SimpleAgent(AgentConfig.create_from_file("agent.config"))
agent.connect()

for i in range(10):
    agent.execute_command("step")

agent.kill()
