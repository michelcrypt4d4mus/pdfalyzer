from os import environ
from subprocess import check_output


def test_extract_pdf_text(multipage_pdf_path, script_cmd_prefix):
    cmd = script_cmd_prefix + ['extract_pdf_text', multipage_pdf_path]
    text = check_output(cmd, env=environ).decode()
    assert "psychopathic cases and would ordinarily" in text
