import pytest
from yaralyzer.util.helpers.env_helper import temporary_argv

from pdfalyzer.config import PdfalyzerConfig
from pdfalyzer.output.pdfalyzer_presenter import PdfalyzerPresenter
from pdfalyzer.util.constants import PDFALYZER_UPPER
from pdfalyzer.util.logging import log


@pytest.fixture
def pdfalyze_analyzing_malicious_shell_cmd(analyzing_malicious_pdf_path, pdfalyze_file_cmd, script_cmd_prefix) -> list[str]:
    return [a for a in pdfalyze_file_cmd(analyzing_malicious_pdf_path) if a not in script_cmd_prefix]


def test_get_export_basepath(pdfalyze_analyzing_malicious_shell_cmd, analyzing_malicious_pdfalyzer, tmp_dir):
    with temporary_argv(pdfalyze_analyzing_malicious_shell_cmd):
        args = PdfalyzerConfig.parse_args()

    presenter = PdfalyzerPresenter(analyzing_malicious_pdfalyzer)
    export_basepath = PdfalyzerConfig.get_export_basepath(presenter.print_document_info)
    assert export_basepath == str(tmp_dir.joinpath(analyzing_malicious_pdfalyzer.pdf_basename + '.document_info'))


def test_env_var_for_command_line_option():
    assert PdfalyzerConfig.env_var_for_command_line_option('min_decode_length') == 'YARALYZER_MIN_DECODE_LENGTH'
    assert PdfalyzerConfig.env_var_for_command_line_option('maximize_width') == f"{PDFALYZER_UPPER}_MAXIMIZE_WIDTH"
    assert PdfalyzerConfig.env_var_for_command_line_option('suppress_boms') == f"{PDFALYZER_UPPER}_SUPPRESS_BOMS"
