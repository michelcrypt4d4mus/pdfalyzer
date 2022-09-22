"""

Rich colors: https://rich.readthedocs.io/en/stable/appendix/colors.html
"""
from rich.theme import Theme


# Colors
BYTES_BRIGHTEST = 'color(220)'
BYTES_BRIGHTER = 'orange1'
BYTES_HIGHLIGHT = 'color(136)'
DEFAULT_LABEL_STYLE = 'yellow'
DARK_GREY = 'color(236)'
GREY = 'color(241)'
GREY_ADDRESS = 'color(238)'

PDFALYZER_THEME = Theme({
    # colors
    'dark_grey': DARK_GREY,
    'dark_grey_italic': f"{DARK_GREY} italic",
    'darkest_grey': 'color(235) dim',
    'dark_orange': 'color(58)',
    'grey': GREY,
    'light_grey': 'color(248)',
    'off_white': 'color(245)',
    # data types
    'address': GREY_ADDRESS,
    'decode_section': 'color(100) reverse',
    'decode_subheading': 'color(215)',
    'encoding': 'color(158) underline',
    'encoding_header': 'color(158) bold',
    'headline': 'bold white underline',
    'language': 'dark_green italic',
    'number': 'bright_cyan',
    'minor_header': 'color(249) bold',
    'danger_header': 'color(88) reverse',
    # bytes
    'ascii': 'color(58)',
    'ascii_unprintable': 'color(131)',
    'bytes': 'color(100) dim',
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
