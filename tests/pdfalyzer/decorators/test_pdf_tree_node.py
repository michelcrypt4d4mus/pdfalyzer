import pytest


@pytest.fixture(scope="session")
def page_node(analyzing_malicious_documents_pdfalyzer):
    return analyzing_malicious_documents_pdfalyzer.find_node_by_idnum(3)


def test_pdf_node_address(analyzing_malicious_documents_pdfalyzer):
    node = analyzing_malicious_documents_pdfalyzer.find_node_by_idnum(41)
    assert node.tree_address() == '/Root/StructTreeRoot/K[0]/K[24]/K[1]/K[3]/K[0]/K[0]/K[1]/K[0]/Obj'
    node2 = analyzing_malicious_documents_pdfalyzer.find_node_by_idnum(6)
    assert node2.tree_address() == '/Root/Pages/Kids[0]/Resources[/Font][/F1]/FontDescriptor'
    node3 = analyzing_malicious_documents_pdfalyzer.find_node_by_idnum(17)
    assert node3.tree_address() == '/Root/Pages/Kids[0]/Resources[/Font][/F4]/DescendantFonts[0]/CIDSystemInfo'


def test_get_address_for_relationship(analyzing_malicious_documents_pdfalyzer, page_node):
    sym_node = analyzing_malicious_documents_pdfalyzer.find_node_by_idnum(13)
    assert sym_node.get_address_for_relationship(page_node) == '/Annots[0]'


def test_referenced_by_keys(analyzing_malicious_documents_pdfalyzer, page_node):
    node = analyzing_malicious_documents_pdfalyzer.find_node_by_idnum(7)
    assert node.addresses() == ['/Resources[/ExtGState][/GS7]']
    assert sorted(page_node.addresses()) ==  ['/Dest', '/Kids[0]', '/Pg']
