"""
Helper functions for building a table that summarizes the decoding attempts made on binary data.
"""
from pypdf import PdfReader
from rich.table import Table
from rich.text import Text

from pdfalyzer.output.layout import generate_subtable, half_width, pad_header
from pdfalyzer.util.logging import log, log_highlighter
from pdfalyzer.util.adobe_strings import *

COUNT_LABEL_STYLE = 'navajo_white3'
PAGE_COUNT = Text('page count', style=COUNT_LABEL_STYLE)
IMAGE_COUNT = Text('image count', style=COUNT_LABEL_STYLE)
HIGHLIGHT_IF = ['http', FALSE, TRUE]


def metadata_table(reader: PdfReader) -> Table:
    """Build a table of metadata extracted from/computed about the PDF."""
    table = Table('Property', 'Value', header_style='bold', title=' Metadata', title_style='grey', title_justify='left')
    table.columns[0].justify = 'right'

    if len(reader.metadata or {}):
        for k, v in (reader.metadata or {}).items():
            v = log_highlighter(str(v)) if isinstance(v, str) and any(hif in v for hif in HIGHLIGHT_IF) else str(v)
            table.add_row(Text(k, style='wheat4'), v)
    else:
        table.add_row('', Text('(no formal metadata found in file)'), style='dim italic')

    try:
        table.add_row(PAGE_COUNT, log_highlighter(f"{len(reader.pages):,}"))
    except Exception as e:
        log.error(f"Failed to get page count! {e}")
        table.add_row(PAGE_COUNT, Text(f"Failed to get page count!", style='bright_red'))

    try:
        table.add_row(IMAGE_COUNT, log_highlighter(f"{sum([len(p.images) for p in reader.pages]):,}"))
    except Exception as e:
        log.error(f"Failed to get image count! {e}")
        table.add_row(IMAGE_COUNT, Text(f"Failed to get image count!", style='bright_red'))

    return table
