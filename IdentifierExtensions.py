INTEGER_VAL = "int"
FLOAT_VAL = "double"
STRING_VAL = "string"

## Given id and attribute, returns value for WME as string (self ^attribute value)
def get_child_str(self, attribute): 
    wme = self.FindByAttribute(attribute, 0)
    if wme == None or wme.GetValueAsString().length() == 0:
        return None
    return wme.GetValueAsString()

## Given id and attribute, returns integer value for WME (self ^attribute value)
def get_child_int(self, attribute): 
    wme = self.FindByAttribute(attribute, 0)
    if wme == None or wme.GetValueType() != INTEGER_VAL:
        return None
    return wme.ConvertToIntElement().GetValue()

## Given id and attribute, returns float value for WME (self ^attribute value)
def get_child_float(self, attribute): 
    wme = self.FindByAttribute(attribute, 0)
    if wme == None or wme.GetValueType() != FLOAT_VAL:
        return None
    return wme.ConvertToFloatElement().GetValue()

## Given id and attribute, returns identifier value of WME (self ^attribute child_id)
def get_child_id(self, attribute): 
    wme = self.FindByAttribute(attribute, 0)
    if wme == None or not wme.IsIdentifier():
        return None
    return wme.ConvertToIdentifier()

## Given id and attribute, returns a list of child identifiers from all WME's matching (self ^attribute child_id)
## If no attribute is specified, all child identifiers are returned
def get_all_child_ids(self, attribute=None): 
    child_ids = []
    for index in range(self.GetNumberChildren()):
        wme = self.GetChild(index)
        if not wme.IsIdentifier():
            continue
        if attribute == None or wme.GetAttribute() == attribute:
            child_ids.append(wme.ConvertToIdentifier())
    return child_ids

## Given id and attribute, returns a list of strings of values from all WME's matching (self ^attribute value)
## If no attribute is specified, all child values (non-identifiers) are returned
def get_all_child_values(self, attribute=None): 
    child_values = []
    for index in range(self.GetNumberChildren()):
        wme = self.GetChild(index)
        if wme.IsIdentifier():
            continue
        if attribute == None or wme.GetAttribute() == attribute:
            child_values.append(wme.GetValueAsString())
    return child_values
