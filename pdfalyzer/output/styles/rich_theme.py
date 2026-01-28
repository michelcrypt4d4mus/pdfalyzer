"""
Rich colors: https://rich.readthedocs.io/en/stable/appendix/colors.html
TODO: interesting colors # row_styles[0] = 'reverse bold on color(144)' <-
"""
from rich.theme import Theme
from yaralyzer.output.console import console
from yaralyzer.output.theme import YARALYZER_THEME_DICT

# Colors / PDF object styles
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


# Override whatever theme The Yaralyzer has configured.
console.push_theme(Theme(PDFALYZER_THEME_DICT))
