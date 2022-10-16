"""
Rich colors: https://rich.readthedocs.io/en/stable/appendix/colors.html
TODO: interesting colors # row_styles[0] = 'reverse bold on color(144)' <-
"""
import re
from numbers import Number
from os import path
from typing import List, Union

from PyPDF2.generic import ByteStringObject, IndirectObject
from rich.text import Text
from rich.theme import Theme
from yaralyzer.output.rich_console import GREY_ADDRESS, YARALYZER_THEME_DICT, console
from yaralyzer.util.logging import log

from pdfalyzer.util import adobe_strings

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


def get_label_style(label: str) -> str:
    """Lookup a style based on the label string"""
    return next((ls[1] for ls in LABEL_STYLES if ls[0].search(label)), DEFAULT_LABEL_STYLE)


def quoted_text(_string, style: Union[str, None]=None, quote_char_style='white', quote_char="'") -> Text:
    quote_char = Text(quote_char, style=quote_char_style)
    txt = quote_char + Text(_string, style=style or '') + quote_char
    txt.justify = 'center'
    return txt
