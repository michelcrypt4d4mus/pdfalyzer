import platform
from os import environ, remove
from pathlib import Path
from typing import Callable, Sequence

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
from yaralyzer.util.constants import ECHO_COMMAND_OPTION, NO_TIMESTAMPS_OPTION
from yaralyzer.util.helpers.file_helper import files_in_dir, relative_path     # noqa: E402
from yaralyzer.util.helpers.shell_helper import ShellResult, safe_args

from pdfalyzer.util.constants import PDFALYZE
from pdfalyzer.util.logging import log

# TODO: importlib doesn't play nice with running tests via GitHub actions
# import importlib.resources
# PROJECT_DIR = path.join(str(importlib.resources.files('pdfalyzer')), pardir)
FIXTURES_DIR = PYTESTS_DIR.joinpath('fixtures')
RENDERED_FIXTURES_DIR = FIXTURES_DIR.joinpath('rendered')

DOCUMENTATION_DIR = PROJECT_DIR.joinpath('doc')
SVG_DIR = DOCUMENTATION_DIR.joinpath('svgs')
RENDERED_IMAGES_DIR = SVG_DIR.joinpath('rendered_images')

PDFALYZE_BASE_CMD = [PDFALYZE, ECHO_COMMAND_OPTION, '--allow-missed-nodes', NO_TIMESTAMPS_OPTION]

# TODO: use env_helpers
is_windows = lambda: platform.system().lower() == 'windows'


# Runs at start every time to clean up tmp_dir
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
    return DOCUMENTATION_DIR.joinpath('Type1_Acrobat_Font_Explanation.pdf')

@pytest.fixture(scope='session')
def analyzing_malicious_pdf_path() -> Path:
    return DOCUMENTATION_DIR.joinpath('analyzing-malicious-document-files.pdf')

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


@pytest.fixture
def pdfalyze_cmd(script_cmd_prefix, _output_dir_args) -> Callable[[Sequence[str | Path]], list[str]]:
    """Shell command to run 'pdfalyze [whatever]'."""
    def _shell_cmd(*args) -> list[str]:
        cmd = safe_args(script_cmd_prefix + PDFALYZE_BASE_CMD + _output_dir_args + [*args])

        if True:# is_windows():
            log.warning(f"current test: {environ.get('PYTEST_CURRENT_TEST')}\n         cmd: {cmd}")

        return cmd

    return _shell_cmd


@pytest.fixture
def pdfalyze_file_cmd(pdfalyze_cmd) -> Callable[[Path, Sequence[str | Path]], list[str]]:
    """Shell command to run run 'pdfalyze [FILE] [whatever]'."""
    def _shell_cmd(file_path: Path, *args) -> list[str]:
        return safe_args(pdfalyze_cmd(file_path, *args))

    return _shell_cmd


@pytest.fixture
def pdfalyze_file(pdfalyze_file_cmd) -> Callable[[Path, Sequence[str | Path]], ShellResult]:
    def _run_pdfalyze(file_to_scan: str | Path, *args) -> ShellResult:
        return ShellResult.from_cmd(pdfalyze_file_cmd(file_to_scan, *args), verify_success=True)

    return _run_pdfalyze


@pytest.fixture
def script_cmd_prefix() -> list[str]:
    return ['poetry', 'run'] if is_windows() else []


@pytest.fixture
def tmp_dir() -> Path:
    """Clear the tmp dir when fixture is loaded."""
    return TMP_DIR


@pytest.fixture
def _output_dir_args(tmp_dir) -> list[str]:
    return safe_args(['--output-dir', tmp_dir])
