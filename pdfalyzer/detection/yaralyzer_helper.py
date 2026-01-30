"""
Functions to help with the pre-configured YARA rules in the /yara directory.
"""
from importlib.resources import as_file, files
from pathlib import Path

from yaralyzer.util.exceptions import print_fatal_error_and_exit
from yaralyzer.yaralyzer import Yaralyzer

from pdfalyzer.config import PdfalyzerConfig
from pdfalyzer.util.constants import PDFALYZER

YARA_RULES_DIR = files(PDFALYZER).joinpath('yara_rules')
YARA_RULES_NOT_FOUND_MSG = f"A YARA rule that's supposed to ship with Pdfalyzer is missing. Please file a bug."

YARA_RULES_FILES = [
    'didier_stevens.yara',
    'lprat.static_file_analysis.yara',
    'PDF.yara',
    'PDF_binary_stream.yara',
    'pdf_malware.yara',
]


def get_file_yaralyzer(file_path_to_scan: str | Path) -> Yaralyzer:
    """Get a yaralyzer for a file path."""
    return _build_yaralyzer(file_path_to_scan)


def get_bytes_yaralyzer(scannable: bytes, label: str) -> Yaralyzer:
    """Get a yaralyzer for a `scannable` bytes."""
    return _build_yaralyzer(scannable, label)


def _build_yaralyzer(scannable: bytes | str | Path, label: str = '') -> Yaralyzer:
    """Build a yaralyzer for .yara rules files stored in the yara_rules/ dir in this package."""
    # TODO: ugh this sucks (handling to extract .yara files from a python pkg zip)
    with as_file(YARA_RULES_DIR.joinpath(YARA_RULES_FILES[0])) as yara0:
        with as_file(YARA_RULES_DIR.joinpath(YARA_RULES_FILES[1])) as yara1:
            with as_file(YARA_RULES_DIR.joinpath(YARA_RULES_FILES[2])) as yara2:
                with as_file(YARA_RULES_DIR.joinpath(YARA_RULES_FILES[3])) as yara3:
                    with as_file(YARA_RULES_DIR.joinpath(YARA_RULES_FILES[4])) as yara4:
                        # If there is a custom yara_rules arg, use that instead of the files in the yara_rules/ dir
                        rules_paths = PdfalyzerConfig.args.yara_rules_files or []

                        if not PdfalyzerConfig.args.no_default_yara_rules:
                            rules_paths = rules_paths + [str(y) for y in [yara0, yara1, yara2, yara3, yara4]]

                        try:
                            return Yaralyzer.for_rules_files(rules_paths, scannable, label)
                        except FileNotFoundError as e:
                            print_fatal_error_and_exit(f"{YARA_RULES_NOT_FOUND_MSG}: {e}")
                            raise e
