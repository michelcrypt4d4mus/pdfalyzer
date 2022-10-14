"""
Class to help with the pre-configured YARA rules in /yara.
"""
from importlib.resources import as_file, files
from typing import Optional, Union

from yaralyzer.yaralyzer import Yaralyzer

YARA_RULES_DIR = files('pdfalyzer').joinpath('yara_rules')

YARA_RULES_FILES = [
    'lprat.static_file_analysis.yara',
    'PDF.yara',
    'PDF_binary_stream.yara',
]


def get_file_yaralyzer(file_path_to_scan: str) -> Yaralyzer:
    """Get a yaralyzer for a file path"""
    return _build_yaralyzer(file_path_to_scan)


def get_bytes_yaralyzer(scannable: bytes, label: str) -> Yaralyzer:
    return _build_yaralyzer(scannable, label)


def _build_yaralyzer(scannable: Union[bytes, str], label: Optional[str] = None) -> Yaralyzer:
    # TODO: ugh this sucks (handling to extract .yara files from a python pkg zip)
    with as_file(YARA_RULES_DIR.joinpath(YARA_RULES_FILES[0])) as yara0:
        with as_file(YARA_RULES_DIR.joinpath(YARA_RULES_FILES[1])) as yara1:
            with as_file(YARA_RULES_DIR.joinpath(YARA_RULES_FILES[2])) as yara2:
                rules_paths = [str(y) for y in [yara0, yara1, yara2]]
                return Yaralyzer.for_rules_files(rules_paths, scannable, label)
