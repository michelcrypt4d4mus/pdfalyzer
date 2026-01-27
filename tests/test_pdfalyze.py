"""
Tests of the command line script 'pdfalyze FILE [OPTIONS].
Unit tests for Pdfalyzer *class* are in the other file: test_pdfalyzer.py.
"""
from pathlib import Path
from sys import version_info

import pytest
from os import environ
from subprocess import CalledProcessError, check_output

from yaralyzer.util.helpers.shell_helper import ShellResult, safe_args

from pdfalyzer.util.constants import PDFALYZE

from .conftest import COMMON_ARGS, OUTPUT_DIR_ARGS, RENDERED_FIXTURES_DIR, export_txt_cmd

NO_LOG_ARGS = safe_args(COMMON_ARGS + OUTPUT_DIR_ARGS)


# Asking for help screen is a good canary test... proves code compiles, at least.
def test_help_option():
    help_text = _run_with_args('-h')
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


def test_multi_export(analyzing_malicious_pdf_path, tmp_dir):
    result = _check_same_as_fixture(analyzing_malicious_pdf_path)
    exported_files = result.exported_file_paths()
    assert len(exported_files) == 6


def test_pdfalyze_CLI_basic_tree(adobe_type1_fonts_pdf_path):
    _check_same_as_fixture(adobe_type1_fonts_pdf_path, '-t')


def test_pdfalyze_CLI_rich_tree(adobe_type1_fonts_pdf_path, sf424_page2_pdf_path):
    _check_same_as_fixture(adobe_type1_fonts_pdf_path, '-r')
    _check_same_as_fixture(sf424_page2_pdf_path, '-r')


def test_pdfalyze_CLI_yara_scan(adobe_type1_fonts_pdf_path):
    _check_same_as_fixture(adobe_type1_fonts_pdf_path, '-y')


def test_pdfalyze_CLI_streams_scan(adobe_type1_fonts_pdf_path):
    _check_same_as_fixture(adobe_type1_fonts_pdf_path, '-s')
    _check_same_as_fixture(adobe_type1_fonts_pdf_path, '--suppress-boms', '-s')
    _check_same_as_fixture(adobe_type1_fonts_pdf_path, '-s', '48')


def test_pdfalyze_non_zero_return_code(analyzing_malicious_pdf_path, script_cmd_prefix):
    cmd = script_cmd_prefix + safe_args([PDFALYZE, analyzing_malicious_pdf_path, '-t'])

    with pytest.raises(CalledProcessError):
        result = ShellResult.from_cmd(cmd)
        assert 'Found 1 important missing node IDs: [67]' in result.stderr_stripped
        result.result.check_returncode()


def test_yara_rules_option(adobe_type1_fonts_pdf_path, additional_yara_rules_path):
    _check_same_as_fixture(adobe_type1_fonts_pdf_path, '-Y', additional_yara_rules_path)
    _check_same_as_fixture(adobe_type1_fonts_pdf_path, '--no-default-yara-rules', '-Y', additional_yara_rules_path)  # noqa: E501


@pytest.mark.skipif(version_info >= (3, 14), reason="currently failing (fixture mismatch) on python 3.14")
def test_quote_extraction(adobe_type1_fonts_pdf_path):
    _check_same_as_fixture(adobe_type1_fonts_pdf_path, '--extract-quoted', 'backtick', '-s')
    _check_same_as_fixture(adobe_type1_fonts_pdf_path, '--extract-quoted', 'backtick', '--extract-quoted', 'frontslash', '-s')  # noqa: E501


def test_pdfalyze_CLI_font_scan(adobe_type1_fonts_pdf_path):
    _check_same_as_fixture(adobe_type1_fonts_pdf_path, '-f')


def _check_same_as_fixture(pdf_path: str | Path, *args):
    cmd = export_txt_cmd(pdf_path, *args)
    return ShellResult.run_and_compare_exported_files_to_existing(cmd, RENDERED_FIXTURES_DIR, no_log_args=NO_LOG_ARGS)


def _run_with_args(pdf: str | Path, *args) -> str:
    """check_output() technically returns bytes so we decode before returning STDOUT output"""
    return check_output(_pdfalyze_cmd(pdf, *args), env=environ).decode()


def _pdfalyze_cmd(pdf_path: str | Path, *args) -> list[str]:
    return safe_args([PDFALYZE, pdf_path, '--allow-missed-nodes', *args])
