"""
Color theme for pdfalyzer including functions to help decide on node colors etc.

Rich colors: https://rich.readthedocs.io/en/stable/appendix/colors.html
TODO: interesting colors # row_styles[0] = 'reverse bold on color(144)' <-
"""
import re
import sys
from collections import namedtuple
from numbers import Number
from types import NoneType
from typing import Any

from pypdf.generic import (ArrayObject, ByteStringObject, DictionaryObject, EncodedStreamObject,
     IndirectObject, NullObject, StreamObject, TextStringObject)
from rich.theme import Theme
from yaralyzer.output.console import console
from yaralyzer.output.theme import BYTES_NO_DIM, YARALYZER_THEME_DICT
from yaralyzer.util.logging import log_console

from pdfalyzer.output.highlighter import (CHILD_STYLE, INDIRECT_OBJ_STYLE, LOG_HIGHLIGHT_PATTERNS,
     LOG_HIGHLIGHT_STYLES, PARENT_STYLE, PDF_ARRAY_STYLE, PDF_DICTIONARY_STYLE, LogHighlighter, PdfHighlighter)
from pdfalyzer.util import adobe_strings
from pdfalyzer.util.helpers.collections_helper import safe_json
from pdfalyzer.util.helpers.rich_helper import vertically_padded_panel
from pdfalyzer.util.helpers.string_helper import highlight_pattern

ClassStyle = namedtuple('ClassStyle', ['cls', 'style'])

# For highlighting / naming styles
PDF_OBJ_STYLE_PFX = 'pdfobj.'

# Colors / PDF object styles
DEFAULT_LABEL_STYLE = 'yellow'
DEFAULT_OBJ_TYPE_STYLE = 'bright_yellow'
FONT_FILE_BLUE = 'steel_blue1'
FONT_OBJ_BLUE = 'deep_sky_blue4 bold'
INFO_OBJ_STYLE = 'yellow4'
LINK_OBJ_STYLE = 'grey46'
METADATA_STYLE = 'color(35)'
NULL_STYLE = 'grey23'
PAGE_OBJ_STYLE = 'light_salmon3'
PDF_NON_TREE_REF_STYLE = 'color(243)'  # grey46?
RED_ALERT_BASE_STYLE = 'blink bold red'
TRAILER_OBJ_STYLE = 'chartreuse2'
TYPE_KEY_STYLE = 'honeydew2'

PDFALYZER_THEME_DICT = {
    **YARALYZER_THEME_DICT,
    'bytes.BOM': 'bright_green',
    # charmap
    'charmap.title': 'color(25)',
    'charmap.prepared_title': 'color(23)',
    'charmap.prepared': 'color(106) dim',
    'charmap.byte': 'color(58)',
    'charmap.char': 'color(120) bold',
    # fonts
    'font.property': 'color(135)',
    'font.title': 'reverse dark_blue on color(253)',
    # design elements
    'subtable': 'color(8) on color(232)',
    # warn log events
    'warn': 'bright_yellow',
    # error log events
    'red_alert': f'{RED_ALERT_BASE_STYLE} reverse on white',
}

PDF_OBJ_TYPE_STYLES = [
    ClassStyle(IndirectObject, INDIRECT_OBJ_STYLE),
    ClassStyle(ByteStringObject, YARALYZER_THEME_DICT['bytes.title']),
    ClassStyle(EncodedStreamObject, YARALYZER_THEME_DICT['bytes']),
    ClassStyle(StreamObject, BYTES_NO_DIM),
    ClassStyle(TextStringObject, YARALYZER_THEME_DICT['grey.light']),
    ClassStyle(ArrayObject, PDF_ARRAY_STYLE),
    ClassStyle(DictionaryObject, PDF_DICTIONARY_STYLE),
    ClassStyle(NullObject, NULL_STYLE),
    ClassStyle(NoneType, NULL_STYLE),
]

PDF_OBJ_TYPE_STYLE_DICT = {f"{cs.cls.__name__}": cs.style for cs in PDF_OBJ_TYPE_STYLES}

