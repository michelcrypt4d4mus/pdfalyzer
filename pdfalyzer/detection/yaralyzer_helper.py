"""
Class to help with the pre-configured YARA rules in /yara.
"""
import re
from os import path

from yaralyzer.util.logging import log
from yaralyzer.yaralyzer import Yaralyzer

from pdfalyzer.util.filesystem_awareness import PROJECT_DIR, YARA_RULES_DIR

YARA_RULES_DIR = path.join(PROJECT_DIR, 'yara')


def get_file_yaralyzer(file_path_to_scan: str) -> Yaralyzer:
    """Get a yaralyzer for a file path"""
    return Yaralyzer.for_rules_dirs([YARA_RULES_DIR], file_path_to_scan)


def get_bytes_yaralyzer(scannable: bytes, label: str) -> Yaralyzer:
    return Yaralyzer.for_rules_dirs([YARA_RULES_DIR], scannable, label)
