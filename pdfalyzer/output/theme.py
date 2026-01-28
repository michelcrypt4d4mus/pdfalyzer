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

from pypdf.generic import (ArrayObject, ByteStringObject, EncodedStreamObject, IndirectObject,
     NullObject, StreamObject, TextStringObject)
from rich.highlighter import ReprHighlighter
from rich.panel import Panel
from rich.padding import Padding
from rich.theme import Theme
from yaralyzer.output.console import console
from yaralyzer.output.theme import BYTES_NO_DIM, YARALYZER_THEME_DICT
from yaralyzer.util.logging import log_console

from pdfalyzer.util import adobe_strings
from pdfalyzer.util.helpers.collections_helper import prefix_keys, safe_json
from pdfalyzer.util.helpers.rich_text_helper import vertically_padded_panel
from pdfalyzer.util.helpers.string_helper import regex_to_capture_group_label

ClassStyle = namedtuple('ClassStyle', ['cls', 'style'])

# For highlighting / naming styles
NODE_STYLE_PFX = 'pdf.'
PDF_OBJ_STYLE_PFX = 'pdfobj.'

# Colors / PDF object styles
DEFAULT_LABEL_STYLE = 'yellow'
DEFAULT_OBJ_TYPE_STYLE = 'bright_yellow'
FONT_FILE_BLUE = 'steel_blue1'
FONT_OBJ_BLUE = 'deep_sky_blue4 bold'
NULL_STYLE = 'grey23'
PAGE_OBJ_STYLE = 'light_salmon3'
PARENT_STYLE = 'violet'
PDF_ARRAY_STYLE = 'color(143)'  # color(120)
PDF_DICTIONARY_STYLE = 'color(64)'
PDF_NON_TREE_REF_STYLE = 'color(243)'
PDFALYZER_THEME_DICT = YARALYZER_THEME_DICT.copy()
RED_ALERT_BASE_STYLE = 'blink bold red'
TRAILER_OBJ_STYLE = 'chartreuse2'

PDFALYZER_THEME_DICT.update({
    'BOM': 'bright_green',
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
    'red_alert': f'{RED_ALERT_BASE_STYLE} reverse on white',
})

