"""
Various text formatting/styling/manipulating methods.
"""
import re
from pprint import PrettyPrinter
from typing import List, Pattern, Union

from PyPDF2.generic import PdfObject
from yaralyzer.output.rich_console import console_width

INDENT_DEPTH = 4
PRETTY_PRINT_WIDTH = 60
DIGIT_REGEX = re.compile("\d+")

# Pretty Printer
pp = PrettyPrinter(
    indent=INDENT_DEPTH,
    width=PRETTY_PRINT_WIDTH,
    sort_dicts=True)


def pypdf_class_name(obj: PdfObject) -> str:
    """Shortened name of type(obj), e.g. PyPDF2.generic._data_structures.ArrayObject becomes Array"""
    class_pkgs = type(obj).__name__.split('.')
    class_pkgs.reverse()
    return class_pkgs[0].removesuffix('Object')


def generate_hyphen_line(width=None, title=None):
    """e.g. '-----------------BEGIN-----------------'"""
    width = width or console_width()

    if title is None:
        return '-' * width

    side_hyphens = int((width - len(title)) / 2) * '-'
    line = side_hyphens + title + side_hyphens
    return line if len(line) == width else line + '-'


def count_pattern_matches_in_text(pattern: str, text: str) -> int:
    return count_regex_matches_in_text(re.compile(pattern), text)


def count_regex_matches_in_text(regex: Pattern, text: str) -> int:
    """For use when you precompile the regex"""
    return sum(1 for _ in regex.finditer(text))


def root_address(_string: str) -> str:
    """Strip the bracketed part off an address, e.g. '/Root[1]' => '/Root'."""
    return _string.split('[')[0]


def is_prefixed_by_any(_string: str, prefixes: List[str]) -> bool:
    """Returns True if _string starts with anything in 'prefixes'."""
    return any([_string.startswith(prefix) for prefix in prefixes])


def bracketed(index: Union[int, str]) -> str:
    """Surround index with [ and ]."""
    return f"[{index}]"


def replace_digits(string_with_digits: str) -> str:
    """Turn all digits to X chars in a string."""
    return DIGIT_REGEX.sub('x', string_with_digits)
