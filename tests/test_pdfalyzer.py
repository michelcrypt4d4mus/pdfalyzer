"""
The tests in here are not super resilient - they will fail if a code changes results in enough
more or fewer lines of output.
"""
from math import isclose
from os import environ
from subprocess import check_output

from yaralyzer.config import MAX_DECODE_LENGTH_ENV_VAR

from pdfalyzer.config import PDFALYZE


# Asking for help screen is a good canary test... proves code compiles, at least.
def test_help_option():
    help_text = _run_with_args('-h')
    assert 'maximize-width' in help_text
    assert len(help_text) > 2000
    assert len(help_text.split('\n')) > 50


def test_pdfalyzer_basic_tree(adobe_type1_fonts_pdf_path, analyzing_malicious_pdf_path):
    type1_tree = _run_with_args(adobe_type1_fonts_pdf_path, '-t')
    _assert_line_count_within_range(90, type1_tree)
    analyzing_malicious_tree = _run_with_args(analyzing_malicious_pdf_path, '-t')
    _assert_line_count_within_range(1022, analyzing_malicious_tree)


def test_is_in_tree(analyzing_malicious_pdfalyzer, page_node):
    assert analyzing_malicious_pdfalyzer.is_in_tree(page_node)


def test_pdfalyzer_rich_tree(adobe_type1_fonts_pdf_path, analyzing_malicious_pdf_path):
    type1_tree = _run_with_args(adobe_type1_fonts_pdf_path, '-r')
    _assert_line_count_within_range(952, type1_tree)
    analyzing_malicious_tree = _run_with_args(analyzing_malicious_pdf_path, '-r')
    _assert_line_count_within_range(6970, analyzing_malicious_tree)


def test_font_scan(adobe_type1_fonts_pdf_path):
    environ[MAX_DECODE_LENGTH_ENV_VAR] = '2'
    font_scan_output = _run_with_args(adobe_type1_fonts_pdf_path, '-f')
    _assert_line_count_within_range(188, font_scan_output)


def test_yara_scan(adobe_type1_fonts_pdf_path):
    font_scan_output = _run_with_args(adobe_type1_fonts_pdf_path, '-y')
    _assert_line_count_within_range(590, font_scan_output)


def _run_with_args(pdf, *args) -> str:
    """check_output() technically returns bytes so we decode before returning STDOUT output"""
    return check_output([PDFALYZE, pdf, *args], env=environ).decode()


def _assert_line_count_within_range(line_count, text):
    lines_in_text = len(text.split("\n"))

    if not isclose(line_count, lines_in_text, rel_tol=0.05):
        for i, line in enumerate(text.split("\n")):
            print(f"{i}: {line}")

        assert False, f"Expected {line_count} +/- but found {lines_in_text}"
