from contextlib import contextmanager
from os import environ
from pathlib import Path

from yaralyzer.util.helpers.env_helper import temporary_env

from pdfalyzer.config import PdfalyzerConfig
from pdfalyzer.output.pdfalyzer_presenter import PdfalyzerPresenter
from pdfalyzer.util.argument_parser import parse_arguments
from pdfalyzer.util.constants import PDFALYZER_UPPER


def test_get_export_basepath(pdfalyze_analyzing_malicious_args, analyzing_malicious_pdfalyzer, tmp_dir):
    parse_arguments(pdfalyze_analyzing_malicious_args)
    presenter = PdfalyzerPresenter(analyzing_malicious_pdfalyzer)
    export_basepath = PdfalyzerConfig.get_export_basepath(presenter.print_document_info)
    assert export_basepath == f'{tmp_dir}/analyzing-malicious-document-files.pdf.document_info'


def test_env_var_for_command_line_option():
    assert PdfalyzerConfig.env_var_for_command_line_option('min_decode_length') == 'YARALYZER_MIN_DECODE_LENGTH'
    assert PdfalyzerConfig.env_var_for_command_line_option('maximize_width') == f"{PDFALYZER_UPPER}_MAXIMIZE_WIDTH"
    assert PdfalyzerConfig.env_var_for_command_line_option('suppress_boms') == f"{PDFALYZER_UPPER}_SUPPRESS_BOMS"
