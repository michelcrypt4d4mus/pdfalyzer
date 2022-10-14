"""
Methods to create the rich table view for a PdfTreeNode.
"""
from typing import List

from PyPDF2.generic import StreamObject
from rich.markup import escape
from rich.table import Table
from rich.text import Text
from yaralyzer.encoding_detection.character_encodings import NEWLINE_BYTE
from yaralyzer.helpers.bytes_helper import clean_byte_string, hex_text
from yaralyzer.helpers.rich_text_helper import size_text
from yaralyzer.output.rich_console import BYTES_NO_DIM, YARALYZER_THEME
from yaralyzer.util.logging import log

from pdfalyzer.helpers.rich_text_helper import PDF_ARRAY, TYPE_STYLES
from pdfalyzer.helpers.string_helper import pypdf_class_name
from pdfalyzer.output.layout import get_label_style
from pdfalyzer.util.adobe_strings import *

HEX = 'Hex'
STREAM = 'Stream'
STREAM_PREVIEW_LENGTH_IN_TABLE = 500
PREVIEW_STYLES = {HEX: BYTES_NO_DIM, STREAM: 'bytes'}


def build_pdf_node_table(node: 'PdfTreeNode') -> Table:
    """
    Generate a Rich table representation of this node's PDF object and its properties.
    Table cols are [title, address, class name] (not exactly headers but sort of).
    Dangerous things like /JavaScript, /OpenAction, Type1 fonts, etc, will be highlighted red.
    """
    title = f"{node.idnum}.{escape(node.label)}"
    table = Table(title, escape(node.tree_address()), pypdf_class_name(node.obj))
    table.columns[0].header_style = f'reverse {get_label_style(node.label)}'
    table.columns[1].header_style = 'dim'
    table.columns[1].overflow = 'fold'
    table.columns[2].header_style = get_node_type_style(node.obj)

    if node.label != node.known_to_parent_as:
        table.add_row(Text('ParentRefKey', style='grey'), Text(str(node.known_to_parent_as), style='grey'), '')

    if isinstance(node.obj, dict):
        for k, v in node.obj.items():
            row = type(node).to_table_row(k, v)

            # Make dangerous stuff look dangerous
            if (k in DANGEROUS_PDF_KEYS) or (node.label == FONT and k == SUBTYPE and v == TYPE1_FONT):
                table.add_row(*[col.plain for col in row], style='fail')
            else:
                table.add_row(*row)
    elif isinstance(node.obj, list):
        for i, item in enumerate(node.obj):
            table.add_row(*type(node).to_table_row(i, item))
    elif not isinstance(node.obj, StreamObject):
        # Then it's a single element node like a URI, TextString, etc.
        table.add_row(*type(node).to_table_row('', node.obj, is_single_row_table=True))

    for row in _get_stream_preview_rows(node):
        row.append(Text(''))
        table.add_row(*row)

    return table


def get_node_type_style(obj) -> str:
    klass_string = pypdf_class_name(obj)

    if 'Dictionary' in klass_string:
        style = TYPE_STYLES[dict]
    elif 'EncodedStream' in klass_string:
        style = YARALYZER_THEME.styles['bytes']
    elif 'Stream' in klass_string:
        style = YARALYZER_THEME.styles['bytes.title']
    elif 'Text' in klass_string:
        style = YARALYZER_THEME.styles['grey.light']
    elif 'Array' in klass_string:
        style = PDF_ARRAY
    else:
        style = 'bright_yellow'

    return f"{style} italic"


def _get_stream_preview_rows(node: 'PdfTreeNode') -> List[List[Text]]:
    """Get rows that preview the stream data"""
    return_rows: List[List[Text]] = []

    if node.stream_length == 0:
        return return_rows

    if node.stream_data is None or len(node.stream_data) == 0:
        log.warning(node.__rich__().append(' is a stream object but had no stream data'))
        return return_rows

    stream_preview = node.stream_data[:STREAM_PREVIEW_LENGTH_IN_TABLE]
    stream_preview_length = len(stream_preview)

    if isinstance(node.stream_data, bytes):
        stream_preview_hex = hex_text(stream_preview).plain
        stream_preview_lines = stream_preview.split(NEWLINE_BYTE)
        stream_preview_string = "\n".join([clean_byte_string(line) for line in stream_preview_lines])
    else:
        stream_preview_hex = f"N/A (Stream data is type '{type(node.stream_data).__name__}', not bytes)"
        stream_preview_string = stream_preview

    def add_preview_row(hex_or_stream: str, stream_string: str):
        if stream_preview_length < STREAM_PREVIEW_LENGTH_IN_TABLE:
            row_label = "Data" if hex_or_stream != HEX else ' View'
        else:
            row_label = "Preview" if hex_or_stream != HEX else ' Preview'
            stream_string += '...'

        style = PREVIEW_STYLES[hex_or_stream]
        row_label = f"{hex_or_stream}{row_label}\n  ({stream_preview_length} bytes)"
        return_rows.append([Text(row_label, 'grey'), Text(stream_string, style)])

    add_preview_row(STREAM, stream_preview_string)
    add_preview_row(HEX, stream_preview_hex)
    return_rows.append([Text('StreamLength', style='grey'), size_text(len(node.stream_data))])
    return return_rows
