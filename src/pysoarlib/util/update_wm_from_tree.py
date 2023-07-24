from pysoarlib import SoarWME

def update_wm_from_tree(root_id, root_name, input_dict, wme_table):
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

