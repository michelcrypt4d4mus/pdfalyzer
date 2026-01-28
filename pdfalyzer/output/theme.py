"""
Color theme for pdfalyzer including functions to help decide on node colors etc.

Rich colors: https://rich.readthedocs.io/en/stable/appendix/colors.html
TODO: interesting colors # row_styles[0] = 'reverse bold on color(144)' <-
"""
import re
from collections import namedtuple
from numbers import Number
from types import NoneType
from typing import Any

from pdfalyzer.helpers.string_helper import regex_to_capture_group_label
from pdfalyzer.util import adobe_strings
from pypdf.generic import (ArrayObject, ByteStringObject, EncodedStreamObject, IndirectObject,
     NullObject, StreamObject, TextStringObject)
from rich.theme import Theme
from yaralyzer.output.console import console
from yaralyzer.output.theme import YARALYZER_THEME_DICT

ClassStyle = namedtuple('ClassStyle', ['cls', 'style'])

# For highlighting / naming styles
NODE_STYLE_PFX = 'pdf.'
PDF_OBJ_STYLE_PFX = 'pdfobj.'

# Colors / PDF object styles
DEFAULT_LABEL_STYLE = 'yellow'
DEFAULT_OBJ_TYPE_STYLE = 'bright_yellow'
FONT_OBJ_BLUE = 'deep_sky_blue4 bold'
NULL_STYLE = 'grey23'
PARENT_STYLE = 'violet'
PDF_ARRAY_STYLE = 'color(143)'  # color(120)
PDF_DICTIONARY_STYLE = 'color(64)'
PDF_NON_TREE_REF_STYLE = 'color(243)'
PDFALYZER_THEME_DICT = YARALYZER_THEME_DICT.copy()

PDFALYZER_THEME_DICT.update({
    'BOM': 'bright_green',
    # PDF objects
    'pdf.array': PDF_ARRAY_STYLE,
    # fonts
    'font.property': 'color(135)',
    'font.title': 'reverse dark_blue on color(253)',
    # charmap
    'charmap.title': 'color(25)',
    'charmap.prepared_title': 'color(23)',
    'charmap.prepared': 'color(106) dim',
    'charmap.byte': 'color(58)',
    'charmap.char': 'color(120) bold',
    # design elements
    'subtable': 'color(8) on color(232)',
    # warn log events
    'warn': 'bright_yellow',
    # error log events
    'mild_warning': 'color(228) dim',
    'red_alert': 'blink bold red reverse on white',
})

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

# Order matters - first match will be the style
LABEL_STYLES_BASE = {
    re.compile(r'(AA|JavaScript|JS|OpenAction)', re.I | re.M): 'blink bold red',
    adobe_strings.FONT_DESCRIPTOR:    'cornflower_blue',
    fr'{adobe_strings.FONT_FILE}\d?':       'steel_blue1',
    f'/(Font(Name)?|BaseFont)':             FONT_OBJ_BLUE,
    adobe_strings.DESCENDANT_FONTS:                    f"{FONT_OBJ_BLUE} dim",
    f'/CharProc':                            'dark_cyan',
    adobe_strings.TO_UNICODE:         'grey30',
    adobe_strings.ENCODING:            YARALYZER_THEME_DICT['encoding.header'],
    adobe_strings.WIDTHS:             'color(67)',
    adobe_strings.W:                  'color(67)',
    adobe_strings.RESOURCES:          'magenta',
    r'/(Trailer|Root|Info|Outlines)':        'bright_green',
    r'/Catalog':                             'color(47)',
    '/(Metadata|ViewerPreferences)':         'color(35)',
    adobe_strings.OBJ_STM:            YARALYZER_THEME_DICT['bytes'],
    adobe_strings.NUMS:               'grey23',
    adobe_strings.CONTENTS:                            'medium_purple1',
    '/Action':                              'dark_red',
    adobe_strings.ANNOTS:                              'deep_sky_blue4',
    adobe_strings.ANNOT:                               'color(24)',
    adobe_strings.PAGES:                               'dark_orange3',
    '/(Page|Pg)':                           'light_salmon3',
    adobe_strings.COLOR_SPACE:                          'medium_orchid1',
    '/(URI|Names)':                         'white',
    adobe_strings.XOBJECT:            'grey37',
    adobe_strings.UNLABELED:          'grey35 reverse',
    adobe_strings.XREF:               'color(148)',
    fr'/Parent(Tree(NextKey)?)?':            PARENT_STYLE,
    adobe_strings.FALSE:                     'bright_red',
    adobe_strings.TRUE:                      'green bold',
}

# Add styles for all NON_TREE_REFERENCES
LABEL_STYLES_BASE.update({
    key: PDF_NON_TREE_REF_STYLE
    for key in adobe_strings.NON_TREE_REFERENCES
})

# Compile regexes as keys
LABEL_STYLES = {
    (k if isinstance(k, re.Pattern) else re.compile(k)): v
    for k, v in LABEL_STYLES_BASE.items()
}

NODE_COLOR_THEME_DICT = {
    **{regex_to_capture_group_label(k): v for k, v in LABEL_STYLES.items()},
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
    return next((v for k, v in LABEL_STYLES.items() if k.match(label)), DEFAULT_LABEL_STYLE)


# TODO: Right now NODE_COLOR_THEME_DICT is the real action. These need to be integrated into the main theme.
THEME_COLORS_FOR_SHOW_ONLY_DICT = {}

for style_regex in LABEL_STYLES.keys():
    patterns = [regex_to_capture_group_label(p) for p in style_regex.pattern.strip().split('|')]

    for obj_type in patterns:
        THEME_COLORS_FOR_SHOW_ONLY_DICT[f"{NODE_STYLE_PFX}{obj_type}"] = LABEL_STYLES[style_regex]

for cls_style in PDF_OBJ_TYPE_STYLES:
    THEME_COLORS_FOR_SHOW_ONLY_DICT[f"{PDF_OBJ_STYLE_PFX}{cls_style.cls.__name__}"] = cls_style.style


# Override whatever theme The Yaralyzer has configured.
console.push_theme(Theme(PDFALYZER_THEME_DICT))
