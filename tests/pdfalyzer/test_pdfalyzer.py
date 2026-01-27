import pytest
from pypdf.errors import FileNotDecryptedError

from pdfalyzer.pdfalyzer import Pdfalyzer

from tests.conftest import FIXTURES_DIR


# Has unplaced empty nodes, formerly unplaced nodes, and /AA /JavaScript nodes
@pytest.fixture(scope='session')
def sf424_page2_pdfalyzer(sf424_page2_pdf_path) -> Pdfalyzer:
    return Pdfalyzer(sf424_page2_pdf_path)


def test_password():
    encrypted_pdf_path = FIXTURES_DIR.joinpath('encrypted-file.pdf')
    pdfalyzer = Pdfalyzer(encrypted_pdf_path, password='test')
    assert len(pdfalyzer.font_infos) == 1

    with pytest.raises(FileNotDecryptedError):
        pdfalyzer = Pdfalyzer(encrypted_pdf_path, password='bad')


def test_is_in_tree(analyzing_malicious_pdfalyzer, page_node):
    assert analyzing_malicious_pdfalyzer.is_in_tree(page_node)


def test_unplaced_nodes(form_evince_pdfalyzer, sf424_page2_pdfalyzer):
    assert len(form_evince_pdfalyzer.missing_node_ids()) == 11
    assert len(sf424_page2_pdfalyzer.missing_node_ids()) == 0


# This is very slow (4 minutes!)
@pytest.mark.slow
def test_slow_unplaced_nodes(test_sweep_indirect_references_nullobject_exception_pdfalyzer):
    assert len(test_sweep_indirect_references_nullobject_exception_pdfalyzer.missing_node_ids()) == 1
