"""Test Pdfalyzer() methods."""


def test_is_in_tree(analyzing_malicious_pdfalyzer, page_node):
    assert analyzing_malicious_pdfalyzer.is_in_tree(page_node)


def test_unplaced_nodes(SF424_page2_pdfalyzer):
    assert len(SF424_page2_pdfalyzer.missing_node_ids()) == 272
