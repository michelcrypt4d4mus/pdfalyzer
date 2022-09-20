"""
Various text formatting/styling/manipulating methods.
Rich colors: https://rich.readthedocs.io/en/stable/appendix/colors.html
"""
from collections import namedtuple
from numbers import Number
from pprint import PrettyPrinter
from pydoc import ispackage
from shutil import get_terminal_size
import re
import sys

from PyPDF2.generic import ByteStringObject, IndirectObject, PdfObject
from rich.console import Console
from rich.markup import escape
from rich.panel import Panel
from rich.text import Text
from rich.theme import Theme

from lib.util import adobe_strings
from lib.util.logging import log


INDENT_DEPTH = 4
PRETTY_PRINT_WIDTH = 60
DEFAULT_CONSOLE_PRINT_WIDTH = 160
CONSOLE_PRINT_WIDTH = min([get_terminal_size().columns, DEFAULT_CONSOLE_PRINT_WIDTH])
SUBHEADING_WIDTH = int(CONSOLE_PRINT_WIDTH * 0.75)

NEWLINE_BYTE = b"\n"
DEFAULT_LABEL_STYLE = 'yellow'

PDFALYZER_THEME = Theme({
    'address': 'color(238)',
    'bytes': 'color(100) dim',
    'bytes_decoded': 'color(220)',
    'bytes_highlighted': 'bright_red bold',
    'ascii_unprintable': 'color(220) dim',
    'font_property': 'color(135)',
    'headline': 'bold white underline',
    'off_white': 'color(245)',
    'light_grey': 'color(248)',
    # sections
    'bytes_title': 'orange1',
    'bytes_title_dim': 'orange1 dim',
    'charmap_title': 'bright_green',
    'font_title': 'reverse dark_blue on color(253)',
    'prepared_charmap': 'color(106) dim',
    'prepared_charmap_title': 'green',
    'minor_header': 'bright_white bold',
    # events
    'attn': 'bold bright_cyan',
    'lowpriority': 'bright_black',
    'siren': 'blink bright_white on red3',
    'grey': 'color(241)',
    'dark_grey': 'color(234)',
    'darkest_grey': 'color(235) dim',
    # Good events
    'good': 'green4',
    'better': 'turquoise4',
    'reallygood': 'dark_cyan',
    'evenbetter': 'chartreuse1',
    'great': 'sea_green2',
    #light_steel_blue
    'reallygreat': 'spring_green1',
    'best': 'green1',
    # warn events
    'warn': 'bright_yellow',
    'mildwarn': 'yellow2',
    'milderwarn': 'dark_orange3',
    'harshwarn': 'reverse bright_yellow',
    # errors
    'error': 'bright_red',
    'milderror': 'red',
    'fail': 'bold reverse red',
    'red_alert': 'blink bold red reverse',
})

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

ENCODINGS = [
    'big5',
    'big5hkscs',
    'cp950',
    'gb2312',
    'gbk',
    'gb18030',
    'hz',
    'iso2022_jp_2',
    'utf-7',
    'utf-8',
    'utf-16',
]

UNPRINTABLE_ASCII = {
    0: 'Null',
    1: 'StartOfHeading',
    2: 'StartOfText',
    3: 'EndOfText',
    4: 'EndOfTransmission',
    5: 'Enquiry',
    6: 'Acknowledgement',
    7: 'Bell',
    8: 'BackSpace',
    9: 'HorizontalTab',
    10: 'LineFeed',
    11: 'VerticalTab',
    12: 'FormFeed',
    13: 'CarriageReturn',
    14: 'ShiftOut',
    15: 'ShiftIn',
    16: 'DataLineEscape',
    17: 'DeviceControl1',
    18: 'DeviceControl2',
    19: 'DeviceControl3',
    20: 'DeviceControl4',
    21: 'NegativeAcknowledgement',
    22: 'SynchronousIdle',
    23: 'EndOfTransmitBlock',
    24: 'Cancel',
    25: 'EndOfMedium',
    26: 'Substitute',
    27: 'Escape',
    28: 'FileSeparator',
    29: 'GroupSeparator',
    30: 'RecordSeparator',
    31: 'UnitSeparator',
    127: 'Delete',
}

