"""
The tests in here are not super resilient - they will fail if a code changes results in more or
fewer lines of output.
"""

from os import path
from subprocess import check_output

from lib.util.filesystem_awareness import PROJECT_DIR

PDFALYZER_EXECUTABLE = path.join(PROJECT_DIR, 'pdfalyzer.py')


# Asking for help screen is a good canary test... proves code compiles, at least.
def test_help_option():
    help_text = _run_with_args('-h')
    assert 'maximize-width' in help_text
    assert len(help_text) > 2000
    assert len(help_text.split('\n')) > 50


def test_pdfalyzer_basic_tree(adobe_type1_fonts_pdf_path, analyzing_malicious_documents_pdf_path):
    type1_tree = _run_with_args(adobe_type1_fonts_pdf_path, '-r')
    assert len(type1_tree.split("\n")) == 762

    analyzing_malicious_tree = _run_with_args(analyzing_malicious_documents_pdf_path, '-r')
    assert len(analyzing_malicious_tree.split("\n")) == 6791


def test_font_scan(adobe_type1_fonts_pdf_path):
    font_scan_output = _run_with_args(adobe_type1_fonts_pdf_path, '-f')
    assert len(font_scan_output.split("\n")) == 4877


def _run_with_args(pdf, *args) -> str:
    """check_output() technically returns bytes so we decode before returning STDOUT output"""
    return check_output([PDFALYZER_EXECUTABLE, pdf, *args]).decode()
