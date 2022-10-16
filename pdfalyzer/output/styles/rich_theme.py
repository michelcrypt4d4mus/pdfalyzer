"""
Rich colors: https://rich.readthedocs.io/en/stable/appendix/colors.html
TODO: interesting colors # row_styles[0] = 'reverse bold on color(144)' <-
"""
from rich.theme import Theme
from yaralyzer.output.rich_console import GREY_ADDRESS, YARALYZER_THEME_DICT, console

# Colors / PDF object styles
DANGER_HEADER = 'color(88) on white'  # Red
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

# Override whatever theme The Yaralyzer has configured.
console.push_theme(Theme(PDFALYZER_THEME_DICT))
