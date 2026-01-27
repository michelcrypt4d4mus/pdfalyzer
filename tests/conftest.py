import platform
from os import environ, remove
from pathlib import Path

PYTESTS_DIR = Path(__file__).parent
TMP_DIR = PYTESTS_DIR.joinpath('tmp')
PROJECT_DIR = PYTESTS_DIR.parent
LOG_DIR = PROJECT_DIR.joinpath('log').resolve()

for required_dir in [LOG_DIR, TMP_DIR]:
    if not required_dir.exists():
        print(f"Creating required dir '{required_dir}'")
        required_dir.mkdir(parents=True, exist_ok=True)

# Must be set before importing yaralyzer.helper.env_helper
environ['INVOKED_BY_PYTEST'] = 'True'

import pytest  # noqa: E402
from yaralyzer.util.constants import ECHO_COMMAND_OPTION, INVOKED_BY_PYTEST, NO_TIMESTAMPS_OPTION
from yaralyzer.util.helpers.file_helper import files_in_dir, relative_path     # noqa: E402
from yaralyzer.util.helpers.shell_helper import safe_args

from pdfalyzer.pdfalyzer import Pdfalyzer                  # noqa: E402
from pdfalyzer.util.constants import PDFALYZE
from pdfalyzer.util.logging import log

# TODO: importlib doesn't play nice with running tests via GitHub actions
# import importlib.resources
# PROJECT_DIR = path.join(str(importlib.resources.files('pdfalyzer')), pardir)
DOCUMENTATION_DIR = PROJECT_DIR.joinpath('doc')
SVG_DIR = DOCUMENTATION_DIR.joinpath('svgs')
RENDERED_IMAGES_DIR = SVG_DIR.joinpath('rendered_images')
FIXTURES_DIR = PYTESTS_DIR.joinpath('fixtures')
RENDERED_FIXTURES_DIR = FIXTURES_DIR.joinpath('rendered')

# TODO: --output path should be in here but then it won't trigger the directory cleanup of tmp_dir
COMMON_ARGS = [
    '--allow-missed-nodes',
    ECHO_COMMAND_OPTION,
    NO_TIMESTAMPS_OPTION,
]

OUTPUT_DIR_ARGS = safe_args([
    '--output-dir',
    TMP_DIR,
])

ARGPARSE_ARGS = COMMON_ARGS + [
    '--min-decode-length', '50',
    '--max-decode-length', '51',
    '--suppress-decodes',
    '--export-txt',
]

# TODO: use env_helpers
is_windows = lambda: platform.system.lower() == 'windows'


@pytest.fixture(scope='session', autouse=True)
def clean_tmp_dir():
    for file in files_in_dir(TMP_DIR):
        if '/tmp/' not in str(file):
            raise ValueError(f"Can't unlink a file '{file}' in a non-tmp dir!")

        log.warning(f"Deleting temp file '{relative_path(file)}'")
        remove(file)


# Full paths to PDF test fixtures
@pytest.fixture(scope='session')
def adobe_type1_fonts_pdf_path() -> Path:
    return _pdf_in_doc_dir('Type1_Acrobat_Font_Explanation.pdf')

@pytest.fixture(scope='session')
def analyzing_malicious_pdf_path() -> Path:
    return _pdf_in_doc_dir('analyzing-malicious-document-files.pdf')

# Has unplaced empty nodes, formerly unplaced nodes, and /AA /JavaScript nodes
@pytest.fixture(scope='session')
def sf424_page2_pdf_path() -> Path:
    return FIXTURES_DIR.joinpath('SF424_page2.pdf')

# Has mysterious unplaced nodes
@pytest.fixture(scope='session')
def form_evince_path() -> Path:
    return FIXTURES_DIR.joinpath('form_evince.pdf')


# Some obj ids for use with -f when you want to limit yourself to the font
@pytest.fixture(scope="session")
def font_obj_ids_in_analyzing_malicious_docs_pdf():
    return [5, 9, 11, 13, 15, 17]


# PDFalyzers to parse them
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


@pytest.fixture(scope="session")
def multipage_pdf_path():
    return FIXTURES_DIR.joinpath('The Consul General at Berlin to FDR underecretary of State June 1933.pdf')


# This might have been too clever
# @pytest.fixture
# def rendered_output_dir(tmp_dir) -> Path:
#     if should_rebuild_fixtures():
#         return RENDERED_FIXTURES_DIR
#     else:
#         return tmp_dir


@pytest.fixture
def rendered_fixtures_dir() -> Path:
    return RENDERED_FIXTURES_DIR


@pytest.fixture
def tmp_dir() -> Path:
    """Clear the tmp dir when fixture is loaded."""
    return TMP_DIR


def _pdf_in_doc_dir(filename: str) -> Path:
    """The couple of PDFs in the /doc dir make handy fixtures"""
    return DOCUMENTATION_DIR.joinpath(filename)


# Argument fixtures
@pytest.fixture
def common_args(tmp_dir) -> list[str]:
    """These args are always used by tests."""
    return safe_args(['--output-dir', tmp_dir] + ARGPARSE_ARGS)


# Argument fixtures
@pytest.fixture
def common_shell_cmd(common_args):
    """These args are always used by tests."""
    return [PDFALYZE] + common_args


# Argument fixtures
@pytest.fixture
def pdfalyze_analyzing_malicious_args(pdfalyze_analyzing_malicious_shell_cmd) -> list[str]:
    """Remove the 'pdfalyze' in front so we get just the args."""
    return pdfalyze_analyzing_malicious_shell_cmd[1:]


@pytest.fixture
def pdfalyze_analyzing_malicious_shell_cmd(analyzing_malicious_pdf_path, common_args) -> list[str]:
    return [PDFALYZE] + safe_args(common_args + [analyzing_malicious_pdf_path])


@pytest.fixture
def script_cmd_prefix() -> list[str]:
    return ['poetry', 'run'] if is_windows() else []


# @pytest.fixture
# def pdfalyze_export_txt_cmd(tmp_dir) -> Callable[[str | Path, list[object]], list[str]]:
#     def _export_txt_cmd(pdf_path: str | Path, *args) -> list[str]:
#         return pdfalyze_cmd(pdf_path, '--output-dir', tmp_dir,  '-txt', *args)

#     return _export_txt_cmd


def pdfalyze_cmd(pdf_path: str | Path, *args) -> list[str]:
    return safe_args([PDFALYZE, pdf_path, *COMMON_ARGS, *args])


def export_txt_cmd(pdf_path: str | Path, *args) -> list[str]:
    return pdfalyze_cmd(pdf_path, '--output-dir', TMP_DIR,  '-txt', *args)
