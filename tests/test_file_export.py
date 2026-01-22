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

from .conftest import REBUILD_FIXTURES_ENV_VAR


def test_file_export(fixture_mismatch_msg, pdfalyze_analyzing_malicious_args, rendered_fixtures_dir, rendered_output_dir):
    args = ['--output-dir', str(rendered_output_dir)] + pdfalyze_analyzing_malicious_args
    log.debug(f"Running {' '.join([PDFALYZE, *args])}")
    check_output([PDFALYZE, *args], env=environ)
    rendered_files = sorted(files_in_dir(rendered_output_dir))
    assert len(rendered_files) == 6

    if rendered_fixtures_dir == rendered_output_dir:
        for fixture_path, size in file_sizes_in_dir(rendered_output_dir).items():
            log.warning(f"    '{fixture_path.relative_to(Path.cwd())}': {size}")

        return

    for output_path in rendered_files:
        tmp_path = Path(output_path)
        fixture_path = rendered_fixtures_dir.joinpath(tmp_path.name)
        assert fixture_path.exists()
        fixture_contents = load_file(fixture_path)
        test_output = load_file(tmp_path)
        # If you assert directly pytest's diff text is very slow, so e.g. this is slow:
        # assert fixture_contents == test_output #, fixture_mismatch_msg(fixture_path, tmp_path)
        is_output_same_as_fixture = fixture_contents == test_output
        assert is_output_same_as_fixture, fixture_mismatch_msg(fixture_path, tmp_path)


@pytest.fixture
def fixture_mismatch_msg() -> Callable[[Path, Path], str]:
    def msg(fixture_path: Path, output_path: Path) -> str:
        fixture_path = fixture_path.relative_to(Path.cwd())
        output_path = output_path.relative_to(Path.cwd())
        error_msg = f"Contents of '{output_path}'\n  does not match fixture: '{fixture_path}'\n\n"
        error_msg += f"Fixtures can be updated by running '{REBUILD_FIXTURES_ENV_VAR}=True pytest'\n\n"
        error_msg += f"pytest diffs can be slow, here's the manual diff cmd:\n\n   diff '{fixture_path}' '{output_path}'\n\n"
        return error_msg

    return msg
