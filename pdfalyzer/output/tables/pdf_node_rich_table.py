"""
Methods to create the rich table view for a PdfTreeNode.
"""
from collections import namedtuple
from typing import List

from rich.markup import escape
from rich.text import Text
from yaralyzer.encoding_detection.character_encodings import NEWLINE_BYTE
from yaralyzer.helpers.bytes_helper import clean_byte_string, hex_text
from yaralyzer.helpers.rich_text_helper import size_text
from yaralyzer.output.rich_console import BYTES_NO_DIM
from yaralyzer.util.logging import log

from pdfalyzer.helpers.string_helper import root_address
from pdfalyzer.output.styles.node_colors import get_label_style
from pdfalyzer.util.adobe_strings import *

# For printing SymlinkNodes
SymlinkRepresentation = namedtuple('SymlinkRepresentation', ['text', 'style'])

HEX = 'Hex'
STREAM = 'Stream'
STREAM_PREVIEW_LENGTH_IN_TABLE = 500
PREVIEW_STYLES = {HEX: BYTES_NO_DIM, STREAM: 'bytes'}


def get_symlink_representation(from_node: 'PdfTreeNode', to_node: 'PdfTreeNode') -> SymlinkRepresentation:
    """Returns a tuple (symlink_text, style) that can be used for pretty printing, tree creation, etc"""
    reference_key = str(to_node.address_of_this_node_in_other(from_node))
    pdf_instruction = root_address(reference_key)  # In case we ended up with a [0] or similar

    if pdf_instruction in DANGEROUS_PDF_KEYS:
        symlink_style = 'red_alert'
    else:
        symlink_style = get_label_style(to_node.label) + ' dim'

    symlink_str = f"{escape(reference_key)} [bright_white]=>[/bright_white]"
    symlink_str += f" {escape(str(to_node.target))} [grey](Non Child Reference)[/grey]"
    return SymlinkRepresentation(symlink_str, symlink_style)


def get_stream_preview_rows(node: 'PdfTreeNode') -> List[List[Text]]:
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
        stream_preview_lines = [clean_byte_string(line) for line in stream_preview.split(NEWLINE_BYTE)]
        stream_preview_string = "\n".join(stream_preview_lines)
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
