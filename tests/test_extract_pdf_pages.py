from os import environ, path
from pathlib import Path
from subprocess import check_output

import pytest

PAGE_2_EXTENSION = "__page_2.pdf"


@pytest.fixture
def extracted_pdf_path(multipage_pdf_path, tmp_dir):
    extracted_basename = path.basename(multipage_pdf_path).replace('.pdf', PAGE_2_EXTENSION)
    extracted_path = Path(tmp_dir).joinpath(extracted_basename)

    if extracted_path.exists():
        extracted_path.unlink()

    yield extracted_path

    if extracted_path.exists():
        extracted_path.unlink()


def test_extract_pdf_pages(extracted_pdf_path, multipage_pdf_path, tmp_dir):
    cmd_stdout = check_output(['extract_pdf_pages', '-r', '2', '-d', tmp_dir, multipage_pdf_path], env=environ).decode()
    assert "__page_2.pdf" in cmd_stdout
    assert extracted_pdf_path.exists()
    text = check_output(['extract_text_from_pdfs', extracted_pdf_path], env=environ).decode()
    assert "woefully ignorant and unprepared" in text
