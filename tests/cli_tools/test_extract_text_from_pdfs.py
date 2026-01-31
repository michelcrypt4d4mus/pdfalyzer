from os import environ
from subprocess import check_output

from yaralyzer.util.helpers.shell_helper import ShellResult


def test_extract_pdf_text(multipage_pdf_path, script_cmd_prefix):
    extract_cmd = script_cmd_prefix + ['extract_pdf_text', multipage_pdf_path]
    result = ShellResult.from_cmd(extract_cmd)
    assert "psychopathic cases and would ordinarily" in result.stdout
    assert 'PAGE 1' in result.stdout

    result = ShellResult.from_cmd(extract_cmd + ['--no-page-number-panels'])
    assert "psychopathic cases and would ordinarily" in result.stdout
    assert 'PAGE 1' not in result.stdout
