from copy import copy

import pytest

BASE_ARGS = [
    '--min-decode-length', '50',
    '--max-decode-length', '51',
    '--suppress-decodes',
    '--allow-missed-nodes',
    '--export-txt',
]


@pytest.fixture
def base_args():
    return copy(BASE_ARGS)


@pytest.fixture
def pdfalyze_analyzing_malicious_args(analyzing_malicious_pdf_path, base_args):
    return base_args + [str(analyzing_malicious_pdf_path)]


@pytest.fixture
def export_analyzing_malicious_args(pdfalyze_analyzing_malicious_args, tmp_dir):
    return ['--output-dir', str(tmp_dir)] + pdfalyze_analyzing_malicious_args
