import Python_sml_ClientInterface as sml

### Note: Helper class used by extract_wm_graph

class WMNode:
    """ Represents a node in the working memory graph wrapping an Identifier and containing links to child wmes

        node.id = root_id (Identifier)
        node.symbol = string (The root_id symbol e.g. O34)
        node['attr'] = WMNode   # for identifiers
        node['attr'] = constant # for string, double, or int value
        node['attr'] = [ val1, val2, ... ] # for multi-valued attributes (values can be constants or WMNodes)
    """

    def __init__(self, soar_id):
        self.id = soar_id
        self.symbol = soar_id.GetValueAsString()
        self.children = {}

    def attributes(self):
        """ Returns a list of all child wme attribute strings """
        return list(self.children.keys())

    # Supports dictionary syntax (read only)
    def __getitem__(self, attr):
        """ Returns the value of the wme (node, attr, val)
            where a value can be a int, double, string, WMNode,
            or a list of such values for a multi-valued attribute """
        return self.children.get(attr, None)

    def __str__(self):
        """ Returns a nicely formatted string representation of the node and all its children 
            (Warning: will be a lot of text for large graphs) """
        return self.__str_helper__("", set())

    def __str_helper__(self, indent, ignore_ids):
        var = "<" + self.symbol + ">"
        if self.symbol in ignore_ids or len(self.children) == 0:
            return var

        ignore_ids.add(self.symbol)

        s = var + " {\n"
        for a, v in self.children.items():
            s += indent + "  " + a + ": " + _wm_value_to_str(v, indent + "  ", ignore_ids) + "\n"
        s += indent + "}"
        return s

    def _extract_children(self, max_depth, node_map):
        """ Internal helper method to recursively extract graph structure for a node's children """
        if max_depth == 0:
            return

        for index in range(self.id.GetNumberChildren()):
            wme = self.id.GetChild(index)
            attr = wme.GetAttribute()
            if wme.IsIdentifier():
                child_id = wme.ConvertToIdentifier()
                child_sym = child_id.GetValueAsString()
                # First check if the child id is already in the node map
                if child_sym in node_map:
                    wme_val = node_map[child_sym]
                else:
                    # If not, recursively create and extract the children
                    wme_val = WMNode(child_id)
                    node_map[wme_val.symbol] = wme_val
                    wme_val._extract_children(max_depth-1, node_map)

            elif wme.GetValueType() == "int":
                wme_val = wme.ConvertToIntElement().GetValue()
            elif wme.GetValueType() == "double":
                wme_val = wme.ConvertToFloatElement().GetValue()
            else:
                wme_val = wme.GetValueAsString()

            self._add_child_wme(attr, wme_val)

    def _add_child_wme(self, attr, value):
        """ Adds the child wme to the children dictionary
            If there are multiple values for a given attr, move them into a list instead of replacing """
        if attr in self.children:
            cur_val = self.children[attr]
            if isinstance(cur_val, list):
                # Child is already a list, just append
                cur_val.append(value)
            else:
                # This is the second value for the attr, replace current value with a list
                self.children[attr] = [ cur_val, value ]
        else:
            # First time we've seen this attr, just add to dictionary
            self.children[attr] = value

def _wm_value_to_str(val, indent, ignore_ids):
    """
    recursive helper function which returns a string representation of any given value type

    :param val: The value to convert to a string (can be str, int, float, list, WMNode)
    :param indent: a string of spaces to indent the current level
    :param ignore_ids: A set of Identifier symbols to not print
    """
    if isinstance(val, str):
        return val
    if isinstance(val, int):
        return str(val)
    if isinstance(val, float):
        return str(val)
    if isinstance(val, list):
        return "[ " + ", ".join(_wm_value_to_str(i, indent, ignore_ids) for i in val) + " ]"
    if isinstance(val, WMNode):
        return val.__str_helper__(indent, ignore_ids)
    return ""


