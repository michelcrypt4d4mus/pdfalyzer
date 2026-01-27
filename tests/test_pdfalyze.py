"""
Tests of the command line script 'pdfalyze FILE [OPTIONS].
Unit tests for Pdfalyzer *class* are in the other file: test_pdfalyzer.py.
"""
from pathlib import Path
from sys import version_info
from typing import Callable, Sequence

import pytest
from os import environ
from subprocess import CalledProcessError, check_output

from yaralyzer.util.constants import NO_TIMESTAMPS_OPTION
from yaralyzer.util.helpers.shell_helper import ShellResult, safe_args

from pdfalyzer.util.constants import PDFALYZE

from .conftest import COMMON_ARGS, OUTPUT_DIR_ARGS, RENDERED_FIXTURES_DIR

NO_LOG_ARGS = safe_args(COMMON_ARGS + OUTPUT_DIR_ARGS)


@pytest.fixture
def compare_to_fixture(pdfalyze_file_cmd) -> Callable[[Path, Sequence[str | Path]], ShellResult]:
    def _compare_exported_txt_to_fixture(file_to_scan: str | Path, *args):
        """
        Compare the output of running yaralyze for a given file/arg combo to prerecorded fixture data.
        'fixture_name' arg should be used in cases where tests with different filename outputs
        can be compared against the same fixture file.
        """
        cmd = pdfalyze_file_cmd(file_to_scan, *[*args, '-txt', NO_TIMESTAMPS_OPTION])
        return ShellResult.run_and_compare_exported_files_to_existing(cmd, RENDERED_FIXTURES_DIR)#, DEFAULT_CLI_ARGS)

    return _compare_exported_txt_to_fixture


# Asking for help screen is a good canary test... proves code compiles, at least.
def test_help_option(pdfalyze_run):
    help_text = pdfalyze_run('-h').stdout_stripped
    assert 'maximize-width' in help_text
    assert 'http' not in help_text
    assert len(help_text) > 2000
    assert len(help_text.split('\n')) > 50


# Can't use match='...' because the error msg goes to STDERR and is not captured by Python
# TODO: this test could be more accurate if we could both get the CalledProcessError AND the STDERR output?
def test_bad_args(additional_yara_rules_path, analyzing_malicious_pdf_path):
    with pytest.raises(CalledProcessError):
        # ShellResult.from_cmd(pdf)
        _run_with_args('bad_file.pdf')
    with pytest.raises(CalledProcessError):
        _run_with_args(analyzing_malicious_pdf_path, '--output-dir', 'bad_dir')
    with pytest.raises(CalledProcessError):
        _run_with_args(analyzing_malicious_pdf_path, '--force-decode-threshold', '105')
    with pytest.raises(CalledProcessError):
        _run_with_args(analyzing_malicious_pdf_path, '--no-default-yara-rules')


def test_multi_export(analyzing_malicious_pdf_path, compare_to_fixture):
    result = compare_to_fixture(analyzing_malicious_pdf_path)
    exported_files = result.exported_file_paths()
    assert len(exported_files) == 6


def test_pdfalyze_CLI_basic_tree(adobe_type1_fonts_pdf_path, compare_to_fixture):
    compare_to_fixture(adobe_type1_fonts_pdf_path, '-t')


def test_pdfalyze_CLI_rich_tree(adobe_type1_fonts_pdf_path, compare_to_fixture, sf424_page2_pdf_path):
    compare_to_fixture(adobe_type1_fonts_pdf_path, '-r')
    compare_to_fixture(sf424_page2_pdf_path, '-r')


def test_pdfalyze_CLI_yara_scan(adobe_type1_fonts_pdf_path, compare_to_fixture):
    compare_to_fixture(adobe_type1_fonts_pdf_path, '-y')


def test_pdfalyze_CLI_streams_scan(adobe_type1_fonts_pdf_path, compare_to_fixture):
    compare_to_fixture(adobe_type1_fonts_pdf_path, '-s')
    compare_to_fixture(adobe_type1_fonts_pdf_path, '--suppress-boms', '-s')
    compare_to_fixture(adobe_type1_fonts_pdf_path, '-s', '48')


def test_pdfalyze_non_zero_return_code(analyzing_malicious_pdf_path, script_cmd_prefix):
    cmd = script_cmd_prefix + safe_args([PDFALYZE, analyzing_malicious_pdf_path, '-t'])

    with pytest.raises(CalledProcessError):
        result = ShellResult.from_cmd(cmd)
        assert 'Found 1 important missing node IDs: [67]' in (result.stderr_stripped or '')
        result.result.check_returncode()


def test_yara_rules_option(adobe_type1_fonts_pdf_path, additional_yara_rules_path, compare_to_fixture):
    compare_to_fixture(adobe_type1_fonts_pdf_path, '-Y', additional_yara_rules_path)
    compare_to_fixture(adobe_type1_fonts_pdf_path, '--no-default-yara-rules', '-Y', additional_yara_rules_path)  # noqa: E501


@pytest.mark.skipif(version_info >= (3, 14), reason="currently failing (fixture mismatch) on python 3.14")
def test_quote_extraction(adobe_type1_fonts_pdf_path, compare_to_fixture):
    compare_to_fixture(adobe_type1_fonts_pdf_path, '--extract-quoted', 'backtick', '-s')
    compare_to_fixture(adobe_type1_fonts_pdf_path, '--extract-quoted', 'backtick', '--extract-quoted', 'frontslash', '-s')  # noqa: E501


def test_pdfalyze_CLI_font_scan(adobe_type1_fonts_pdf_path, compare_to_fixture):
    compare_to_fixture(adobe_type1_fonts_pdf_path, '-f')


# def _check_same_as_fixture(pdf_path: str | Path, *args):
#     cmd = export_txt_cmd(pdf_path, *args)
#     return ShellResult.run_and_compare_exported_files_to_existing(cmd, RENDERED_FIXTURES_DIR, no_log_args=NO_LOG_ARGS)


def _run_with_args(pdf: str | Path, *args) -> str:
    """check_output() technically returns bytes so we decode before returning STDOUT output"""
    return check_output(_pdfalyze_cmd(pdf, *args), env=environ).decode()


def _pdfalyze_cmd(pdf_path: str | Path, *args) -> list[str]:
    return safe_args([PDFALYZE, pdf_path, '--allow-missed-nodes', *args])
