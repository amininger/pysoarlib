
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


