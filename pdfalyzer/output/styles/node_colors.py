"""
Configurations and methods to help with consistent styling of PDF trees, nodes, etc.
"""
import re
from numbers import Number

from PyPDF2.generic import ByteStringObject, IndirectObject
from yaralyzer.output.rich_console import YARALYZER_THEME_DICT

from pdfalyzer.helpers.pdf_object_helper import pypdf_class_name
from pdfalyzer.output.styles.rich_theme import PDF_ARRAY
from pdfalyzer.util import adobe_strings

DEFAULT_LABEL_STYLE = 'yellow'
FONT_OBJ_BLUE = 'deep_sky_blue4 bold'
PDF_NON_TREE_REF = 'color(243)'

# Subclasses of the key type will be styled with the value string
NODE_TYPE_STYLES = {
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

# Add common color for all NON_TREE_REFERENCES
LABEL_STYLES += [
    [re.compile(f'^{key}'), PDF_NON_TREE_REF]
    for key in adobe_strings.NON_TREE_REFERENCES
]


def get_type_style(klass) -> str:
    """Style for various types of data (e.g. DictionaryObject)"""
    return next((NODE_TYPE_STYLES[t] for t in NODE_TYPE_STYLES.keys() if issubclass(klass, t)), '')


def get_type_string_style(klass) -> str:
    """Dim version of get_type_style() for non primitives, white for primitives"""
    if issubclass(klass, (str, Number)):
        return 'white'
    else:
        return f"{get_type_style(klass)} dim"


def get_label_style(label: str) -> str:
    """Lookup a style based on the node's label string (either its type or first address)."""
    return next((ls[1] for ls in LABEL_STYLES if ls[0].search(label)), DEFAULT_LABEL_STYLE)


def get_node_type_style(obj) -> str:
    klass_string = pypdf_class_name(obj)

    if 'Dictionary' in klass_string:
        style = NODE_TYPE_STYLES[dict]
    elif 'EncodedStream' in klass_string:
        style = YARALYZER_THEME_DICT['bytes']
    elif 'Stream' in klass_string:
        style = YARALYZER_THEME_DICT['bytes.title']
    elif 'Text' in klass_string:
        style = YARALYZER_THEME_DICT['grey.light']
    elif 'Array' in klass_string:
        style = PDF_ARRAY
    else:
        style = 'bright_yellow'

    return f"{style} italic"
