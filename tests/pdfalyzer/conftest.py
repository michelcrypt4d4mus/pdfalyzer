import pytest

BASE_ARGS = [
    '--min-decode-length', '50',
    '--max-decode-length', '51',
    '--suppress-decodes',
    '--allow-missed-nodes',
    '--export-txt',
]


@pytest.fixture
def pdfalyzer_args(analyzing_malicious_pdf_path, tmp_dir):
    return BASE_ARGS + [
        '--output-dir', str(tmp_dir),
        str(analyzing_malicious_pdf_path),
    ]
