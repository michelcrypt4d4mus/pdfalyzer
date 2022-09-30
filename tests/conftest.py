

from os import environ, path
environ['INVOKED_BY_PYTEST'] = 'True'

import pytest

from lib.config import MAX_DECODE_LENGTH_ENV_VAR, PYTEST_FLAG
from lib.pdf_walker import PdfWalker
from lib.util.filesystem_awareness import DOCUMENTATION_DIR


# Env var option that may Speeds things up considerably
environ[MAX_DECODE_LENGTH_ENV_VAR] = '2'


# Full paths to PDF test fixtures
@pytest.fixture(scope='session')
def adobe_type1_fonts_pdf_path():
    return _pdf_in_doc_dir('Type1_Acrobat_Font_Explanation.pdf')

@pytest.fixture(scope='session')
def analyzing_malicious_documents_pdf_path():
    return _pdf_in_doc_dir('analyzing-malicious-document-files.pdf')

# Some obj ids for use with -f when you want to limit yourself to the font
@pytest.fixture(scope="session")
def font_obj_ids_in_analyzing_malicious_docs_pdf():
    return [9, 11, 13, 15, 17]


# PDF walkers to parse them
@pytest.fixture(scope="session")
def analyzing_malicious_documents_pdf_walker(analyzing_malicious_documents_pdf_path):
    return PdfWalker(analyzing_malicious_documents_pdf_path)

@pytest.fixture(scope="session")
def adobe_type1_fonts_pdf_walker(adobe_type1_fonts_pdf_path):
    return PdfWalker(adobe_type1_fonts_pdf_path)


# Handy iterator
@pytest.fixture(scope='session')
def all_pdf_fixtures_in_repo(adobe_type1_fonts_pdf, analyzing_malicious_documents_pdf_path):
    return [
        adobe_type1_fonts_pdf,
        analyzing_malicious_documents_pdf_path
    ]


def _pdf_in_doc_dir(filename):
    """The couple of PDFs in the /doc dir make handy fixtures"""
    return path.join(DOCUMENTATION_DIR, filename)
