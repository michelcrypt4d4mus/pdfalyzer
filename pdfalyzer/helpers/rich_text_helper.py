"""
Rich colors: https://rich.readthedocs.io/en/stable/appendix/colors.html
TODO: interesting colors # row_styles[0] = 'reverse bold on color(144)' <-
"""
import re
import time
from numbers import Number
from os import path
from shutil import get_terminal_size
from typing import Union

from PyPDF2.generic import ByteStringObject, IndirectObject
from rich import box
from rich.console import Console
from rich.errors import MarkupError
from rich.padding import Padding
from rich.style import Style
from rich.table import Table
from rich.terminal_theme import TerminalTheme
from rich.text import Text
from rich.theme import Theme

from pdfalyzer.config import is_env_var_set_and_not_false, is_invoked_by_pytest
from pdfalyzer.util import adobe_strings
from pdfalyzer.util.logging import log, log_and_print


# Colors
BYTES = 'color(100) dim'
BYTES_NO_DIM = 'color(100)'
BYTES_BRIGHTEST = 'color(220)'
BYTES_BRIGHTER = 'orange1'
BYTES_HIGHLIGHT = 'color(136)'
DANGER_HEADER = 'color(88) on white'  # Red
DEFAULT_LABEL_STYLE = 'yellow'
FONT_OBJ_BLUE = 'deep_sky_blue4 bold'
DARK_GREY = 'color(236)'
GREY = 'color(241)'
GREY_ADDRESS = 'color(238)'


