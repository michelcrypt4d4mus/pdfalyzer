"""Test Pdfalyzer() methods."""
import pytest


def test_is_in_tree(analyzing_malicious_pdfalyzer, page_node):
    assert analyzing_malicious_pdfalyzer.is_in_tree(page_node)


def test_unplaced_nodes(SF424_page2_pdfalyzer, form_evince_pdfalyzer):
    assert len(SF424_page2_pdfalyzer.missing_node_ids()) == 0
    assert len(form_evince_pdfalyzer.missing_node_ids()) == 11

# This is very slow (4 minutes!)
@pytest.mark.slow
def test_slow_unplaced_nodes(test_sweep_indirect_references_nullobject_exception_pdfalyzer):
    assert len(test_sweep_indirect_references_nullobject_exception_pdfalyzer.missing_node_ids()) == 1
