"""
This module defines a utility class called SoarWME 
which wraps SML code for adding/removing Soar Working Memory Elements (WME)
"""

class SoarWME(object):
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
        self.att = att
        self.val = val
        self.wme = None

        self.added = False
        self.changed = False

        if type(val) == int:
            self.create_wme = self.__create_int_wme
        elif type(val) == float:
            self.create_wme = self.__create_float_wme
        else:
            self.create_wme = self.__create_string_wme

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

    def is_added(self):
        """ Returns true if the wme is currently in soar's working memory """
        return self.added

    def add_to_wm(self, parent_id):
        """ Creates a wme in soar's working memory rooted at the given parent_id """
        if self.wme != None:
            self.remove_from_wm()
        self.wme = self.create_wme(parent_id, self.att, self.val)
        self.added = True

    def update_wm(self):
        """ If the value has changed, will update soar's working memory with the new value """
        if self.wme == None or not self.changed:
            return
        self.wme.Update(self.val)
        self.changed = False

    def remove_from_wm(self):
        """ Will remove the wme from soar's working memory """
        if self.wme != None:
            self.wme.DestroyWME()
            self.wme = None
        self.added = False

    ### Internal Methods

    def __create_int_wme(self, id, att, val):
        return id.CreateIntWME(att, val)

    def __create_float_wme(self, id, att, val):
        return id.CreateFloatWME(att, val)

    def __create_string_wme(self, id, att, val):
        return id.CreateStringWME(att, str(val))