PDF_OBJ_TYPE_STYLES = [
    ClassStyle(IndirectObject, 'color(225)'),
    ClassStyle(ByteStringObject, YARALYZER_THEME_DICT['bytes.title']),
    ClassStyle(EncodedStreamObject, YARALYZER_THEME_DICT['bytes']),
    ClassStyle(StreamObject, BYTES_NO_DIM),
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
LABEL_STYLES_BASE: dict[str, str] = {
    '/AA':                                                      RED_ALERT_BASE_STYLE,
    adobe_strings.JAVASCRIPT:                                   RED_ALERT_BASE_STYLE,
    adobe_strings.JS:                                           RED_ALERT_BASE_STYLE,
    adobe_strings.OPEN_ACTION:                                  RED_ALERT_BASE_STYLE,
    '/Action':                                                 'dark_red',
    # Fonts
    adobe_strings.FONT_DESCRIPTOR:                             'cornflower_blue',
    f'{adobe_strings.FONT_FILE}':                              FONT_FILE_BLUE,
    f'{adobe_strings.FONT_FILE}2':                             FONT_FILE_BLUE,
    f'{adobe_strings.FONT_FILE}3':                             FONT_FILE_BLUE,
    '/FontName':                                               FONT_OBJ_BLUE,
    adobe_strings.FONT:                                        FONT_OBJ_BLUE,  # After other /Font styles so it matches after
    '/BaseFont':                                               FONT_OBJ_BLUE,
    adobe_strings.DESCENDANT_FONTS:                            f"{FONT_OBJ_BLUE} dim",
    '/CharProc':                                               'dark_cyan',
    adobe_strings.TO_UNICODE:                                  'grey30',
    adobe_strings.ENCODING:                                    YARALYZER_THEME_DICT['encoding.header'],
    adobe_strings.WIDTHS:                                      'color(67)',
    adobe_strings.W:                                           'color(67)',
    adobe_strings.RESOURCES:                                   'magenta',
    # Doc info
    '/Catalog':                                                'color(47)',
    adobe_strings.CONTENTS:                                    'medium_purple1',
    adobe_strings.TRAILER:                                     TRAILER_OBJ_STYLE,
    '/Root':                                                   TRAILER_OBJ_STYLE,
    '/Info':                                                   TRAILER_OBJ_STYLE,
    '/Outlines':                                               TRAILER_OBJ_STYLE,
    '/Metadata':                                              'color(35)',
    '/ViewerPreferences':                                     'color(35)',
    adobe_strings.OBJ_STM:                                     YARALYZER_THEME_DICT['bytes'],
    # Data nodes
    adobe_strings.ANNOTS:                                      'deep_sky_blue4',
    adobe_strings.ANNOT:                                       'color(24)',
    adobe_strings.NAMES:                                       'white',
    adobe_strings.NUMS:                                        'grey23',
    adobe_strings.UNLABELED:                                   'grey35 reverse',
    adobe_strings.XOBJECT:                                     'grey37',
    adobe_strings.XREF:                                        'color(148)',
    '/URI':                                                    'white',
    # Pages
    adobe_strings.PAGES:                                       'dark_orange3',
    adobe_strings.PAGE:                                        PAGE_OBJ_STYLE,
    adobe_strings.PG:                                          PAGE_OBJ_STYLE,
    adobe_strings.COLOR_SPACE:                                 'medium_orchid1',
    # Parents
    adobe_strings.PARENT:                                      PARENT_STYLE,
    adobe_strings.PARENT_TREE:                                 PARENT_STYLE,
    adobe_strings.PARENT_TREE_NEXT_KEY:                        PARENT_STYLE,
    # Booleans
    adobe_strings.FALSE:                                       'bright_red',
    adobe_strings.TRUE:                                        'green bold',
}

# Add styles for all NON_TREE_REFERENCES
LABEL_STYLES_BASE.update({
    non_tree_ref: PDF_NON_TREE_REF_STYLE
    for non_tree_ref in adobe_strings.NON_TREE_REFERENCES
})

# Compile regexes as keys
LABEL_STYLES = {re.compile(k): v for k, v in LABEL_STYLES_BASE.items()}

NODE_COLOR_THEME_DICT = {
    **{regex_to_capture_group_label(k): v for k, v in LABEL_STYLES.items()},
    **{regex_to_capture_group_label(re.compile(cs[0].__name__)): cs[1] for cs in PDF_OBJ_TYPE_STYLES},
}

CUSTOM_LOG_HIGHLIGHTS = {
    "array_obj": f"{PDF_ARRAY_STYLE} italic",
    "child": "orange3 bold",
    "dictionary_obj": f"{PDF_DICTIONARY_STYLE} italic",
    "indeterminate": 'bright_black',
    "indirect_object": 'light_coral',
    "node_type": 'honeydew2',
    "parent": PARENT_STYLE,
    "pypdf_line": "dim",
    "pypdf_prefix": "light_slate_gray",
    "relationship": 'light_pink4',
    "stream_object": 'light_slate_blue bold',
    # Overload default theme
    'call': 'magenta',
    'ipv4': 'cyan',
    'ipv6': 'cyan',
}

LOG_THEME_DICT = prefix_keys(
    ReprHighlighter.base_style,
    {**CUSTOM_LOG_HIGHLIGHTS, **NODE_COLOR_THEME_DICT},
)


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
COMPLETE_THEME_DICT = {**PDFALYZER_THEME_DICT, **LOG_THEME_DICT, **THEME_COLORS_FOR_SHOW_ONLY_DICT}
console.push_theme(Theme(COMPLETE_THEME_DICT))


def theme_json() -> str:
    theme_dicts = {
        'PDFALYZER_THEME_DICT': PDFALYZER_THEME_DICT,
        'LOG_THEME_DICT': LOG_THEME_DICT,
        'THEME_COLORS_FOR_SHOW_ONLY_DICT': THEME_COLORS_FOR_SHOW_ONLY_DICT,
        'COMPLETE_THEME_DICT': COMPLETE_THEME_DICT,
    }

    return safe_json(theme_dicts)


def debug_themes() -> None:
    log_console.print(vertically_padded_panel('All Theme Dicts'))
    log_console.print_json(theme_json(), indent=4, sort_keys=True)
