"""
Configurations and methods to help with consistent styling of PDF trees, nodes, etc.
"""
import re
from collections import namedtuple
from numbers import Number
from types import NoneType
from typing import Any

from pypdf.generic import (ArrayObject, ByteStringObject, EncodedStreamObject, IndirectObject,
     NullObject, StreamObject, TextStringObject)
from yaralyzer.output.theme import YARALYZER_THEME_DICT
from yaralyzer.util.logging import log_console

from pdfalyzer.helpers.string_helper import regex_to_capture_group_label
from pdfalyzer.output.styles.rich_theme import PDF_ARRAY_STYLE
from pdfalyzer.util import adobe_strings

ClassStyle = namedtuple('ClassStyle', ['cls', 'style'])

DEFAULT_LABEL_STYLE = 'yellow'
DEFAULT_OBJ_TYPE_STYLE = 'bright_yellow'
FONT_OBJ_BLUE = 'deep_sky_blue4 bold'
NULL_STYLE = 'grey23'
PDF_NON_TREE_REF = 'color(243)'
PARENT_STYLE = 'violet'

NODE_STYLE_PFX = 'pdf.'
PDF_OBJ_STYLE_PFX = 'pdfobj.'

PDF_OBJ_TYPE_STYLES = [
    ClassStyle(IndirectObject, 'color(225)'),
    ClassStyle(ByteStringObject, YARALYZER_THEME_DICT['bytes']),
    ClassStyle(EncodedStreamObject, YARALYZER_THEME_DICT['bytes']),
    ClassStyle(StreamObject, YARALYZER_THEME_DICT['bytes.title']),
    ClassStyle(TextStringObject, YARALYZER_THEME_DICT['grey.light']),
    ClassStyle(ArrayObject, PDF_ARRAY_STYLE),
    ClassStyle(NullObject, NULL_STYLE),
    ClassStyle(NoneType, NULL_STYLE),
]

# Subclasses of the key type will be styled with the value string
OBJ_TYPE_STYLES = PDF_OBJ_TYPE_STYLES + [
    ClassStyle(Number, 'cyan bold'),
    ClassStyle(dict, 'color(64)'),
    ClassStyle(list, PDF_ARRAY_STYLE),
    ClassStyle(tuple, PDF_ARRAY_STYLE),
    ClassStyle(str, 'bright_white bold'),
]

LABEL_STYLES = [
    [re.compile(r'(AA|JavaScript|JS|OpenAction)', re.I | re.M), 'blink bold red'],
    [re.compile(fr'{adobe_strings.FONT_DESCRIPTOR}'),    'cornflower_blue'],
    [re.compile(fr'{adobe_strings.FONT_FILE}\d?'),       'steel_blue1'],
    [re.compile(f'/(Font(Name)?|BaseFont)'),             FONT_OBJ_BLUE],
    [re.compile(f'/DescendantFonts'),                    f"{FONT_OBJ_BLUE} dim"],
    [re.compile(f'/CharProc'),                            'dark_cyan'],
    [re.compile(fr'{adobe_strings.TO_UNICODE}'),         'grey30'],
    [re.compile(fr'{adobe_strings.ENCODING}'),            YARALYZER_THEME_DICT['encoding.header']],
    [re.compile(fr'{adobe_strings.WIDTHS}'),             'color(67)'],
    [re.compile(fr'{adobe_strings.W}'),                  'color(67)'],
    [re.compile(fr'{adobe_strings.RESOURCES}'),          'magenta'],
    [re.compile(r'/(Trailer|Root|Info|Outlines)'),        'bright_green'],
    [re.compile(r'/Catalog'),                             'color(47)'],
    [re.compile('/(Metadata|ViewerPreferences)'),         'color(35)'],
    [re.compile(fr"{adobe_strings.OBJ_STM}"),            YARALYZER_THEME_DICT['bytes']],
    [re.compile(fr"{adobe_strings.NUMS}"),               'grey23'],
    [re.compile('/Contents'),                            'medium_purple1'],
    [re.compile('/Action'),                              'dark_red'],
    [re.compile('/Annots'),                              'deep_sky_blue4'],
    [re.compile('/Annot'),                               'color(24)'],
    [re.compile('/Pages'),                               'dark_orange3'],
    [re.compile('/(Page|Pg)'),                           'light_salmon3'],
    [re.compile('/ColorSpace'),                          'medium_orchid1'],
    [re.compile('/(URI|Names)'),                         'white'],
    [re.compile(fr'{adobe_strings.XOBJECT}'),            'grey37'],
    [re.compile(fr'{adobe_strings.UNLABELED}'),          'grey35 reverse'],
    [re.compile(fr'{adobe_strings.XREF}'),               'color(148)'],
    [re.compile(fr'/Parent(Tree(NextKey)?)?'),            PARENT_STYLE],
    [re.compile(adobe_strings.FALSE),                     'bright_red'],
    [re.compile(adobe_strings.TRUE),                      'green bold'],
]

# Add styles for all NON_TREE_REFERENCES
LABEL_STYLES += [
    [re.compile(f'{key}'), PDF_NON_TREE_REF]
    for key in adobe_strings.NON_TREE_REFERENCES
]

NODE_COLOR_THEME_DICT = {
    **{regex_to_capture_group_label(label_style[0]): label_style[1] for label_style in LABEL_STYLES},
    **{regex_to_capture_group_label(re.compile(cs[0].__name__)): cs[1] for cs in PDF_OBJ_TYPE_STYLES},
}


def get_class_style(obj: Any) -> str:
    """Style for various types of data (e.g. DictionaryObject)"""
    if obj is True:
        cls_style = 'bright_green bold'
    elif obj is False:
        cls_style = 'bright_red bold'
    else:
        cls_style = next((cs.style for cs in OBJ_TYPE_STYLES if isinstance(obj, cs.cls)), DEFAULT_OBJ_TYPE_STYLE)

    if cls_style == DEFAULT_OBJ_TYPE_STYLE:
        #log_console.print(f"Style FAIL: {type(obj).__name__} style resolved as {cls_style}", style=cls_style)
        pass

    return cls_style


def get_class_style_dim(obj: Any) -> str:
    """Dim version of get_class_style() for non primitives, white for primitives"""
    if isinstance(obj, str):
        return 'color(244)'
    elif isinstance(obj, Number):
        cls_style = get_class_style(obj).replace('bold', '').strip()
    else:
        cls_style = get_class_style(obj)

    return f"{cls_style} dim"


def get_class_style_italic(obj: Any) -> str:
    return f"{get_class_style(obj)} italic"


def get_label_style(label: str) -> str:
    """Lookup a style based on the node's label string (either its type or first address)."""
    return next((ls[1] for ls in LABEL_STYLES if ls[0].match(label)), DEFAULT_LABEL_STYLE)


# TODO: Right now NODE_COLOR_THEME_DICT is the real action. These need to be integrated into the main theme.
THEME_COLORS_FOR_SHOW_ONLY_DICT = {}

for label_style in LABEL_STYLES:
    patterns = [regex_to_capture_group_label(p) for p in label_style[0].pattern.strip().split('|')]

    for obj_type in patterns:
        THEME_COLORS_FOR_SHOW_ONLY_DICT[f"{NODE_STYLE_PFX}{obj_type}"] = label_style[1]

for cls_style in PDF_OBJ_TYPE_STYLES:
    THEME_COLORS_FOR_SHOW_ONLY_DICT[f"{PDF_OBJ_STYLE_PFX}{cls_style.cls.__name__}"] = cls_style.style