# Theme used by main console
PDFALYZER_THEME = Theme({
    # colors
    'dark_grey': DARK_GREY,
    'dark_grey_italic': f"{DARK_GREY} italic",
    'darker_grey_italic': 'color(8) dim italic',
    'darkest_grey': 'color(235) dim',
    'dark_orange': 'color(58)',
    'grey': GREY,
    'light_grey': 'color(248)',
    'off_white': 'color(245)',
    'zero_bytes': 'color(20)',
    # data types
    'address': GREY_ADDRESS,
    'decode_section': 'color(100) reverse',
    'decode_subheading': 'color(215)',
    'decode_subheading_dim_italic': 'color(215) dim italic',
    'encoding': 'color(158) underline bold',
    'encoding_header': 'color(158) bold',
    'language': 'dark_green italic',
    'number': 'bright_cyan',
    'regex': 'color(218) dim',
    'no_attempt': "color(60) dim italic",
    # design elements
    'subtable': 'color(8) on color(232)',
    'headline': 'bold white underline',
    'minor_header': 'color(249) bold',
    'danger_header': DANGER_HEADER,
    'danger_header_reverse': f'{DANGER_HEADER} reverse',
    # bytes
    'ascii': 'color(58)',
    'ascii_unprintable': 'color(131)',
    'bytes': BYTES,
    'bytes_decoded': BYTES_BRIGHTEST,
    'bytes_highlighted': 'bright_red bold',
    'bytes_title': BYTES_BRIGHTER,
    'bytes_title_dim': 'orange1 dim',
    # fonts
    'charmap_title': 'bright_green',
    'font_property': 'color(135)',
    'font_title': 'reverse dark_blue on color(253)',
    'prepared_charmap': 'color(106) dim',
    'prepared_charmap_title': 'green',
    # neutral log events
    'attn': 'bold bright_cyan',
    'lowpriority': 'bright_black',
    'siren': 'blink bright_white on red3',
    # good log events
    'good': 'green4',
    'better': 'turquoise4',
    'reallygood': 'dark_cyan',
    'evenbetter': 'chartreuse1',
    'great': 'sea_green2',
    'reallygreat': 'spring_green1',
    'best': 'green1',
    # warn log events
    'warn': 'bright_yellow',
    'mildwarn': 'yellow2',
    'milderwarn': 'dark_orange3',
    'harshwarn': 'reverse bright_yellow',
    # error log events
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
    [re.compile(f'^{key}'), 'color(243)']
    for key in adobe_strings.NON_TREE_REFERENCES
]


# Color meter realted constants. Make even sized buckets color coded from blue (cold) to green (go)
METER_COLORS = list(reversed([82, 85, 71, 60, 67, 30, 24, 16]))
GRADIENT_INTERVAL = (100 / float(len(METER_COLORS))) + 0.1
# Color meter extra style thresholds (these are assuming a scale of 0-100)
UNDERLINE_CONFIDENCE_THRESHOLD = 90
BOLD_CONFIDENCE_THRESHOLD = 60
DIM_COUNTRY_THRESHOLD = 25


# Table stuff
DEFAULT_SUBTABLE_COL_STYLES = ['white', 'bright_white']
HEADER_PADDING = (1, 1)
CENTER = 'center'
FOLD = 'fold'
LEFT = 'left'
MIDDLE = 'middle'
RIGHT = 'right'


# Text object defaults mostly for table entries
NO_DECODING_ERRORS_MSG = Text('No', style='green4 dim')
DECODING_ERRORS_MSG = Text('Yes', style='dark_red dim')
NOT_FOUND_MSG = Text('(not found)', style='dark_grey_italic')

def na_txt(style: Union[str, Style] = 'white'):
    return Text('N/A', style=style)


# TerminalThemes are used when saving SVGS. This one just swaps white for black in DEFAULT_TERMINAL_THEME
PDFALYZER_TERMINAL_THEME = TerminalTheme(
    (0, 0, 0),
    (255, 255, 255),
    [
        (0, 0, 0),
        (128, 0, 0),
        (0, 128, 0),
        (128, 128, 0),
        (0, 0, 128),
        (128, 0, 128),
        (0, 128, 128),
        (192, 192, 192),
    ],
    [
        (128, 128, 128),
        (255, 0, 0),
        (0, 255, 0),
        (255, 255, 0),
        (0, 0, 255),
        (255, 0, 255),
        (0, 255, 255),
        (255, 255, 255),
    ],
)


# Keys are export function names, values are options we always want to use w/that export function
# Not meant for direct access; instead call invoke_rich_export().
_EXPORT_KWARGS = {
    'save_html': {
        'inline_styles': True,
        'theme': PDFALYZER_TERMINAL_THEME,
    },
    'save_svg': {
        'theme': PDFALYZER_TERMINAL_THEME,
    },
    'save_text': {
        'styles': True,
    },
}


# rich.console configuration (console is the main interface to Rich text formatting)
DEFAULT_CONSOLE_WIDTH = 160

def console_width_possibilities():
    # Subtract 2 from terminal cols just as a precaution in case things get weird
    return [get_terminal_size().columns - 2, DEFAULT_CONSOLE_WIDTH]

# Maximize output width if PDFALYZER_MAXIMIZE_WIDTH is set (also can changed with --maximize-width option)
if is_invoked_by_pytest():
    CONSOLE_WIDTH = DEFAULT_CONSOLE_WIDTH
elif is_env_var_set_and_not_false('PDFALYZER_MAXIMIZE_WIDTH'):
    CONSOLE_WIDTH = max(console_width_possibilities())
else:
    CONSOLE_WIDTH = min(console_width_possibilities())

# Many bytes take 4 chars to print (e.g. '\xcc') so this is the max bytes we can safely print in a line
CONSOLE_PRINT_BYTE_WIDTH = int(CONSOLE_WIDTH / 4.0)

console = Console(theme=PDFALYZER_THEME, color_system='256', highlight=False, width=CONSOLE_WIDTH)


def console_width() -> int:
    """Current width set in console obj"""
    return console._width


def subheading_width():
    return int(console_width() * 0.75)


def console_print_with_fallback(_string, style=None) -> None:
    """Fallback to regular print() if there's a Markup issue"""
    try:
        console.print(_string, style=style)
    except MarkupError:
        console.print(f"Hit a bracket issue with rich.console printing, defaulting to plain print", style='warn')
        print(_string.plain if isinstance(_string, Text) else _string)


def get_label_style(label: str) -> str:
    """Lookup a style based on the label string"""
    return next((ls[1] for ls in LABEL_STYLES if ls[0].search(label)), DEFAULT_LABEL_STYLE)


def get_type_style(klass) -> str:
    """Style for various types of data (e.g. DictionaryObject)"""
    return next((TYPE_STYLES[t] for t in TYPE_STYLES.keys() if issubclass(klass, t)), None)


def get_type_string_style(klass) -> str:
    """Dim version of get_type_style() for non primitives, white for primitives"""
    if issubclass(klass, (str, Number)):
        return 'white'
    else:
        return f"{get_type_style(klass)} dim"


def prefix_with_plain_text_obj(_str: str, style: str, root_style=None) -> Text:
    """Sometimes you need a Text() object to start plain lest the underline or whatever last forever"""
    return Text('', style=root_style or 'white') + Text(_str, style)


def to_rich_text(obj, style='') -> Text:
    """Nones become empty Text() objects, other things are __str__()ed"""
    if obj is None:
        return None

    return Text(str(obj), style=style)


def generate_subtable(cols, header_style='subtable') -> Table:
    """Suited for lpacement in larger tables"""
    table = Table(
        box=box.SIMPLE,
        show_edge=False,
        collapse_padding=True,
        header_style=header_style,
        show_lines=False,
        border_style='dark_grey',
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


def meter_style(meter_pct):
    """For coloring numbers between 0 and 100 (AKA pcts). Closer to 100 means greener, closer to 0.0 means bluer"""
    if meter_pct > 100 or meter_pct < 0:
        log.warning(f"Invalid meter_pct: {meter_pct}")

    color_number = METER_COLORS[int(meter_pct / GRADIENT_INTERVAL)]
    style = f"color({color_number})"

    if meter_pct > BOLD_CONFIDENCE_THRESHOLD:
        style += ' bold'
    if meter_pct > UNDERLINE_CONFIDENCE_THRESHOLD:
        style += ' underline'

    return style


def unprintable_byte_to_text(code: str, style='') -> Text:
    """Used with ASCII escape codes and the like, gives colored results like '[NBSP]'."""
    style = BYTES_HIGHLIGHT if style == BYTES_BRIGHTEST else style
    txt = Text('[', style=style)
    txt.append(code.upper(), style=f"{style} italic dim")
    txt.append(Text(']', style=style))
    return txt


def invoke_rich_export(export_method, output_file_basepath) -> str:
    """
    Announce the export, perform the export, announce completion.
    export_method is a Rich.console.save_blah() method, output_file_path is file path w/no extname.
    Returns the path to path data was exported to.
    """
    method_name = export_method.__name__
    extname = 'txt' if method_name == 'save_text' else method_name.split('_')[-1]
    output_file_path = f"{output_file_basepath}.{extname}"

    if method_name not in _EXPORT_KWARGS:
        raise RuntimeError(f"{method_name} is not a valid Rich.console export method!")

    kwargs = _EXPORT_KWARGS[method_name].copy()
    kwargs.update({'clear': False})

    if 'svg' in method_name:
        kwargs.update({'title': path.basename(output_file_path) })

    # Invoke it
    log_and_print(f"Invoking Rich.console.{method_name}('{output_file_path}') with kwargs: '{kwargs}'...")
    start_time = time.perf_counter()
    export_method(output_file_path, **kwargs)
    elapsed_time = time.perf_counter() - start_time
    log_and_print(f"'{output_file_path}' written in {elapsed_time:02f} seconds")
    return output_file_path
