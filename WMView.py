from pysoarlib.util import parse_wm_printout

class WMView:
    """ WMView provides a working-memory like view over some wrapped datastructures, 
        the details of which are abstracted away from the user

        Consumers can use the view and not worry about the underlying representation
        They should not every assume anything about the identifier type (e.g. root_id)
        and should only use it as a handle into the view"""

    def __init__(self, root_id):
        self.root_id = root_id

    def get_root(self):
        """ Returns the root identifier for the view """
        return self.root_id

    def id_to_str(self, id):
        """ Returns a string representation of the given identifier """
        pass

    def get_child_id(self, id, attr):
        """ Returns a child identifier matching (<id> ^attr <child_id>) or None """
        pass

    def get_all_child_ids(self, id, attr):
        """ Returns a list of child identifiers matching (<id> ^attr <child_id>) """
        pass

    def get_value(self, id, attr):
        """ Returns a value string matching (<id> ^attr <val>), or None """
        pass

    def get_all_values(self, id, attr):
        """ Returns a list of values matching (<id> ^attr <val>) """
        pass

    def get_wmes(self, id):
        """ Returns a list of (attr, val) string tuples representing all wmes rooted at the given identifier """
        pass



class SmlView(WMView):
    """ An SmlView provides a working-memory like view that wraps sml objects """

    def __init__(self, root_id):
        """ root_id is an sml Identifier """
        super().__init__(self, root_id)

    def get_root(self):
        return self.root_id

    def id_to_str(self, id):
        return id.GetValueAsString()

    def get_child_id(self, id, attr):
        return id.get_child_id(attr)

    def get_all_child_ids(self, id, attr):
        return id.get_all_child_ids(attr)

    def get_value(self, id, attr):
        return id.get_child_str(attr)

    def get_all_values(self, id, attr):
        return id.get_all_child_values(attr)

    def get_wmes(self, id):
        wmes = []
        for index in range(self.GetNumberChildren()):
            wme = self.GetChild(index)
            if wme.IsIdentifier():
                wmes.append( (wme.GetAttribute(), wme.ConvertToIdentifier()) )
            else:
                wmes.append( (wme.GetAttribute(), wme.GetValueAsString()) )
        return wmes


class PrintoutView(WMView):
    """ A PrintoutView provides a working-memory like view for the result
        of a soar print command """

    def __init__(self, printout):
        """ printout is the text result from a soar print command (e.g. print S1 -d 3) """
        self.root_id = printout.split()[0].replace('(', '')
        super().__init__(self, root_id)

        # wmes is a dictionary mapping identifiers to a list of wmes
        #   { id_str: [ (id_str, attr, val_str) ] }
        self.wmes = parse_wm_printout(printout)

    def get_child_id(self, id, attr):
        return self.get_value(id, attr)

    def get_all_child_ids(self, id, attr):
        return self.get_all_values(id, attr)

    def get_value(self, id, attr):
        return next((wme[2] for wme in self.wmes.get(id, []) if wme[1] == attr), None)

    def get_all_values(self, id, attr):
        return [ wme[2] for wme in self.wmes.get(id, []) if wme[1] == attr ]

    def get_all_wmes(self, id):
        return [ (wme[1], wme[2]) for wme in self.wmes.get(id, []) ]

    def id_to_str(self, id):
        return id