# Subclasses of the key type will be styled with the value string
OBJ_TYPE_STYLES = PDF_OBJ_TYPE_STYLES + [
    ClassStyle(Number, 'cyan bold'),
    ClassStyle(dict, PDF_DICTIONARY_STYLE),
    ClassStyle(list, PDF_ARRAY_STYLE),
    ClassStyle(tuple, PDF_ARRAY_STYLE),
    ClassStyle(str, 'bright_white bold'),
]

# Add styles for all NON_TREE_REFERENCES first because /OpenAction is one such action
NODE_STYLES_BASE_DICT = {
    key: PDF_NON_TREE_REF_STYLE
    for key in (adobe_strings.NON_TREE_REFERENCES + adobe_strings.LINK_NODE_KEYS + [adobe_strings.FIRST])
}

# Order matters - first match will be the style
NODE_STYLES_BASE_DICT.update({
    adobe_strings.AA:                                          RED_ALERT_BASE_STYLE,
    adobe_strings.JAVASCRIPT:                                  RED_ALERT_BASE_STYLE,
    adobe_strings.JS:                                          RED_ALERT_BASE_STYLE,
    adobe_strings.OPEN_ACTION:                                 RED_ALERT_BASE_STYLE,
    adobe_strings.GO_TO_R:                                     RED_ALERT_BASE_STYLE,
    '/Action':                                                 'red',
    # Fonts
    adobe_strings.FONT_DESCRIPTOR:                             'cornflower_blue',
    f'{adobe_strings.FONT_FILE}':                              FONT_FILE_BLUE,
    f'{adobe_strings.FONT_FILE}2':                             FONT_FILE_BLUE,
    f'{adobe_strings.FONT_FILE}3':                             FONT_FILE_BLUE,
    '/FontName':                                               FONT_OBJ_BLUE,
    adobe_strings.FONT:                                        FONT_OBJ_BLUE,  # After /Fontetc so it matches after
    '/BaseFont':                                               FONT_OBJ_BLUE,
    adobe_strings.DESCENDANT_FONTS:                            f"{FONT_OBJ_BLUE} dim",
    '/CharProc':                                               'dark_cyan',
    adobe_strings.TO_UNICODE:                                  'grey30',
    adobe_strings.ENCODING:                                    YARALYZER_THEME_DICT['encoding.header'],
    adobe_strings.WIDTHS:                                      'color(67)',
    adobe_strings.W:                                           'color(67)',
    adobe_strings.RESOURCES:                                   'magenta',
    # Top level nodes
    '/Root':                                                   TRAILER_OBJ_STYLE,
    adobe_strings.CATALOG:                                     'color(47)',
    adobe_strings.CONTENTS:                                    'medium_purple1',
    adobe_strings.TRAILER:                                     TRAILER_OBJ_STYLE,
    adobe_strings.INFO:                                        INFO_OBJ_STYLE,
    adobe_strings.OUTLINES:                                    INFO_OBJ_STYLE,
    adobe_strings.METADATA:                                    METADATA_STYLE,
    '/ViewerPreferences':                                      METADATA_STYLE,
    adobe_strings.OBJ_STM:                                     YARALYZER_THEME_DICT['bytes'],
    # Data nodes
    adobe_strings.ANNOTS:                                      'deep_sky_blue4',
    adobe_strings.ANNOT:                                       'color(24)',
    adobe_strings.NAMES:                                       'white',
    adobe_strings.NUMS:                                        'grey23',
    adobe_strings.UNLABELED:                                   'grey35 reverse',
    adobe_strings.XOBJECT:                                     'grey37',
    adobe_strings.XREF:                                        'color(148)',
    # Images
    adobe_strings.IMAGE:                                       'medium_violet_red',
    adobe_strings.URI:                                         'color(244)',
    # Pages
    adobe_strings.PAGES:                                       'dark_orange3',
    adobe_strings.PAGE:                                        PAGE_OBJ_STYLE,
    adobe_strings.PG:                                          PAGE_OBJ_STYLE,
    adobe_strings.COLOR_SPACE:                                 'medium_orchid1',
    # Parents
    adobe_strings.KIDS:                                        CHILD_STYLE,
    adobe_strings.PARENT:                                      PARENT_STYLE,
    adobe_strings.PARENT_TREE:                                 PARENT_STYLE,
    adobe_strings.PARENT_TREE_NEXT_KEY:                        PARENT_STYLE,
    adobe_strings.STRUCT_PARENT:                               PARENT_STYLE,
    # Booleans
    adobe_strings.FALSE:                                       'bright_red',
    adobe_strings.TRUE:                                        'green bold',
    # /Type fields
    adobe_strings.SUBTYPE:                                     TYPE_KEY_STYLE,
    adobe_strings.TYPE:                                        TYPE_KEY_STYLE,
})

