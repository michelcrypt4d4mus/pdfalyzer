import importlib.resources
from os import environ, path, pardir, remove
from pathlib import Path
environ['INVOKED_BY_PYTEST'] = 'True'

import pytest
from yaralyzer.helpers.file_helper import files_in_dir

from pdfalyzer.pdfalyzer import Pdfalyzer

# TODO: importlib doesn't play nice with running tests via GitHub actions
# PROJECT_DIR = path.join(str(importlib.resources.files('pdfalyzer')), pardir)
PYTESTS_DIR = path.dirname(__file__)
PROJECT_DIR = path.join(PYTESTS_DIR, pardir)
DOCUMENTATION_DIR = path.join(PROJECT_DIR, 'doc')
SVG_DIR = path.join(DOCUMENTATION_DIR, 'svgs')
RENDERED_IMAGES_DIR = path.join(SVG_DIR, 'rendered_images')
FIXTURES_DIR = Path(PROJECT_DIR).joinpath('tests', 'fixtures')


# Full paths to PDF test fixtures
@pytest.fixture(scope='session')
def adobe_type1_fonts_pdf_path():
    return _pdf_in_doc_dir('Type1_Acrobat_Font_Explanation.pdf')

@pytest.fixture(scope='session')
def analyzing_malicious_pdf_path():
    return _pdf_in_doc_dir('analyzing-malicious-document-files.pdf')


# Some obj ids for use with -f when you want to limit yourself to the font
@pytest.fixture(scope="session")
def font_obj_ids_in_analyzing_malicious_docs_pdf():
    return [5, 9, 11, 13, 15, 17]


# PDF walkers to parse them
@pytest.fixture(scope="session")
def analyzing_malicious_pdfalyzer(analyzing_malicious_pdf_path):
    return Pdfalyzer(analyzing_malicious_pdf_path)

@pytest.fixture(scope="session")
def adobe_type1_fonts_pdfalyzer(adobe_type1_fonts_pdf_path):
    return Pdfalyzer(adobe_type1_fonts_pdf_path)


# /Page and /Pages nodes
@pytest.fixture(scope="session")
def page_node(analyzing_malicious_pdfalyzer):
    return analyzing_malicious_pdfalyzer.find_node_by_idnum(3)

@pytest.fixture(scope="session")
def pages_node(analyzing_malicious_pdfalyzer):
    return analyzing_malicious_pdfalyzer.find_node_by_idnum(2)


# A font info object
@pytest.fixture(scope="session")
def font_info(analyzing_malicious_pdfalyzer):
    return next(fi for fi in analyzing_malicious_pdfalyzer.font_infos if fi.idnum == 5)


@pytest.fixture(scope="session")
def additional_yara_rules_path():
    return FIXTURES_DIR.joinpath('additional_yara_rules.yara')


@pytest.fixture
def tmp_dir():
    """Clear the tmp dir when fixture is loaded"""
    tmpdir = path.join(path.dirname(__file__), 'tmp')

    for file in files_in_dir(tmpdir):
        remove(file)

    return tmpdir


def _pdf_in_doc_dir(filename):
    """The couple of PDFs in the /doc dir make handy fixtures"""
    return path.join(DOCUMENTATION_DIR, filename)
