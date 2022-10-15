import pytest

from pdfalyzer.decorators.pdf_tree_node import PdfTreeNode


@pytest.fixture(scope="session")
def page_node(analyzing_malicious_pdfalyzer):
    return analyzing_malicious_pdfalyzer.find_node_by_idnum(3)


@pytest.fixture(scope="session")
def pages_node(analyzing_malicious_pdfalyzer):
    return analyzing_malicious_pdfalyzer.find_node_by_idnum(2)


def test_pdf_node_address(analyzing_malicious_pdfalyzer):
    node41 = analyzing_malicious_pdfalyzer.find_node_by_idnum(41)
    assert node41.tree_address() == '/Root/StructTreeRoot/K[0]/K[24]/K[1]/K[3]/K[0]/K[0]/K[1]/K[0]/Obj'
    node6 = analyzing_malicious_pdfalyzer.find_node_by_idnum(6)
    assert node6.tree_address() == '/Root/Pages/Kids[0]/Resources[/Font][/F1]/FontDescriptor'
    node17 = analyzing_malicious_pdfalyzer.find_node_by_idnum(17)
    assert node17.tree_address() == '/Root/Pages/Kids[0]/Resources[/Font][/F4]/DescendantFonts[0]/CIDSystemInfo'


def test_address_in_other_node(analyzing_malicious_pdfalyzer, page_node, pages_node):
    sym_node = analyzing_malicious_pdfalyzer.find_node_by_idnum(13)
    assert sym_node.address_in_other_node(page_node) == '/Annots[0]'
    node38 = analyzing_malicious_pdfalyzer.find_node_by_idnum(38)
    assert node38.address_in_other_node(page_node) == '/Annots[14]'

    node7 = analyzing_malicious_pdfalyzer.find_node_by_idnum(7)
    assert node7.address_in_other_node(page_node) == '/Resources[/ExtGState][/GS7]'
    assert page_node.address_in_other_node(pages_node) == '/Kids[0]'


def test_referenced_by_keys(analyzing_malicious_pdfalyzer, page_node):
    node = analyzing_malicious_pdfalyzer.find_node_by_idnum(7)
    assert node.unique_addresses() == ['/Resources[/ExtGState][/GS7]']
    assert sorted(page_node.unique_addresses()) ==  ['/Dest[0]', '/Kids[0]', '/Pg']


def test_find_common_ancestor_among_nodes(analyzing_malicious_pdfalyzer):
    nodes = [analyzing_malicious_pdfalyzer.find_node_by_idnum(id) for id in [2, 4, 12, 417]]
    assert PdfTreeNode.find_common_ancestor_among_nodes(nodes) == nodes[0]
