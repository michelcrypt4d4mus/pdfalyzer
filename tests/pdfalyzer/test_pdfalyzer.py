"""
Test Pdfalyzer() methods.
"""
import pytest
from pypdf.errors import FileNotDecryptedError

from pdfalyzer.pdfalyzer import Pdfalyzer

from ..conftest import FIXTURES_DIR


def test_password():
    encrypted_pdf_path = FIXTURES_DIR.joinpath('encrypted-file.pdf')
    pdfalyzer = Pdfalyzer(encrypted_pdf_path, password='test')
    assert len(pdfalyzer.font_infos) == 1

    with pytest.raises(FileNotDecryptedError):
        pdfalyzer = Pdfalyzer(encrypted_pdf_path, password='bad')


def test_is_in_tree(analyzing_malicious_pdfalyzer, page_node):
    assert analyzing_malicious_pdfalyzer.is_in_tree(page_node)
