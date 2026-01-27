"""
Tests of the command line script 'pdfalyze FILE [OPTIONS].
Unit tests for Pdfalyzer *class* are in the other file: test_pdfalyzer.py.
"""
from pathlib import Path
from subprocess import CalledProcessError
from sys import version_info
from typing import Callable, Sequence

import pytest
from yaralyzer.util.constants import dotfile_name
from yaralyzer.util.helpers.shell_helper import ShellResult

from pdfalyzer.util.constants import PDFALYZER

from .conftest import FIXTURES_DIR, RENDERED_FIXTURES_DIR


@pytest.fixture(scope="session")
def additional_yara_rules_path():
    return FIXTURES_DIR.joinpath('additional_yara_rules.yara')


@pytest.fixture
def compare_to_fixture(pdfalyze_file_cmd) -> Callable[[Path, Sequence[str | Path]], ShellResult]:
    def _compare_exported_txt_to_fixture(file_to_scan: str | Path, *args):
        """
        Compare the output of running yaralyze for a given file/arg combo to prerecorded fixture data.
        'fixture_name' arg should be used in cases where tests with different filename outputs
        can be compared against the same fixture file.
        """
        cmd = pdfalyze_file_cmd(file_to_scan, *[*args, '-txt'])
        return ShellResult.run_and_compare_exported_files_to_existing(cmd, RENDERED_FIXTURES_DIR)#, DEFAULT_CLI_ARGS)

    return _compare_exported_txt_to_fixture


@pytest.fixture
def pdfalyze_run(pdfalyze_cmd) -> Callable[[Sequence[str | Path]], ShellResult]:
    """Actually executes the command."""
    def _run_yaralyze(*args) -> ShellResult:
        return ShellResult.from_cmd(pdfalyze_cmd(*args), verify_success=True)

    return _run_yaralyze


# Can't use match='...' because the error msg goes to STDERR and is not captured by Python
# TODO: this test could be more accurate if we could both get the CalledProcessError AND the STDERR output?
def test_bad_args(analyzing_malicious_pdf_path, pdfalyze_run):
    with pytest.raises(CalledProcessError):
        pdfalyze_run('bad_file.pdf')
    with pytest.raises(CalledProcessError):
        pdfalyze_run(analyzing_malicious_pdf_path, '--output-dir', 'bad_dir')
    with pytest.raises(CalledProcessError):
        pdfalyze_run(analyzing_malicious_pdf_path, '--force-decode-threshold', '105')
    with pytest.raises(CalledProcessError):
        pdfalyze_run(analyzing_malicious_pdf_path, '--no-default-yara-rules')


def test_basic_tree(adobe_type1_fonts_pdf_path, compare_to_fixture):
    compare_to_fixture(adobe_type1_fonts_pdf_path, '-t')


def test_font_scan(adobe_type1_fonts_pdf_path, compare_to_fixture):
    compare_to_fixture(adobe_type1_fonts_pdf_path, '-f')


def test_help_option(pdfalyze_run):
    help_text = pdfalyze_run('-h').stdout_stripped
    assert 'maximize-width' in help_text
    assert 'http' not in help_text
    assert dotfile_name(PDFALYZER) in help_text
    assert len(help_text) > 2000
    assert len(help_text.split('\n')) > 50


def test_multi_export(analyzing_malicious_pdf_path, compare_to_fixture):
    result = compare_to_fixture(analyzing_malicious_pdf_path)
    exported_files = result.exported_file_paths()
    assert len(exported_files) == 6


def test_non_zero_return_code(analyzing_malicious_pdf_path, pdfalyze_file_cmd):
    with pytest.raises(CalledProcessError):
        cmd = [a for a in pdfalyze_file_cmd(analyzing_malicious_pdf_path, '-t') if a != '--allow-missed-nodes']
        result = ShellResult.from_cmd(cmd)
        assert 'Found 1 important missing node IDs: [67]' in (result.stderr_stripped or '')
        result.result.check_returncode()


@pytest.mark.skipif(version_info >= (3, 14), reason="currently failing (fixture mismatch) on python 3.14")
def test_quote_extraction(adobe_type1_fonts_pdf_path, compare_to_fixture):
    args = ['--extract-quoted', 'backtick', '-s']
    compare_to_fixture(adobe_type1_fonts_pdf_path, *args)
    compare_to_fixture(adobe_type1_fonts_pdf_path, *args, '--extract-quoted', 'frontslash')  # noqa: E501


def test_rich_tree(adobe_type1_fonts_pdf_path, compare_to_fixture, sf424_page2_pdf_path):
    compare_to_fixture(adobe_type1_fonts_pdf_path, '-r')
    compare_to_fixture(sf424_page2_pdf_path, '-r')


def test_streams_scan(adobe_type1_fonts_pdf_path, compare_to_fixture):
    compare_to_fixture(adobe_type1_fonts_pdf_path, '-s')
    compare_to_fixture(adobe_type1_fonts_pdf_path, '--suppress-boms', '-s')
    compare_to_fixture(adobe_type1_fonts_pdf_path, '-s', '48')


def test_yara_scan(adobe_type1_fonts_pdf_path, compare_to_fixture):
    compare_to_fixture(adobe_type1_fonts_pdf_path, '-y')


def test_yara_rules_option(adobe_type1_fonts_pdf_path, additional_yara_rules_path, compare_to_fixture):
    compare_to_fixture(adobe_type1_fonts_pdf_path, '-Y', additional_yara_rules_path)
    compare_to_fixture(adobe_type1_fonts_pdf_path, '--no-default-yara-rules', '-Y', additional_yara_rules_path)  # noqa: E501
