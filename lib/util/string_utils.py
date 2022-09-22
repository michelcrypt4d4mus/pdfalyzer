"""
Various text formatting/styling/manipulating methods.
Rich colors: https://rich.readthedocs.io/en/stable/appendix/colors.html
"""
import re
from collections import namedtuple
from numbers import Number
from pprint import PrettyPrinter
from shutil import get_terminal_size

from PyPDF2.generic import ByteStringObject, IndirectObject, PdfObject
from rich.console import Console
from rich.errors import MarkupError
from rich.markup import escape
from rich.panel import Panel
from rich.text import Text

from lib.util import adobe_strings
from lib.util.rich_text_helper import DEFAULT_LABEL_STYLE, PDFALYZER_THEME


# Style
INDENT_DEPTH = 4
PRETTY_PRINT_WIDTH = 60
DEFAULT_CONSOLE_PRINT_WIDTH = 160
CONSOLE_PRINT_WIDTH = min([get_terminal_size().columns, DEFAULT_CONSOLE_PRINT_WIDTH])
CONSOLE_PRINT_BYTE_WIDTH = int(CONSOLE_PRINT_WIDTH / 4.0)
SUBHEADING_WIDTH = int(CONSOLE_PRINT_WIDTH * 0.75)

TYPE_STYLES = {
    Number: 'bright_cyan bold',
    dict: 'color(64)',
    list: 'color(143)',
    str: 'bright_white bold',
    IndirectObject: 'color(157)',
    ByteStringObject: 'bytes',
}

LABEL_STYLES = [
    [re.compile('JavaScript|JS|OpenAction', re.I | re.M), 'blink bold red'],
    [re.compile(f'^{adobe_strings.FONT_DESCRIPTOR}'),     'cornflower_blue'],
    [re.compile(f'^{adobe_strings.FONT_FILE}'),           'steel_blue1'],
    [re.compile(f'^{adobe_strings.FONT}'),                'deep_sky_blue4 bold'],
    [re.compile(f'^{adobe_strings.TO_UNICODE}'),          'grey30'],
    [re.compile(f'^{adobe_strings.WIDTHS}'),              'color(67)'],
    [re.compile(f'^{adobe_strings.W}'),                   'color(67)'],
    [re.compile(f'^{adobe_strings.RESOURCES}'),           'magenta'],
    [re.compile('/(Trailer|Root|Info|Outlines)'),         'bright_green'],
    [re.compile('/Catalog'),                              'color(47)'],
    [re.compile('/(Metadata|ViewerPreferences)'),         'color(35)'],
    [re.compile('^/Contents'),                            'medium_purple1'],
    [re.compile('^/Action'),                              'dark_red'],
    [re.compile('^/Annots'),                              'deep_sky_blue4'],
    [re.compile('^/Annot'),                               'color(24)'],
    [re.compile('^/Pages'),                               'dark_orange3'],
    [re.compile('^/Page'),                                'light_salmon3'],
    [re.compile('^/ColorSpace'),                          'medium_orchid1'],
    [re.compile('^/(URI|Names)'),                         'white'],
    [re.compile(f'^{adobe_strings.XOBJECT}'),             'grey37'],
    [re.compile(f'^{adobe_strings.UNLABELED}'),           'grey35 reverse'],
    [re.compile(f'^{adobe_strings.XREF}'),                'color(148)'],
]

LABEL_STYLES += [
    [re.compile(f'^{key}'), 'color(243)']
    for key in adobe_strings.NON_TREE_REFERENCES
]


# Main interface to Rich package output
# TODO move to rich_text_helper.py
console = Console(
    theme=PDFALYZER_THEME,
    color_system='256',
    highlight=False,
    width=CONSOLE_PRINT_WIDTH,
    record=True)


# Pretty Printer
pp = PrettyPrinter(
    indent=INDENT_DEPTH,
    width=PRETTY_PRINT_WIDTH,
    sort_dicts=True)


def print_section_header(headline: str) -> None:
    console.print("\n\n")
    console.print(Panel(headline, style='reverse'))
    console.print('')


def pypdf_class_name(obj: PdfObject) -> str:
    """Shortened name of type(obj), e.g. PyPDF2.generic._data_structures.ArrayObject becomes Array"""
    class_pkgs = type(obj).__name__.split('.')
    class_pkgs.reverse()
    return class_pkgs[0].removesuffix('Object')


def generate_hyphen_line(length=CONSOLE_PRINT_WIDTH, title=None):
    """e.g. '-----------------BEGIN-----------------'"""
    if title is None:
        return '-' * length

    side_hyphens = int((length - len(title)) / 2) * '-'
    line = side_hyphens + title + side_hyphens
    return line if len(line) == length else line + '-'


def get_label_style(label: str) -> str:
    """Lookup a style based on the label string"""
    return next((ls[1] for ls in LABEL_STYLES if ls[0].search(label)), DEFAULT_LABEL_STYLE)


def get_type_style(klass) -> str:
    """Style for various types of data (e.g. DictionaryObject)"""
    return next((TYPE_STYLES[t] for t in TYPE_STYLES.keys() if issubclass(klass, t)), None)


def get_node_type_style(obj):
    klass_string = pypdf_class_name(obj)

    if 'Dictionary' in klass_string:
        style = TYPE_STYLES[dict]
    elif 'EncodedStream' in klass_string:
        style = PDFALYZER_THEME.styles['bytes']
    elif 'Stream' in klass_string:
        style = PDFALYZER_THEME.styles['bytes_title']
    elif 'Text' in klass_string:
        style = PDFALYZER_THEME.styles['light_grey']
    elif 'Array' in klass_string:
        style = 'color(120)'
    else:
        style = 'bright_yellow'

    return f"{style} italic"


def get_type_string_style(klass) -> str:
    """Dim version of get_type_style() for non primitives, white for primitives"""
    if issubclass(klass, (str, Number)):
        return 'white'
    else:
        return f"{get_type_style(klass)} dim"


def console_print_with_fallback(_string, style=None):
    """Fallback to regular print() if there's a Markup issue"""
    try:
        console.print(_string, style=style)
    except MarkupError:
        console.print(f"Hit a bracket issue with rich.console printing, defaulting to plain print", style='warn')
        print(_string.plain if isinstance(_string, Text) else _string)


def list_to_string(_list: list, sep=', ') -> str:
    """Join elements of _list with sep"""
    return sep.join([str(item) for item in _list])