# Compile regexes as keys
NODE_STYLE_REGEXES = {re.compile(k): v for k, v in NODE_STYLES_BASE_DICT.items()}
# Collect regexes for both PDF types (DictionaryObject) as well as nodes (/Trailer)
PDF_HIGHLIGHT_PATTERNS = [pattern for pattern in {**NODE_STYLE_REGEXES, **PDF_OBJ_TYPE_STYLE_DICT}.keys()]

# Unite class styles for things like ArrayObject with node styles for things like /Parent
NODE_STYLES_THEME_DICT = {
    **PdfHighlighter.prefix_styles({k.removeprefix('/'): v for k, v in NODE_STYLES_BASE_DICT.items()}),
    **PdfHighlighter.prefix_styles(PDF_OBJ_TYPE_STYLE_DICT)
}

# Merge all the theme dicts
LOG_THEME_DICT = LogHighlighter.prefix_styles(LOG_HIGHLIGHT_STYLES)
COMPLETE_THEME_DICT = {**PDFALYZER_THEME_DICT, **LOG_THEME_DICT, **NODE_STYLES_THEME_DICT}


# Add patterns to highlighters
# TODO: currently using PdfHighlighter for log highlights, LogHighlighter only for pypdf logs
LogHighlighter.set_highlights(LOG_HIGHLIGHT_PATTERNS)
PdfHighlighter.set_highlights([highlight_pattern(r) for r in PDF_HIGHLIGHT_PATTERNS])

# Push themes into the console objects that manage stdout.
console.push_theme(Theme(COMPLETE_THEME_DICT))
log_console.push_theme(Theme(COMPLETE_THEME_DICT))


def get_class_style(obj: Any) -> str:
    """Style for various types of data (e.g. DictionaryObject)"""
    if obj is True:
        cls_style = 'bright_green bold'
    elif obj is False:
        cls_style = 'bright_red bold'
    else:
        cls_style = next((cs.style for cs in OBJ_TYPE_STYLES if isinstance(obj, cs.cls)), DEFAULT_OBJ_TYPE_STYLE)

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
    return next((v for k, v in NODE_STYLE_REGEXES.items() if k.match(label)), DEFAULT_LABEL_STYLE)


def theme_json() -> str:
    theme_dicts = {
        'COMPLETE_THEME_DICT': COMPLETE_THEME_DICT,
        'LOG_THEME_DICT': LOG_THEME_DICT,
        'NODE_STYLES_THEME_DICT': NODE_STYLES_THEME_DICT,
        'PDFALYZER_THEME_DICT': PDFALYZER_THEME_DICT,
    }

    return safe_json(theme_dicts)


def _debug_themes() -> None:
    LogHighlighter._debug_highlight_patterns()
    PdfHighlighter._debug_highlight_patterns()
    log_console.print(vertically_padded_panel('All Theme Dicts'))
    log_console.print_json(theme_json(), indent=4, sort_keys=True)


if '--show-colors' in sys.argv and '--debug' in sys.argv:
    _debug_themes()
