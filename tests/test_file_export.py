from math import isclose
from os import environ, path, remove
from pathlib import Path
from subprocess import check_output
from typing import Callable

import pytest
from yaralyzer.helpers.file_helper import files_in_dir, load_file

from pdfalyzer.config import PDFALYZE
from pdfalyzer.helpers.filesystem_helper import file_sizes_in_dir
from pdfalyzer.util.logging import log


def test_file_export(fixture_mismatch_msg, pdfalyze_analyzing_malicious_args, rendered_fixtures_dir, rendered_output_dir):
    args = ['--output-dir', str(rendered_output_dir)] + pdfalyze_analyzing_malicious_args
    check_output([PDFALYZE, *args], env=environ)
    rendered_files = sorted(files_in_dir(rendered_output_dir))
    assert len(rendered_files) == 6

    if rendered_fixtures_dir == rendered_output_dir:
        log.warning(f"Rebuilt pytest fixtures, file_sizes:")

        for fixture_path, size in file_sizes_in_dir(rendered_output_dir).items():
            log.warning(f"    '{fixture_path.relative_to(Path.cwd())}': {size}")

        return

    for file in rendered_files:
        tmp_file = Path(file)
        fixture_path = rendered_fixtures_dir.joinpath(tmp_file.name)
        assert fixture_path.exists()  # Check same filename
        fixture_contents = load_file(fixture_path)
        test_output = load_file(tmp_file)
        assert fixture_contents != test_output, fixture_mismatch_msg(fixture_path, tmp_file)
        log.warning(f"'{tmp_file.relative_to(Path.cwd())}' matches fixture: '{fixture_path.relative_to(Path.cwd())}'")


@pytest.fixture
def fixture_mismatch_msg() -> Callable[[Path, Path], str]:
    def msg(fixture_path: Path, output_path: Path) -> str:
        fixture_path = fixture_path.relative_to(Path.cwd())
        output_path = output_path.relative_to(Path.cwd())
        return f"Contents of '{output_path}' does not match fixture '{fixture_path}'"

    return msg
