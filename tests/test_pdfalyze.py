"""
Tests of the command line script 'pdfalyze FILE [OPTIONS].
Unit tests for Pdfalyzer *class* are in the other file: test_pdfalyzer.py.
"""
import pytest
from math import isclose
from os import environ
from subprocess import CalledProcessError, check_output

from pdfalyzer.config import PDFALYZE


# Asking for help screen is a good canary test... proves code compiles, at least.
def test_help_option():
    help_text = _run_with_args('-h')
    assert 'maximize-width' in help_text
    assert len(help_text) > 2000
    assert len(help_text.split('\n')) > 50


def test_bad_args(analyzing_malicious_pdf_path):
    with pytest.raises(CalledProcessError):
        _run_with_args(analyzing_malicious_pdf_path, '--extract-quoted', 'noquotes')
    with pytest.raises(CalledProcessError):
        _run_with_args(analyzing_malicious_pdf_path, '--extract-quoted', 'backtick', '--tree')
    with pytest.raises(CalledProcessError):
        _run_with_args(analyzing_malicious_pdf_path, '--force-decode-threshold', '105')


def test_pdfalyze_CLI_basic_tree(adobe_type1_fonts_pdf_path, analyzing_malicious_pdf_path):
    _assert_args_yield_lines(90, adobe_type1_fonts_pdf_path, '-t')
    _assert_args_yield_lines(1022, analyzing_malicious_pdf_path, '-t')


def test_pdfalyze_CLI_rich_tree(adobe_type1_fonts_pdf_path, analyzing_malicious_pdf_path):
    _assert_args_yield_lines(952, adobe_type1_fonts_pdf_path, '-r')
    _assert_args_yield_lines(6970, analyzing_malicious_pdf_path, '-r')


def test_pdfalyze_CLI_yara_scan(adobe_type1_fonts_pdf_path):
    _assert_args_yield_lines(774, adobe_type1_fonts_pdf_path, '-y')


def test_pdfalyze_CLI_streams_scan(adobe_type1_fonts_pdf_path):
    _assert_args_yield_lines(1560, adobe_type1_fonts_pdf_path, '-s')
    _assert_args_yield_lines(1165, adobe_type1_fonts_pdf_path, '--suppress-boms', '-s')
    _assert_args_yield_lines(135, adobe_type1_fonts_pdf_path, '-s', '48')


def test_yara_rules_option(adobe_type1_fonts_pdf_path, additional_yara_rules_path):
    _assert_args_yield_lines(2447, adobe_type1_fonts_pdf_path, '-Y', additional_yara_rules_path)


@pytest.mark.slow
def test_quote_extraction(adobe_type1_fonts_pdf_path):
    _assert_args_yield_lines(2914, adobe_type1_fonts_pdf_path, '--extract-quoted', 'backtick', '-s')
    _assert_args_yield_lines(5736, adobe_type1_fonts_pdf_path, '--extract-quoted', 'backtick', '--extract-quoted', 'frontslash', '-s')


def test_pdfalyze_CLI_font_scan(adobe_type1_fonts_pdf_path, analyzing_malicious_pdf_path):
    _assert_args_yield_lines(197, adobe_type1_fonts_pdf_path, '-f')
    _assert_args_yield_lines(205, analyzing_malicious_pdf_path, '-f')


def _assert_args_yield_lines(line_count, file, *args) -> bool:
    output = _run_with_args(file, *args)
    assertion = _assert_line_count_within_range(line_count, output)
    assert assertion[0], assertion[1]


def _run_with_args(pdf, *args) -> str:
    """check_output() technically returns bytes so we decode before returning STDOUT output"""
    return check_output([PDFALYZE, pdf, *args], env=environ).decode()


def _assert_line_count_within_range(line_count, text):
    lines_in_text = len(text.split("\n"))

    if not isclose(line_count, lines_in_text, rel_tol=0.05):
        for i, line in enumerate(text.split("\n")):
            print(f"{i}: {line}")

        return (False, f"Expected {line_count} +/- but found {lines_in_text}")

    return (True, 'True')
