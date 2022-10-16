from pdfalyzer.decorators.indeterminate_node import IndeterminateNode


def test_find_common_ancestor_among_nodes(page_node, analyzing_malicious_pdfalyzer):
    nodes = [analyzing_malicious_pdfalyzer.find_node_by_idnum(id) for id in [2, 4, 12, 417]]
    assert IndeterminateNode(nodes[2])._find_common_ancestor_among_nodes(nodes) == nodes[0]
