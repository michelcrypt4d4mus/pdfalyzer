"""Test Pdfalyzer() methods."""
import pytest


def test_is_in_tree(analyzing_malicious_pdfalyzer, page_node):
    assert analyzing_malicious_pdfalyzer.is_in_tree(page_node)


@pytest.mark.slow
def test_unplaced_nodes(SF424_page2_pdfalyzer, test_sweep_indirect_references_nullobject_exception_pdfalyzer):
    assert len(SF424_page2_pdfalyzer.missing_node_ids()) == 0
    # This is very slow:
    assert len(test_sweep_indirect_references_nullobject_exception_pdfalyzer.missing_node_ids()) == 1
