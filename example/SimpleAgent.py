import sys
import Python_sml_ClientInterface as sml

from pysoarlib import SoarAgent, LanguageConnector
from SimpleConnector import SimpleConnector

class SimpleAgent(SoarAgent):
    def __init__(self, agent_config):
        SoarAgent.__init__(self, agent_config)

        self.connectors["simple"] = SimpleConnector(self)
        self.connectors["language"] = LanguageConnector(self)
        self.connectors["language"].send_message("Hello World")

