from os import environ
from subprocess import check_output


def test_extract_pdf_text(multipage_pdf_path):
    text = check_output(['extract_pdf_text', multipage_pdf_path], env=environ).decode()
    assert "psychopathic cases and would ordinarily" in text
