from math import isclose
from os import environ, path, remove
from subprocess import check_output

import pytest
from yaralyzer.helpers.file_helper import files_in_dir

from pdfalyzer.config import PDFALYZE


# This used to fail but seems to be OK ever since upgrading yara-python to 4.5.4?
# @pytest.mark.skip(reason="YARA is throwing internal error 46 about 'too many fibers' on macOS")
@pytest.mark.slow
def test_file_export(analyzing_malicious_pdf_path, tmp_dir):
    args = [
        '--min-decode-length', '50',
        '--max-decode-length', '51',
        '--suppress-decodes',
        '-txt',
        '--output-dir', tmp_dir
    ]

    check_output([PDFALYZE, analyzing_malicious_pdf_path, *args], env=environ)
    rendered_files = files_in_dir(tmp_dir)
    assert len(rendered_files) == 6
    file_sizes = sorted([path.getsize(f) for f in rendered_files])
    assert_array_is_close(file_sizes, [6905, 8356, 13069, 35956, 189154, 1671253])

    for file in rendered_files:
        remove(file)


def assert_array_is_close(_list1, _list2):
    for i, item in enumerate(_list1):
        if not isclose(item, _list2[i], rel_tol=0.05):
            assert False, f"File size of {item} too far from {_list2[i]}"
