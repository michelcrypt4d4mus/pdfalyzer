"""
Output formatting for font character mappings.
"""
from rich.columns import Columns
from rich.padding import Padding
from rich.text import Text
from yaralyzer.helpers.bytes_helper import print_bytes
from yaralyzer.output.rich_console import console
from yaralyzer.util.logging import log

from pdfalyzer.helpers.rich_text_helper import quoted_text
from pdfalyzer.helpers.string_helper import pp
from pdfalyzer.output.layout import print_headline_panel, subheading_width

CHARMAP_TITLE = 'Character Mapping (As Extracted By PyPDF)'
CHARMAP_TITLE_PADDING = (1, 0, 0, 2)
CHARMAP_PADDING = (0, 2, 0, 10)


def print_character_mapping(font: 'FontInfo') -> None:
    """Prints the character mapping extracted by PyPDF._charmap in tidy columns"""
    if font.character_mapping is None or len(font.character_mapping) == 0:
        log.info(f"No character map found in {font}")
        return

    print_headline_panel(f"{font} {CHARMAP_TITLE}", style='charmap.title')
    charmap_entries = [_format_charmap_entry(k, v) for k, v in font.character_mapping.items()]

    charmap_columns = Columns(
        charmap_entries,
        column_first=True,
        padding=CHARMAP_PADDING,
        equal=True,
        align='right')

    console.print(Padding(charmap_columns, CHARMAP_TITLE_PADDING), width=subheading_width())
    console.line()


def print_prepared_charmap(font: 'FontInfo'):
    """Prints the prepared_charmap returned by PyPDF."""
    if font.prepared_char_map is None:
        log.info(f"No prepared_charmap found in {font}")
        return

    headline = f"{font} Adobe PostScript charmap prepared by PyPDF"
    print_headline_panel(headline, style='charmap.prepared_title')
    print_bytes(font.prepared_char_map, style='charmap.prepared')
    console.line()


def _format_charmap_entry(k: str, v: str) -> Text:
    key = pp.pformat(k)

    for quote_char in ['"', "'"]:
        if len(key) > 1 and key.startswith(quote_char) and key.endswith(quote_char):
            key = key[1:-1]

    return quoted_text(key, 'charmap.byte') + Text(' => ') + quoted_text(str(v), 'charmap.char')
