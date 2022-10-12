"""
Rich colors: https://rich.readthedocs.io/en/stable/appendix/colors.html
TODO: interesting colors # row_styles[0] = 'reverse bold on color(144)' <-
"""
import re
import time
from numbers import Number
from os import path
from typing import List, Union

from PyPDF2.generic import ByteStringObject, IndirectObject
from rich import box
from rich.columns import Columns
from rich.padding import Padding
from rich.panel import Panel
from rich.style import Style
from rich.table import Table
from rich.text import Text
from rich.theme import Theme
from yaralyzer.output.rich_console import GREY_ADDRESS, YARALYZER_THEME_DICT, console
from yaralyzer.helpers.rich_text_helper import prefix_with_plain_text_obj
from yaralyzer.util.logging import log, log_and_print

from pdfalyzer.helpers.dict_helper import merge

# Colors
DANGER_HEADER = 'color(88) on white'  # Red

# PDF object styles
PDF_ARRAY = 'color(120)'
PDF_NON_TREE_REF = 'color(243)'

PDFALYZER_THEME_DICT = YARALYZER_THEME_DICT.copy()
PDFALYZER_THEME_DICT.update({
    'address': GREY_ADDRESS,
    'BOM': 'bright_green',
    # PDF objects
    'pdf.array': PDF_ARRAY,
    'pdf.non_tree_ref': PDF_NON_TREE_REF,
    # fonts
    'font.property': 'color(135)',
    'font.title': 'reverse dark_blue on color(253)',
    # charmap
    'charmap.title': 'color(18) reverse on white dim',
    'charmap.prepared_title': 'color(23) reverse on white dim',
    'charmap.prepared': 'color(106) dim',
    'charmap.byte': 'color(58)',
    'charmap.char': 'color(120) bold',
    # design elements
    'subtable': 'color(8) on color(232)',
    'header.minor': 'color(249) bold',
    'header.danger': DANGER_HEADER,
    'header.danger_reverse': f'{DANGER_HEADER} reverse',
    # neutral log events
    'event.attn': 'bold bright_cyan',
    'event.lowpriority': 'bright_black',
    # good log events
    'event.good': 'green4',
    'event.better': 'turquoise4',
    'event.reallygood': 'dark_cyan',
    'event.reallygreat': 'spring_green1',
    'event.great': 'sea_green2',
    'event.evenbetter': 'chartreuse1',
    'event.best': 'green1',
    'event.siren': 'blink bright_white on red3',
    # warn log events
    'warn': 'bright_yellow',
    'warn.mild': 'yellow2',
    'warn.milder': 'dark_orange3',
    'warn.harsh': 'reverse bright_yellow',
    # error log events
    'fail': 'bold reverse red',
    'milderror': 'red',
    'red_alert': 'blink bold red reverse on white',
})

console.push_theme(Theme(PDFALYZER_THEME_DICT))


TYPE_STYLES = {
    Number: 'bright_cyan bold',
    dict: 'color(64)',
    list: 'color(143)',
    str: 'bright_white bold',
    IndirectObject: 'color(157)',
    ByteStringObject: 'bytes',
}

# Color meter realted constants. Make even sized buckets color coded from blue (cold) to green (go)
METER_COLORS = list(reversed([82, 85, 71, 60, 67, 30, 24, 16]))
METER_INTERVAL = (100 / float(len(METER_COLORS))) + 0.1

# Color meter extra style thresholds (these are assuming a scale of 0-100)
UNDERLINE_CONFIDENCE_THRESHOLD = 90
BOLD_CONFIDENCE_THRESHOLD = 60
DIM_COUNTRY_THRESHOLD = 25

# Table stuff
DEFAULT_SUBTABLE_COL_STYLES = ['white', 'bright_white']
HEADER_PADDING = (1, 1)

# For the table shown by running pdfalyzer_show_color_theme
MAX_THEME_COL_SIZE = 35

# Text object defaults mostly for table entries
NOT_FOUND_MSG = Text('(not found)', style='grey.dark_italic')


def get_type_style(klass) -> str:
    """Style for various types of data (e.g. DictionaryObject)"""
    return next((TYPE_STYLES[t] for t in TYPE_STYLES.keys() if issubclass(klass, t)), None)


def get_type_string_style(klass) -> str:
    """Dim version of get_type_style() for non primitives, white for primitives"""
    if issubclass(klass, (str, Number)):
        return 'white'
    else:
        return f"{get_type_style(klass)} dim"


def generate_subtable(cols, header_style='subtable') -> Table:
    """Suited for lpacement in larger tables"""
    table = Table(
        box=box.SIMPLE,
        show_edge=False,
        collapse_padding=True,
        header_style=header_style,
        show_lines=False,
        border_style='grey.dark',
        expand=True)

    for i, col in enumerate(cols):
        if i + 1 < len(cols):
            table.add_column(col, style=DEFAULT_SUBTABLE_COL_STYLES[0], justify='left')
        else:
            table.add_column(col, style='off_white', justify='right')

    return table


def pad_header(header: str) -> Padding:
    """Would pad anything, not just headers"""
    return Padding(header, HEADER_PADDING)


def pdfalyzer_show_color_theme() -> None:
    """Utility method to show pdfalyzer's color theme. Invocable with 'pdfalyzer_show_colors'."""
    console.print(Panel('The Pdfalyzer Color Theme', style='reverse'))

    colors = [
        prefix_with_plain_text_obj(name[:MAX_THEME_COL_SIZE], style=str(style)).append(' ')
        for name, style in PDFALYZER_THEME_DICT.items()
        if name not in ['reset', 'repr_url']
    ]

    console.print(Columns(colors, column_first=True, padding=(0,3)))
