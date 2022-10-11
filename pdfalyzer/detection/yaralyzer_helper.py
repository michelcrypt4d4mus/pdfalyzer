"""
Class to help with the pre-configured YARA rules in /yara.
"""
import importlib.resources

from yaralyzer.yaralyzer import Yaralyzer

YARA_RULES_DIR = importlib.resources.path('pdfalyzer', 'yara_rules')


def get_file_yaralyzer(file_path_to_scan: str) -> Yaralyzer:
    """Get a yaralyzer for a file path"""
    return Yaralyzer.for_rules_dirs([str(YARA_RULES_DIR)], file_path_to_scan)


def get_bytes_yaralyzer(scannable: bytes, label: str) -> Yaralyzer:
    return Yaralyzer.for_rules_dirs([str(YARA_RULES_DIR)], scannable, label)
