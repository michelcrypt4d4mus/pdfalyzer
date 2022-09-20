from os import path
from subprocess import check_call

from lib.pdf_parser_manager import PROJECT_DIR

PDFALYZER_EXECUTABLE = path.join(PROJECT_DIR, 'pdfalyzer.py')


def test_pdfalyzer_py_executable(pdfs_in_repo):
    for pdf in pdfs_in_repo:
        check_call([PDFALYZER_EXECUTABLE, pdf])
