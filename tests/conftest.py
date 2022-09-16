from os import path
import pytest

from lib.pdf_parser_manager import PROJECT_DIR

ANALYZING_MALICIOUS_DOCUMENTS_PDF = path.join(PROJECT_DIR, 'doc', 'analyzing-malicious-document-files.pdf')


@pytest.fixture
def pdfs_in_repo():
    return [
        ANALYZING_MALICIOUS_DOCUMENTS_PDF
    ]


@pytest.fixture
def analyzing_malicious_documents_pdf():
    return ANALYZING_MALICIOUS_DOCUMENTS_PDF
