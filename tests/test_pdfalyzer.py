"""
Test Pdfalyzer() methods.
"""


def test_is_in_tree(analyzing_malicious_pdfalyzer, page_node):
    assert analyzing_malicious_pdfalyzer.is_in_tree(page_node)


