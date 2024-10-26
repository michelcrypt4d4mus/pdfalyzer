"""
Configurations and methods to help with consistent styling of PDF trees, nodes, etc.
"""
import re
from collections import namedtuple
from numbers import Number
from typing import Any

from pypdf.generic import (ArrayObject, ByteStringObject, EncodedStreamObject, IndirectObject,
     StreamObject, TextStringObject)
from yaralyzer.output.rich_console import YARALYZER_THEME_DICT

from pdfalyzer.output.styles.rich_theme import PDF_ARRAY
from pdfalyzer.util import adobe_strings

ClassStyle = namedtuple('ClassStyle', ['klass', 'style'])

DEFAULT_LABEL_STYLE = 'yellow'
FONT_OBJ_BLUE = 'deep_sky_blue4 bold'
PDF_NON_TREE_REF = 'color(243)'

# Subclasses of the key type will be styled with the value string
NODE_TYPE_STYLES = [
    ClassStyle(Number, 'cyan bold'),
    ClassStyle(IndirectObject, 'color(225)'),
    ClassStyle(ByteStringObject, 'bytes'),
    ClassStyle(EncodedStreamObject, YARALYZER_THEME_DICT['bytes']),
    ClassStyle(StreamObject, YARALYZER_THEME_DICT['bytes.title']),
    ClassStyle(TextStringObject, YARALYZER_THEME_DICT['grey.light']),
    ClassStyle(ArrayObject, PDF_ARRAY),
    ClassStyle(dict, 'color(64)'),
    ClassStyle(list, 'color(143)'),
    ClassStyle(str, 'bright_white bold'),
    # Default
    ClassStyle(object, 'bright_yellow'),
]

LABEL_STYLES = [
    [re.compile('JavaScript|JS|OpenAction', re.I | re.M), 'blink bold red'],
    [re.compile(f'^{adobe_strings.FONT_DESCRIPTOR}'),     'cornflower_blue'],
    [re.compile(f'^{adobe_strings.FONT_FILE}'),           'steel_blue1'],
    [re.compile(f'^{adobe_strings.FONT}'),                FONT_OBJ_BLUE],
    [re.compile(f'^{adobe_strings.TO_UNICODE}'),          'grey30'],
    [re.compile(f'^{adobe_strings.ENCODING}'),            YARALYZER_THEME_DICT['encoding.header']],
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

# Add common color for all NON_TREE_REFERENCES
LABEL_STYLES += [
    [re.compile(f'^{key}'), PDF_NON_TREE_REF]
    for key in adobe_strings.NON_TREE_REFERENCES
]


def get_class_style(obj: Any) -> str:
    """Style for various types of data (e.g. DictionaryObject)"""
    return next((cs.style for cs in NODE_TYPE_STYLES if isinstance(obj, cs.klass)), '')


def get_class_style_dim(obj: Any) -> str:
    """Dim version of get_class_style() for non primitives, white for primitives"""
    if isinstance(obj, str):
        return 'color(244)'
    elif isinstance(obj, Number):
        return 'cyan dim'
    else:
        return f"{get_class_style(obj)} dim"


def get_class_style_italic(obj: Any) -> str:
    return f"{get_class_style(obj)} italic"


def get_label_style(label: str) -> str:
    """Lookup a style based on the node's label string (either its type or first address)."""
    return next((ls[1] for ls in LABEL_STYLES if ls[0].search(label)), DEFAULT_LABEL_STYLE)
