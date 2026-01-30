"""
Various text formatting/styling/manipulating methods.
"""
import re
from pprint import PrettyPrinter
from typing import Pattern

from pypdf.generic import IndirectObject

from yaralyzer.output.console import console_width
from yaralyzer.util.helpers.string_helper import (INDENT_DEPTH, INDENT_SPACES, INDENTED_JOINER,
     NON_WORD_CHAR_REGEX, indented)

ARRAY_IDX_REGEX = re.compile(r"\[\d+\]")
PRETTY_PRINT_WIDTH = 60
DIGIT_REGEX = re.compile(r"\d+")

# Pretty Printer
pp = PrettyPrinter(
    indent=INDENT_DEPTH,
    width=PRETTY_PRINT_WIDTH,
    sort_dicts=True
)


def all_strings_are_same_ignoring_numbers(strings: list[str]) -> bool:
    """Returns true if string addresses are same except for digits."""
    return len(set([replace_digits(s) for s in strings])) == 1


def bracketed(index: int | str) -> str:
    """Surround index with [ and ]."""
    return f"[{index}]"


def class_name_regex(t: type) -> re.Pattern:
    return re.compile(t.__name__)


def coerce_address(address: str | int) -> str:
    return bracketed(address) if isinstance(address, int) else address


def count_pattern_matches_in_text(pattern: str, text: str) -> int:
    return count_regex_matches_in_text(re.compile(pattern), text)


def count_regex_matches_in_text(regex: Pattern, text: str) -> int:
    """For use when you precompile the regex."""
    return sum(1 for _ in regex.finditer(text))


def exception_str(e: Exception) -> str:
    """A string with the type and message."""
    return f"{type(e).__name__}: {e}"


def generate_hyphen_line(width: int | None = None, title: str | None = None):
    """e.g. '-----------------BEGIN-----------------'"""
    width = width or console_width()

    if title is None:
        return '-' * width

    side_hyphens = int((width - len(title)) / 2) * '-'
    line = side_hyphens + title + side_hyphens
    return line if len(line) == width else line + '-'


def has_a_common_substring(strings: list[str]) -> bool:
    return all([is_substring_of_longer_strings_in_list(s, strings) for s in strings])


def highlight_pattern(regex: re.Pattern | str) -> str:
    """Build a rich.Highlighter style pattern, e.g. `(?P<stream_object>((De|En)coded)?StreamObject)`."""
    pattern = regex.pattern if isinstance(regex, re.Pattern) else regex
    label = regex_to_capture_group_label(regex)

    if len(pattern) <= 2:
        pattern = fr"^{pattern}$"
    else:
        pattern = fr"{pattern}\b".removeprefix('/')

        if not pattern.startswith('^'):
            pattern = fr"(\b|/){pattern}"

    return fr"(?P<{label}>{pattern})"


def is_array_idx(address: str) -> bool:
    """True if address looks like '[23]'."""
    return bool(ARRAY_IDX_REGEX.match(address))


def is_prefixed_by_any(_string: str, prefixes: list[str]) -> bool:
    """Returns True if _string starts with anything in 'prefixes'."""
    return any([_string.startswith(prefix) for prefix in prefixes])


def is_substring_of_longer_strings_in_list(_string: str, strings: list[str]) -> bool:
    """Return True if '_string' is a substring of all the 'strings' longer than '_string'."""
    longer_strings = [s for s in strings if len(s) > len(_string)]
    return all([_string in longer_string for longer_string in longer_strings])


def numbered_list(objs: list, indent: int = 4) -> str:
    list_str = '\n'.join([f"[{i + 1}] {e}" for i, e in enumerate(objs)])
    return indented(list_str, spaces=indent)


def props_string(obj: object, keys: list[str] | None = None, joiner: str = ', ') -> str:
    prefix = INDENT_SPACES if '\n' in joiner else ''
    return prefix + joiner.join(props_strings(obj, keys))


def props_string_indented(obj: object, keys: list[str] | None = None) -> str:
    return props_string(obj, keys, INDENTED_JOINER)


def props_strings(obj: object, keys: list[str] | None = None) -> list[str]:
    """Get props of 'obj' in the format ["prop1=5", "prop2='string'"] etc."""
    props = []

    for k in (keys or [k for k in vars(obj).keys()]):
        value = getattr(obj, k)
        value = f"'{value}'" if isinstance(value, str) else value
        value = repr(value) if isinstance(value, IndirectObject) else value
        props.append(f"{k}={value}")

    return props


def regex_to_capture_group_label(pattern: re.Pattern | str) -> str:
    pattern = pattern.pattern if isinstance(pattern, re.Pattern) else pattern
    return NON_WORD_CHAR_REGEX.sub('', pattern.replace('|', '_'))


def replace_digits(string_with_digits: str) -> str:
    """Turn all digits to X chars in a string."""
    return DIGIT_REGEX.sub('x', string_with_digits)


def root_address(_string: str) -> str:
    """Strip the bracketed part off an address, e.g. '/Root[1]' => '/Root'."""
    return _string.split('[')[0]
