from argparse import Namespace

import pytest


@pytest.fixture
def pdf_parser_manager_args(analyzing_malicious_pdf_path, tmp_dir) -> Namespace:
    return Namespace(file_to_scan_path=analyzing_malicious_pdf_path, output_dir=tmp_dir)
