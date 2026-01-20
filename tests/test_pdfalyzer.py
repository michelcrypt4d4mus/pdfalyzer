"""
Test Pdfalyzer() methods.
"""
import pytest
from pypdf.errors import FileNotDecryptedError

from pdfalyzer.pdfalyzer import Pdfalyzer

from tests.conftest import FIXTURES_DIR


def test_password():
    pdfalyzer = Pdfalyzer(FIXTURES_DIR.joinpath('encrypted-file.pdf'), password='test')
    assert len(pdfalyzer.font_infos) == 1

    with pytest.raises(FileNotDecryptedError):
        pdfalyzer = Pdfalyzer(FIXTURES_DIR.joinpath('encrypted-file.pdf'), password='bad')


def test_is_in_tree(analyzing_malicious_pdfalyzer, page_node):
    assert analyzing_malicious_pdfalyzer.is_in_tree(page_node)
