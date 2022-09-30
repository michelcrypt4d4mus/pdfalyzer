"""
Various text formatting/styling/manipulating methods.
"""
import re
from pprint import PrettyPrinter
from typing import Pattern

from PyPDF2.generic import PdfObject
from rich.panel import Panel

from pdfalyzer.helpers.rich_text_helper import console, console_width


# Style
INDENT_DEPTH = 4
PRETTY_PRINT_WIDTH = 60


# Pretty Printer
pp = PrettyPrinter(
    indent=INDENT_DEPTH,
    width=PRETTY_PRINT_WIDTH,
    sort_dicts=True)


def print_section_header(headline: str, style=None) -> None:
    style = style or ''
    console.line(2)
    console.print(Panel(headline, style=f"{style} reverse"))
    console.line()


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


def list_to_string(_list: list, sep=', ') -> str:
    """Join elements of _list with sep"""
    return sep.join([str(item) for item in _list])


def count_pattern_matches_in_text(pattern: str, text: str) -> int:
    return count_regex_matches_in_text(re.compile(pattern), text)


def count_regex_matches_in_text(regex: Pattern, text: str) -> int:
    """For use when you precompile the regex"""
    return sum(1 for _ in regex.finditer(text))


