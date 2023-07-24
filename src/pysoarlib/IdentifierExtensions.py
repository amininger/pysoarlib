""" Defines additional helper methods for the Identifier class for accessing child values

This module is not intended to be imported directly,
Importing the pysoarlib module will cause these to be added to the Identifier class
Note that the methods will use CamelCase, so get_child_str => GetChildStr
"""
_INTEGER_VAL = "int"
_FLOAT_VAL = "double"
_STRING_VAL = "string"

def get_child_str(self, attribute): 
    """ Given id and attribute, returns value for WME as string (self ^attribute value) """
    wme = self.FindByAttribute(attribute, 0)
    if wme == None or len(wme.GetValueAsString()) == 0:
        return None
    return wme.GetValueAsString()

def get_child_int(self, attribute): 
    """ Given id and attribute, returns integer value for WME (self ^attribute value) """
    wme = self.FindByAttribute(attribute, 0)
    if wme == None or wme.GetValueType() != _INTEGER_VAL:
        return None
    return wme.ConvertToIntElement().GetValue()

def get_child_float(self, attribute): 
    """ Given id and attribute, returns float value for WME (self ^attribute value) """
    wme = self.FindByAttribute(attribute, 0)
    if wme == None or wme.GetValueType() != _FLOAT_VAL:
        return None
    return wme.ConvertToFloatElement().GetValue()

def get_child_id(self, attribute): 
    """ Given id and attribute, returns identifier value of WME (self ^attribute child_id) """
    wme = self.FindByAttribute(attribute, 0)
    if wme == None or not wme.IsIdentifier():
        return None
    return wme.ConvertToIdentifier()

def get_all_child_ids(self, attribute=None): 
    """ Given id and attribute, returns a list of child identifiers from all WME's matching (self ^attribute child_id)

    If no attribute is specified, all child identifiers are returned
    """
    child_ids = []
    for index in range(self.GetNumberChildren()):
        wme = self.GetChild(index)
        if not wme.IsIdentifier():
            continue
        if attribute == None or wme.GetAttribute() == attribute:
            child_ids.append(wme.ConvertToIdentifier())
    return child_ids

def get_all_child_values(self, attribute=None): 
    """ Given id and attribute, returns a list of strings of non-identifier values from all WME's matching (self ^attribute value)
    
    If no attribute is specified, all child values (non-identifiers) are returned
    """
    child_values = []
    for index in range(self.GetNumberChildren()):
        wme = self.GetChild(index)
        if wme.IsIdentifier():
            continue
        if attribute == None or wme.GetAttribute() == attribute:
            child_values.append(wme.GetValueAsString())
    return child_values

def get_all_child_wmes(self):
    """ Returns a list of (attr, val) tuples representing all wmes rooted at this identifier
        val will either be an Identifier or a string, depending on its type """
    wmes = []
    for index in range(self.GetNumberChildren()):
        wme = self.GetChild(index)
        if wme.IsIdentifier():
            wmes.append( (wme.GetAttribute(), wme.ConvertToIdentifier()) )
        else:
            wmes.append( (wme.GetAttribute(), wme.GetValueAsString()) )
    return wmes


