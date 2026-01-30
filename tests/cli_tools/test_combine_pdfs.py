from os import environ
from pathlib import Path
from subprocess import check_output

import pytest
from yaralyzer.util.helpers.file_helper import files_in_dir

from pdfalyzer.util.helpers.filesystem_helper import file_size_in_mb

from ..conftest import FIXTURES_DIR

COMBINE_PDFS = 'combine_pdfs'


@pytest.fixture
def one_page_pdfs():
    return files_in_dir(FIXTURES_DIR.joinpath('one_page_pdfs'), 'pdf')


@pytest.fixture
def combined_pdf_path(tmp_dir):
    combined_path = Path(tmp_dir).joinpath('combined.pdf')

    if combined_path.exists():
        combined_path.unlink()

    yield combined_path

    if combined_path.exists():
        combined_path.unlink()


def test_combine_pdfs(combined_pdf_path, one_page_pdfs, script_cmd_prefix):
    assert not combined_pdf_path.exists()
    assert len(one_page_pdfs) == 3
    check_output(script_cmd_prefix + [COMBINE_PDFS, '-o', combined_pdf_path, *one_page_pdfs], env=environ).decode()
    assert combined_pdf_path.exists()
    assert file_size_in_mb(combined_pdf_path) == 0.18


@pytest.mark.slow
def test_combine_pdfs_image_quality(combined_pdf_path, one_page_pdfs, script_cmd_prefix):
    assert not combined_pdf_path.exists()
    cmd = script_cmd_prefix + [COMBINE_PDFS, '-o', combined_pdf_path, '-iq', '1', *one_page_pdfs]
    check_output(cmd, env=environ).decode()
    assert combined_pdf_path.exists()
    assert file_size_in_mb(combined_pdf_path) == 0.09
