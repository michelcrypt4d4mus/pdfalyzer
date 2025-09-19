from os import environ
from pathlib import Path
from subprocess import check_output

import pytest


def test_extract_text_from_pdfs(multipage_pdf_path):
    text = check_output(['extract_text_from_pdfs', multipage_pdf_path], env=environ).decode()
    assert "psychopathic cases and would ordinarily" in text
