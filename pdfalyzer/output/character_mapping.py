"""
Output formatting for font character mappings.
"""
from rich.columns import Columns
from rich.padding import Padding
from rich.text import Text
from yaralyzer.output.console import console
from yaralyzer.util.helpers.bytes_helper import print_bytes

# from pdfalyzer.font_info import FontInfo  # Causes circular import
from pdfalyzer.output.layout import print_headline_panel, subheading_width
from pdfalyzer.util.helpers.rich_helper import quoted_text
from pdfalyzer.util.helpers.string_helper import pp

CHARMAP_TITLE = 'Embedded Character Mapping (As Extracted By PyPDF)'
PREPARED_CHARMAP_TITLE = 'Embedded Adobe PostScript charmap prepared by PyPDF'
CHARMAP_INDENT = 8
CHARMAP_PADDING = (0, 2, 0, 10)
PREPARED_CHARMAP_PADDING = (0, 0, 0, CHARMAP_INDENT)
CHARMAP_TABLE_PADDING = (1, 0, 0, CHARMAP_INDENT + 2)
CHARMAP_PANEL_INTERNAL_INDENT = 1


def print_character_mapping(font: 'FontInfo') -> None:  # noqa: F821
    """Prints the character mapping extracted by PyPDF._charmap in tidy columns."""
    _print_charmap_header(f"{font} {CHARMAP_TITLE}", 'charmap.title')
    charmap_entries = [_format_charmap_entry(k, v) for k, v in font.character_mapping.items()]

    charmap_columns = Columns(
        charmap_entries,
        column_first=True,
        padding=CHARMAP_PADDING,
        equal=True,
        align='right'
    )

    console.print(Padding(charmap_columns, CHARMAP_TABLE_PADDING), width=subheading_width())
    console.line()


def print_prepared_charmap(font: 'FontInfo'):  # noqa: F821
    """Prints the prepared_charmap returned by PyPDF."""
    _print_charmap_header(f"{font} {PREPARED_CHARMAP_TITLE}", 'charmap.prepared_title')
    console.line()
    print_bytes(font.prepared_char_map, style='charmap.prepared', indent=CHARMAP_INDENT + 2)
    console.line()


def _format_charmap_entry(k: str, v: str) -> Text:
    key = pp.pformat(k)

    for quote_char in ['"', "'"]:
        if len(key) > 1 and key.startswith(quote_char) and key.endswith(quote_char):
            key = key[1:-1]

    return quoted_text(key, 'charmap.byte') + Text(' => ') + quoted_text(str(v), style='charmap.char')


def _print_charmap_header(headline: str, style: str) -> None:
    right_padding = subheading_width() - CHARMAP_INDENT - CHARMAP_PANEL_INTERNAL_INDENT - len(headline) - 2
    print_headline_panel(headline, style, CHARMAP_INDENT, (0, right_padding, 0, 2))
