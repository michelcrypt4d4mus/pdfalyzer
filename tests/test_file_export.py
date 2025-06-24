import json
from math import isclose
from os import environ, path, remove
from subprocess import check_output

import pytest
from yaralyzer.helpers.file_helper import files_in_dir

from pdfalyzer.config import PDFALYZE


@pytest.mark.slow
@pytest.mark.skip(reason="YARA is throwing internal error 46 about 'too many fibers' on macOS")
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
    assert_array_is_close(file_sizes, [6905, 8356, 35908, 170612, 181688, 1689983])

    for file in rendered_files:
        remove(file)


def assert_array_is_close(_list1, _list2):
    for i, item in enumerate(_list1):
        if not isclose(item, _list2[i], rel_tol=0.05):
            assert False, f"File size of {item} too far from {_list2[i]}"


def test_json_export(one_page_pdf_path, tmp_dir):
    """Test JSON export functionality."""
    import sys
    args = [
        sys.executable, '-m', 'pdfalyzer',
        one_page_pdf_path,
        '-json',
        '--output-dir', tmp_dir,
        '--docinfo',
        '--tree',
        '--counts',
        '--fonts'
    ]
    
    check_output(args, env=environ)
    
    # Check that JSON files were created
    json_files = [f for f in files_in_dir(tmp_dir) if f.endswith('.json')]
    assert len(json_files) >= 4  # At least docinfo, tree, summary, and manifest
    
    # Verify each JSON file is valid and contains expected data
    for json_file in json_files:
        with open(json_file, 'r') as f:
            data = json.load(f)
            assert isinstance(data, dict)
            
        # Check specific file contents
        if 'docinfo.json' in json_file:
            assert 'metadata' in data
            assert 'hashes' in data
            assert 'file_size' in data
            assert 'pdf_file' in data
            
        elif 'tree.json' in json_file:
            assert 'root' in data
            assert 'total_nodes' in data
            assert 'pdf_file' in data
            
        elif 'summary.json' in json_file:
            assert 'node_type_counts' in data
            assert 'total_objects' in data
            assert 'pdf_file' in data
            
        elif 'manifest.json' in json_file:
            assert 'exports' in data
            assert 'timestamp' in data
            assert 'pdf_file' in data
            
        elif 'fonts.json' in json_file:
            assert 'fonts' in data
            assert 'total_fonts' in data
            assert 'pdf_file' in data
    
    # Clean up
    for file in json_files:
        remove(file)
