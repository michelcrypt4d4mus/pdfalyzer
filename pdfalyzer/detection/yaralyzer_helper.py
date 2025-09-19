"""
Functions to help with the pre-configured YARA rules in the /yara directory.
"""
from importlib.resources import as_file, files
from typing import Optional, Union

from yaralyzer.config import YaralyzerConfig
from yaralyzer.output.rich_console import print_fatal_error_and_exit
from yaralyzer.yaralyzer import Yaralyzer

from pdfalyzer.config import PDFALYZER

YARA_RULES_DIR = files(PDFALYZER).joinpath('yara_rules')

YARA_RULES_FILES = [
    'didier_stevens.yara',
    'lprat.static_file_analysis.yara',
    'PDF.yara',
    'PDF_binary_stream.yara',
    'pdf_malware.yara',
]


def get_file_yaralyzer(file_path_to_scan: str) -> Yaralyzer:
    """Get a yaralyzer for a file path."""
    return _build_yaralyzer(file_path_to_scan)


def get_bytes_yaralyzer(scannable: bytes, label: str) -> Yaralyzer:
    """Get a yaralyzer for a `scannable` bytes."""
    return _build_yaralyzer(scannable, label)


def _build_yaralyzer(scannable: Union[bytes, str], label: Optional[str] = None) -> Yaralyzer:
    """Build a yaralyzer for .yara rules files stored in the yara_rules/ dir in this package."""
    # TODO: ugh this sucks (handling to extract .yara files from a python pkg zip)
    with as_file(YARA_RULES_DIR.joinpath(YARA_RULES_FILES[0])) as yara0:
        with as_file(YARA_RULES_DIR.joinpath(YARA_RULES_FILES[1])) as yara1:
            with as_file(YARA_RULES_DIR.joinpath(YARA_RULES_FILES[2])) as yara2:
                with as_file(YARA_RULES_DIR.joinpath(YARA_RULES_FILES[3])) as yara3:
                    with as_file(YARA_RULES_DIR.joinpath(YARA_RULES_FILES[4])) as yara4:
                        # If there is a custom yara_rules arg, use that instead of the files in the yara_rules/ dir
                        rules_paths = YaralyzerConfig.args.yara_rules_files or []

                        if not YaralyzerConfig.args.no_default_yara_rules:
                            rules_paths += [str(y) for y in [yara0, yara1, yara2, yara3, yara4]]

                        try:
                            return Yaralyzer.for_rules_files(rules_paths, scannable, label)
                        except FileNotFoundError as e:
                            print_fatal_error_and_exit(str(e))
