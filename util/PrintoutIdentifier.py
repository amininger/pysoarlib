from pysoarlib.util import parse_wm_printout

class PrintoutIdentifier:
    """ Represents an identifier that was parsed from a soar print command via parse_wm_printout
        and implements the IdentifierExtensions interface for it """

    def create(agent, id, depth):
        """ Will print the given identifier to the given depth and wrap the result in a PrintoutIdentifier """
        printout = agent.execute_command("p " + id + " -d " + str(depth))
        if printout.strip().startswith("There is no identifier"):
            return None
        wmes = parse_wm_printout(printout)
        return PrintoutIdentifier(wmes, id) 

    def __init__(self, wmes, root_id):
        """ wmes is the result of a parse_wm_printout command,
            root_id is the str id for this identifier """
        self.wmes = wmes
        self.root_id = root_id

    def __lt__(self, other):
        return self.root_id < other.root_id

    def GetIdentifierSymbol(self):
        return self.root_id

    def GetChildString(self, attr):
        return self._get_value(attr)

    def GetChildInt(self, attr):
        val = self._get_value(attr)
        try:
            return int(val)
        except ValueError:
            return None

    def GetChildFloat(self, attr):
        val = self._get_value(attr)
        try:
            return float(val)
        except ValueError:
            return None

    def GetChildId(self, attr):
        child_id = self._get_value(attr)
        if child_id is not None:
            return PrintoutIdentifier(self.wmes, child_id)
        return None

    def GetAllChildIds(self, attr=None):
        # Get all children whose values are also identifiers in the wmes dict
        child_wmes = [ wme for wme in self.wmes.get(self.root_id, []) if wme[2] in self.wmes ]
        if attr is not None:
            child_wmes = [ wme for wme in child_wmes if wme[1] == attr ]
        return [ PrintoutIdentifier(self.wmes, wme[2]) for wme in child_wmes ]

    def GetAllChildValues(self, attr=None):
        # Get all children whose values are not identifiers in the wmes dict
        child_wmes = [ wme for wme in self.wmes.get(self.root_id, []) if wme[2] not in self.wmes ]
        if attr is not None:
            child_wmes = [ wme for wme in child_wmes if wme[1] == attr ]
        return [ wme[2] for wme in child_wmes ]

    def GetAllChildWmes(self):
        child_wmes = []
        for wme in self.wmes.get(self.root_id, []):
            if wme[2] in self.wmes:
                # Identifier
                child_wmes.append( (wme[1], PrintoutIdentifier(self.wmes, wme[2])) )
            else:
                # Value
                child_wmes.append( (wme[1], wme[2]) )
        return child_wmes

    def _get_value(self, attr):
        return next((wme[2] for wme in self.wmes.get(self.root_id, []) if wme[1] == attr), None)
