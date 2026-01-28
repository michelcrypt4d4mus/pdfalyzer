from argparse import Namespace

import pytest

from pdfalyzer.pdfalyzer import Pdfalyzer


# PDFalyzers to parse fixture PDFs
@pytest.fixture(scope="session")
def analyzing_malicious_pdfalyzer(analyzing_malicious_pdf_path):
    return Pdfalyzer(analyzing_malicious_pdf_path)


@pytest.fixture
def pdf_parser_manager_args(analyzing_malicious_pdf_path, tmp_dir) -> Namespace:
    return Namespace(file_to_scan_path=analyzing_malicious_pdf_path, output_dir=tmp_dir)


@pytest.fixture(scope='session')
def page_node(analyzing_malicious_pdfalyzer):
    return analyzing_malicious_pdfalyzer.find_node_by_idnum(3)