# Unicode prefix for 2 byte chars
UNICODE_2_BYTE_PREFIX = b'\xc0'

# Keys are bytes, values are number of bytes in a character starting with that byte
UNICODE_PREFIX_BYTES = {
    UNICODE_2_BYTE_PREFIX: 2,
    b'\xe0': 3,
    b'\xf0': 4
}

SymlinkRepresentation = namedtuple('SymlinkRepresentation', ['text', 'style'])


pp = PrettyPrinter(
    indent=INDENT_DEPTH,
    width=PRETTY_PRINT_WIDTH,
    sort_dicts=True)


console = Console(
    theme=PDFALYZER_THEME,
    color_system='256',
    highlight=False,
    width=CONSOLE_PRINT_WIDTH,
    record=True)


def print_section_header(headline: str) -> None:
    console.print("\n\n")
    console.print(Panel(headline, style='reverse'))
    console.print('')


def clean_byte_string(bytes_array: bytes) -> str:
    """Gives you '\x80\nx44' instead of b'\x80\nx44'"""
    return str(bytes_array).removeprefix("b'").removesuffix("'")


def print_bytes(bytes_array: bytes, style=None) -> None:
    """Convert bytes to a string representation and print to console"""
    for line in bytes_array.split(NEWLINE_BYTE):
        console.print(clean_byte_string(line), style=style or 'bytes')


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


def force_print_with_encoding(_bytes: bytes, encoding: str, highlight_at_idx=None, highlight_length=None) -> str:
    """Returns a string representing an attempt to force a UTF-8 encoding upon an array of bytes"""
    output = Text('', style='bytes_decoded')
    skip_next = False

    for i, b in enumerate(_bytes):
        if skip_next > 0:
            skip_next -= 1
            continue

        style = None

        if highlight_at_idx and i >= highlight_at_idx and i < (highlight_at_idx + highlight_length):
            style = 'bytes_highlighted'

        try:
            if b in UNPRINTABLE_ASCII:
                output.append(f"[{UNPRINTABLE_ASCII[b].upper()}]", style=style or 'bytes')
            elif b < 127:
                output.append(b.to_bytes(1, sys.byteorder).decode(encoding), style=style or 'bytes_decoded')
            elif encoding == 'utf-8':
                _byte = b.to_bytes(1, sys.byteorder)

                if _byte in UNICODE_PREFIX_BYTES:
                    char_width = UNICODE_PREFIX_BYTES[_byte]
                    output.append(_bytes[i:i + char_width].decode(), style=style or 'bytes_decoded')
                    skip_next = char_width - 1  # Won't be set if there's a decoding exception
                elif b <= 2047:
                    output.append((UNICODE_2_BYTE_PREFIX + _byte).decode(), style=style or 'bytes_decoded')
                else:
                    output.append(clean_byte_string(_byte), style=style or 'ascii_unprintable')
            else:
                output.append(b.to_bytes(1, sys.byteorder).decode(encoding), style=style or 'bytes_decoded')
        except UnicodeDecodeError:
            output.append(clean_byte_string(b.to_bytes(1, sys.byteorder)), style=style or 'ascii_unprintable')

    console.print(output)


def list_to_string(_list: list, sep=', ') -> str:
    """Join elements of _list with sep"""
    return sep.join([str(item) for item in _list])


def get_symlink_representation(from_node, to_node) -> SymlinkRepresentation:
    """Returns a tuple (symlink_text, style)"""
    reference_key = str(to_node.get_reference_key_for_relationship(from_node))
    pdf_instruction = reference_key.split('[')[0]  # In case we ended up with a [0] or similar

    if pdf_instruction in adobe_strings.DANGEROUS_PDF_KEYS:
        symlink_style = 'red_alert'
    else:
        symlink_style = get_label_style(to_node.label) + ' dim'

    symlink_str = f"{escape(reference_key)} [bright_white]=>[/bright_white] {escape(str(to_node.target))} [grey](Non Child Reference)[/grey]"
    return SymlinkRepresentation(symlink_str, symlink_style)
