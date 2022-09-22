from os import environ, path
import pytest

from lib.data_stream_handler import LIMIT_DECODES_LARGER_THAN_ENV_VAR
from lib.pdf_parser_manager import PROJECT_DIR
from lib.pdf_walker import PdfWalker

ANALYZING_MALICIOUS_DOCUMENTS_PDF = path.join(PROJECT_DIR, 'doc', 'analyzing-malicious-document-files.pdf')

# Speeds things up considerably
environ[LIMIT_DECODES_LARGER_THAN_ENV_VAR] = '48'


@pytest.fixture(scope='session')
def pdfs_in_repo():
    return [ANALYZING_MALICIOUS_DOCUMENTS_PDF]


@pytest.fixture(scope='session')
def analyzing_malicious_documents_pdf_path():
    return ANALYZING_MALICIOUS_DOCUMENTS_PDF


@pytest.fixture(scope="session")
def analyzing_malicious_documents_pdf_walker(analyzing_malicious_documents_pdf_path):
    return PdfWalker(analyzing_malicious_documents_pdf_path)
