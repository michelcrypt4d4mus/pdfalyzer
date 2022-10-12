"""
Methods to help with the design of the output
"""
import re

from rich.panel import Panel
from yaralyzer.output.rich_console import console, console_width

from pdfalyzer.util import adobe_strings

HEADER_PADDING = (1, 1)
DEFAULT_LABEL_STYLE = 'yellow'
FONT_OBJ_BLUE = 'deep_sky_blue4 bold'
PDF_NON_TREE_REF = 'color(243)'

LABEL_STYLES = [
    [re.compile('JavaScript|JS|OpenAction', re.I | re.M), 'blink bold red'],
    [re.compile(f'^{adobe_strings.FONT_DESCRIPTOR}'),     'cornflower_blue'],
    [re.compile(f'^{adobe_strings.FONT_FILE}'),           'steel_blue1'],
    [re.compile(f'^{adobe_strings.FONT}'),                FONT_OBJ_BLUE],
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
    [re.compile(f'^{key}'), PDF_NON_TREE_REF]
    for key in adobe_strings.NON_TREE_REFERENCES
]


def subheading_width() -> int:
    return int(console_width() * 0.75)


def half_width() -> int:
    return int(console_width() * 0.5)


def print_section_header(headline: str, style: str = '') -> None:
    console.line(2)
    _print_header_panel(headline, f"{style} reverse", True, console_width(), HEADER_PADDING)
    console.line()


def print_section_subheader(headline: str, style: str = '') -> None:
    console.line()
    _print_header_panel(headline, style, True, subheading_width(), HEADER_PADDING)


def print_section_sub_subheader(headline: str, style: str = ''):
    console.line()
    _print_header_panel(headline, style, True, half_width())


def print_headline_panel(headline, style: str = ''):
    _print_header_panel(headline, style, False, console_width())


def _print_header_panel(headline: str, style: str, expand: bool, width: int, padding: tuple = (0,)) -> None:
    console.print(Panel(headline, style=style, expand=expand, width=width or subheading_width(), padding=padding))


def get_label_style(label: str) -> str:
    """Lookup a style based on the label string"""
    return next((ls[1] for ls in LABEL_STYLES if ls[0].search(label)), DEFAULT_LABEL_STYLE)
