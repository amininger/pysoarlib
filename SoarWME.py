"""
This module defines a utility class called SoarWME 
which wraps SML code for adding/removing Soar Working Memory Elements (WME)
"""

from .WMInterface import WMInterface

class SoarWME(WMInterface):
    """ Wrapper for a single Soar Working Memory Element with a primitive value

        It can wrap an int, float, or string type

        An instance is not directly tied to an SML wme,
            the user decides how and when soar's working memory is modified

        So you can change the value anytime (asynchronously to soar)
            And then modify working memory via add_to_wm, update_wm, and remove_from_wm
            during an agent callback (like BEFORE_INPUT_PHASE)
    """
    
    def __init__(self, att, val):
        """ Initializes the wme, but does not add to working memory yet

        :param att: The wme's attribute
        :type att: str

        :param val: The wme's value, any of the 3 main primitive types
        :type val: int, float, or str
        """
        WMInterface.__init__(self)
        self.att = att
        self.val = val
        self.wme = None

        self.changed = False

        if type(val) == int:
            self.create_wme = self._create_int_wme
        elif type(val) == float:
            self.create_wme = self._create_float_wme
        else:
            self.create_wme = self._create_string_wme

    def get_attr(self):
        """ Returns the wme's attribute """
        return self.att

    def get_value(self):
        """ Returns the wme's value """
        return self.val

    def set_value(self, newval):
        """ Set's the wme's value, but also need to call update_wm to change working memory """
        if self.val != newval:
            self.val = newval
            self.changed = True


    ### Internal Methods

    def _create_int_wme(self, id, att, val):
        return id.CreateIntWME(att, val)

    def _create_float_wme(self, id, att, val):
        return id.CreateFloatWME(att, val)

    def _create_string_wme(self, id, att, val):
        return id.CreateStringWME(att, str(val))

    def _add_to_wm_impl(self, parent_id):
        """ Creates a wme in soar's working memory rooted at the given parent_id """
        self.wme = self.create_wme(parent_id, self.att, self.val)

    def _update_wm_impl(self):
        """ If the value has changed, will update soar's working memory with the new value """
        if self.changed:
            self.wme.Update(self.val)
            self.changed = False

    def _remove_from_wm_impl(self):
        """ Will remove the wme from soar's working memory """
        self.wme.DestroyWME()
        self.wme = None

