import Python_sml_ClientInterface as sml

from .SoarWME import SoarWME

class SoarUtils:
    """ A Class containing static utility methods for dealing with Soar and working memory """

    def update_wm_from_tree(root_id: sml.Identifier, root_name, input_dict, wme_table):
        """
        Recursively update WMEs that have a sub-tree structure rooted at the given identifier.

        We scan through the `input_dict`, which represents the input value getters (or further
        sub-trees) of the sub-tree root, either adding terminal WMEs as usual or further recursing.

        :param root_id: The sml identifier of the root of the sub-tree
        :param root_name: The attribute which is the root of this sub-tree
        :param input_dict: A dict mapping attributes to getter functions
        :param wme_table: A table to lookup and store wme's and identifiers
        :return: None
        """
        assert isinstance(input_dict, dict), "Should only recurse on dicts!"

        for attribute in input_dict.keys():
            input_val = input_dict[attribute]
            child_name = root_name + "." + attribute

            if not callable(input_val):
                if child_name not in wme_table:
                    wme_table[child_name] = root_id.CreateIdWME(attribute)
                child_id = wme_table[child_name]
                SoarUtils.update_wm_from_tree(child_id, child_name, input_val, wme_table)
                continue

            value = input_val()
            if child_name not in wme_table:
                wme_table[child_name] = SoarWME(att=attribute, val=value)
            wme = wme_table[child_name]
            wme.set_value(value)
            wme.update_wm(root_id)

    def remove_tree_from_wm(wme_table):
        """
        Given a wme_table filled by SoarUtils.update_wm_from_tree, removes all wmes from working memory 

        Intermediate nodes are sml.Identifiers, which are removed from the table
        Leaves are SoarWME's which are kept in the table but .remove_from_wm() is called on them
        """
        items_to_remove = set()
        for path, wme in wme_table.items():
            if isinstance(wme, sml.Identifier):
                items_to_remove.add(path)
            else:
                wme.remove_from_wm()
        for path in items_to_remove:
            del wme_table[path]


    def extract_wm_graph(root_id, max_depth=1000000, id_map=None):
        """
        Given a soar identifier (root_id), crawls over the children and builds a graph rep for them

        Return dictionary:
            d['__id__'] = root_id 
            d['__sym__'] = root_id as a string
            d['attr'] = constant # for string, double, or int value
            d['attr'] = dict # for identifier
            d['attr'] = [ val1, val2, ... ] # for multi-valued attributes

        This will handle loops, where the same dict will be reused for each reference to an identifier

        Example:

        Given an identifier <obj> with the following wm structure:
        (<obj> ^id 5 ^volume 23.3 ^predicates <preds>)
           (<preds> ^predicate red ^predicate cube ^predicate block)

        Will return the following dictionary:
        { 
            '__id': (sml Identifier for <obj>)
            '__sym__': 'O32' 
            'id' : 5 (int),
            'volume': 23.3 (float),
            'predicates': {
                '__id__': (sml Identifier for <preds>)
                '__sym__': 'P53'
                'predicate': [ 'red', 'cube', 'block' ]
            }
        }

        :param root_id: The sml identifier of the root of the sub-graph
        :param max_depth: The maximum depth to extract
        :param id_map: A dictionary from identifiers to their corresponding dictionaries
        :return a dict containing a recurisve enumeration of all children reachable from the given root_id
        """

        if id_map is None:
            id_map = dict()
        root_id_str = root_id.GetValueAsString()
        if root_id_str in id_map:
            return id_map[root_id_str]

        child_wmes = dict()
        child_wmes['__id__'] = root_id
        child_wmes['__sym__'] = root_id_str
        id_map[root_id_str] = child_wmes

        if max_depth == 0:
            return child_wmes

        for index in range(root_id.GetNumberChildren()):
            wme = root_id.GetChild(index)
            attr = wme.GetAttribute()
            if wme.IsIdentifier():
                wme_val = SoarUtils.extract_wm_graph(wme.ConvertToIdentifier(), max_depth-1, id_map)
            elif wme.GetValueType() == "int":
                wme_val = wme.ConvertToIntElement().GetValue()
            elif wme.GetValueType() == "double":
                wme_val = wme.ConvertToFloatElement().GetValue()
            else:
                wme_val = wme.GetValueAsString()
            if attr in child_wmes:
                cur_val = child_wmes[attr]
                if isinstance(cur_val, list):
                    cur_val.append(wme_val)
                else:
                    child_wmes[attr] = [ cur_val, wme_val ]
            else:
                child_wmes[attr] = wme_val

        return child_wmes

    def wm_graph_to_str(wm_graph):
        """
        Given a wm_graph produced by extract_wm_graph, returns a nicely formatted string representation of it

        :param wm_graph: A dictionary representing a wm graph produced by extract_wm_graph
        """
        return SoarUtils._wm_value_to_str(wm_graph, "", set())

    def _wm_value_to_str(val, indent, ignore_ids):
        """
        recursive helper function which returns a string representation of any given value type
        (str, int, float, list, dict)

        :param wm_graph: A dictionary representing a wm graph produced by extract_wm_graph
        :param indent: a string of spaces to indent the current level
        :param ignore_ids: A set of Identifiers to not print
        """
        if isinstance(val, str):
            return val
        if isinstance(val, int):
            return str(val)
        if isinstance(val, float):
            return str(val)
        if isinstance(val, list):
            return "[ " + ", ".join(SoarUtils._wm_value_to_str(i, indent, ignore_ids) for i in val) + " ]"
        if not isinstance(val, dict):
            return ""
        id_str = val['__sym__']
        if id_str in ignore_ids:
            return "<" + id_str + ">"
        ignore_ids.add(id_str)
        if len(val) == 1:
            return "<" + id_str + ">"
        s = "<" + id_str + "> {\n"
        for a, v in val.items():
            if a == '__sym__' or a == '__id__':
                continue
            s += indent + "  " + a + ": " + SoarUtils._wm_value_to_str(v, indent + "  ", ignore_ids) + "\n"
        s += indent + "}"
        return s


