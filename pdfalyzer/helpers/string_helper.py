"""
Various text formatting/styling/manipulating methods.
"""
import re
from pprint import PrettyPrinter
from typing import List, Pattern, Union

from yaralyzer.output.rich_console import console_width

INDENT_DEPTH = 4
PRETTY_PRINT_WIDTH = 60
DIGIT_REGEX = re.compile("\\d+")

# Pretty Printer
pp = PrettyPrinter(
    indent=INDENT_DEPTH,
    width=PRETTY_PRINT_WIDTH,
    sort_dicts=True)


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


def all_strings_are_same_ignoring_numbers(strings: List[str]) -> bool:
    """Returns true if string addresses are same except for digits."""
    return len(set([replace_digits(s) for s in strings])) == 1


def is_substring_of_longer_strings_in_list(_string: str, strings: List[str]) -> bool:
    longer_strings = [s for s in strings if len(s) > len(_string)]
    return all([_string in longer_string for longer_string in longer_strings])


def has_a_common_substring(strings: List[str]) -> bool:
    return all([
        is_substring_of_longer_strings_in_list(s, strings)
        for s in strings
    ])
