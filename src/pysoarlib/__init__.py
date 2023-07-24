""" Helper classes and functions for creating a soar agent and working with SML

Depends on the Python_sml_ClientInterface, so make sure that SOAR_HOME is on the PYTHONPATH

SoarClient and AgentConnector are used to create an agent
WMInterface is a standardized interface for adding/removing structures from working memory
SoarWME is a wrapper for creating working memory elements
SVSCommands will generate svs command strings for some common use cases

Also adds helper methods to the Identifier class to access children more easily
(See IdentifierExtensions)

"""
import Python_sml_ClientInterface as sml

__all__ = ["WMInterface", "SoarWME", "SVSCommands", "AgentConnector", "SoarClient", "TimeConnector"]

# Extend the sml Identifier class definition with additional utility methods
from .IdentifierExtensions import *
sml.Identifier.GetChildString = get_child_str
sml.Identifier.GetChildInt = get_child_int
sml.Identifier.GetChildFloat = get_child_float
sml.Identifier.GetChildId = get_child_id
sml.Identifier.GetAllChildIds = get_all_child_ids
sml.Identifier.GetAllChildValues = get_all_child_values
sml.Identifier.GetAllChildWmes = get_all_child_wmes
sml.Identifier.__lt__ = lambda self, other: self.GetIdentifierSymbol() < other.GetIdentifierSymbol()

from .WMInterface import WMInterface
from .SoarWME import SoarWME
from .SVSCommands import SVSCommands
from .AgentConnector import AgentConnector
from .SoarClient import SoarClient
from .TimeConnector import TimeConnector


