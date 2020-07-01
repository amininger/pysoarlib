from .WMNode import WMNode

def extract_wm_graph(root_id, max_depth=-1):
    """ Given a soar identifier (root_id), crawls over the children and builds a graph rep for them
        This will handle cycles, where the same node will be used for each reference to an identifier

        :param root_id: The sml identifier of the root of the sub-graph
        :param max_depth: The maximum depth to extract (defaults to unlimited depth)
        :return a WMNode containing a recursive enumeration of all children reachable from the given root_id

        Example:

        Given an identifier <obj> with the following wm structure:
        (<obj> ^id 5 ^volume 23.3 ^predicates <preds>)
           (<preds> ^predicate red ^predicate cube ^predicate block)

        Will return the following WMNode:
        WMNode root_node
            .id = sml Identifier for <obj>
            .symbol = 'O32'
            ['id'] = 5
            ['volume'] = 23.3
            ['predicates'] = WMNode
                .id = sml Identifier for <preds>
                .symbol = 'P53'
                ['predicate'] = [ 'red', 'cube', 'block' ]
    """
    root_node = WMNode(root_id)
    node_map = dict()
    node_map[root_node.symbol] = root_node
    root_node._extract_children(max_depth, node_map)
    return root_node

