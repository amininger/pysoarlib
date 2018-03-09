import Python_sml_ClientInterface as sml

__all__ = ["SoarWME", "SVSCommands", "AgentConnector", "LanguageConnector", "SoarAgent"]

# Extend the sml Identifier class definition with additional utility methods
from IdentifierExtensions import *
sml.Identifier.GetChildString = get_child_str
sml.Identifier.GetChildInt = get_child_int
sml.Identifier.GetChildFloat = get_child_float
sml.Identifier.GetChildId = get_child_id
sml.Identifier.GetAllChildIds = get_all_child_ids
sml.Identifier.GetAllChildValues = get_all_child_values

from SoarWME import SoarWME
from SVSCommands import SVSCommands
from AgentConnector import AgentConnector
from LanguageConnector import LanguageConnector
from SoarAgent import SoarAgent

