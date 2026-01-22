from copy import copy
from os import environ, path, remove
from pathlib import Path
environ['INVOKED_BY_PYTEST'] = 'True'  # Must be set before importing yaralyzer (?)

import pytest                                              # noqa: E402
from yaralyzer.config import is_env_var_set_and_not_false  # noqa: E402
from yaralyzer.helpers.file_helper import files_in_dir     # noqa: E402

from pdfalyzer.pdfalyzer import Pdfalyzer                  # noqa: E402

# TODO: importlib doesn't play nice with running tests via GitHub actions
# import importlib.resources
# PROJECT_DIR = path.join(str(importlib.resources.files('pdfalyzer')), pardir)
PYTESTS_DIR = Path(path.dirname(__file__))
PROJECT_DIR = PYTESTS_DIR.parent
DOCUMENTATION_DIR = PROJECT_DIR.joinpath('doc')
SVG_DIR = DOCUMENTATION_DIR.joinpath('svgs')
RENDERED_IMAGES_DIR = SVG_DIR.joinpath('rendered_images')
FIXTURES_DIR = PROJECT_DIR.joinpath('tests', 'fixtures')
RENDERED_FIXTURES_DIR = FIXTURES_DIR.joinpath('rendered')
REBUILD_FIXTURES_ENV_VAR = 'PYTEST_REBUILD_FIXTURES'

BASE_ARGS = [
    '--min-decode-length', '50',
    '--max-decode-length', '51',
    '--suppress-decodes',
    '--allow-missed-nodes',
    '--export-txt',
]


@pytest.fixture
def pytests_dir():
    return PYTESTS_DIR


#######################
#    PDF test paths   #
#######################
@pytest.fixture(scope='session')
def adobe_type1_fonts_pdf_path() -> Path:
    return _pdf_in_doc_dir('Type1_Acrobat_Font_Explanation.pdf')

@pytest.fixture(scope='session')
def analyzing_malicious_pdf_path() -> Path:
    return _pdf_in_doc_dir('analyzing-malicious-document-files.pdf')

# Has a Type1 font with character map. PDF comes from pypdf repo.
@pytest.fixture(scope='session')
def attachment_pdf_pdfalyzer():
    return Pdfalyzer(FIXTURES_DIR.joinpath('attachment.pdf'))

# Has /Resources that is not an IndirectObject, also has multiple /DescendantFonts and /ObjStm
@pytest.fixture(scope='session')
def geobase_pdfalyzer():
    return Pdfalyzer(FIXTURES_DIR.joinpath('GeoBase_NHNC1_Data_Model_UML_EN.pdf'))

# Has unplaced empty nodes, formerly unplaced nodes, and /AA /JavaScript nodes
@pytest.fixture(scope='session')
def sf424_page2_pdf_path() -> Path:
    return FIXTURES_DIR.joinpath('SF424_page2.pdf')

# Has mysterious unplaced nodes
@pytest.fixture(scope='session')
def form_evince_path() -> Path:
    return FIXTURES_DIR.joinpath('form_evince.pdf')


##########################
#    Pdfalyzer objects   #
##########################
@pytest.fixture(scope="session")
def analyzing_malicious_pdfalyzer(analyzing_malicious_pdf_path):
    return Pdfalyzer(analyzing_malicious_pdf_path)

@pytest.fixture(scope="session")
def adobe_type1_fonts_pdfalyzer(adobe_type1_fonts_pdf_path):
    return Pdfalyzer(adobe_type1_fonts_pdf_path)

# Has mysterious unplaced nodes
@pytest.fixture(scope='session')
def form_evince_pdfalyzer(form_evince_path):
    return Pdfalyzer(form_evince_path)

@pytest.fixture(scope='session')
def SF424_page2_pdfalyzer(SF424_page2_pdf_path):
    return Pdfalyzer(SF424_page2_pdf_path)

@pytest.fixture(scope='session')
def test_sweep_indirect_references_nullobject_exception_pdfalyzer():
    return Pdfalyzer(FIXTURES_DIR.joinpath('test_sweep_indirect_references_nullobject_exception.pdf'))


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


# Some obj ids for use with -f when you want to limit yourself to the font
@pytest.fixture(scope="session")
def font_obj_ids_in_analyzing_malicious_docs_pdf():
    return [5, 9, 11, 13, 15, 17]


@pytest.fixture(scope="session")
def additional_yara_rules_path():
    return FIXTURES_DIR.joinpath('additional_yara_rules.yara')


@pytest.fixture(scope="session")
def multipage_pdf_path():
    return FIXTURES_DIR.joinpath('The Consul General at Berlin to FDR underecretary of State June 1933.pdf')


@pytest.fixture
def should_rebuild_fixtures() -> bool:
    return is_env_var_set_and_not_false(REBUILD_FIXTURES_ENV_VAR)


@pytest.fixture
def rendered_output_dir(should_rebuild_fixtures, tmp_dir) -> Path:
    if should_rebuild_fixtures:
        return RENDERED_FIXTURES_DIR
    else:
        return tmp_dir


@pytest.fixture
def rendered_fixtures_dir() -> Path:
    return RENDERED_FIXTURES_DIR


@pytest.fixture
def tmp_dir(pytests_dir) -> Path:
    """Clear the tmp dir when fixture is loaded."""
    tmpdir = pytests_dir.joinpath('tmp')

    for file in files_in_dir(tmpdir):
        remove(file)

    return tmpdir


def _pdf_in_doc_dir(filename: str) -> Path:
    """The couple of PDFs in the /doc dir make handy fixtures"""
    return DOCUMENTATION_DIR.joinpath(filename)


# Argument fixtures
@pytest.fixture
def base_args():
    return copy(BASE_ARGS)


@pytest.fixture
def pdfalyze_analyzing_malicious_args(analyzing_malicious_pdf_path, base_args):
    return base_args + [str(analyzing_malicious_pdf_path)]


@pytest.fixture
def export_analyzing_malicious_args(pdfalyze_analyzing_malicious_args, tmp_dir):
    return ['--output-dir', str(tmp_dir)] + pdfalyze_analyzing_malicious_args
