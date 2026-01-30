"""
Methods to create the rich table view for a PdfTreeNode.
"""
from rich.text import Text
from yaralyzer.output.theme import BYTES_NO_DIM
from yaralyzer.util.helpers.bytes_helper import NEWLINE_BYTE, clean_byte_string, hex_text
from yaralyzer.util.helpers.rich_helper import size_text

from pdfalyzer.util.logging import log

HEX = 'Hex'
STREAM = 'Stream'
STREAM_PREVIEW_LENGTH_IN_TABLE = 500
PREVIEW_STYLES = {HEX: BYTES_NO_DIM, STREAM: 'bytes'}


# TODO: this should be a method on the Objstm or other StreamNode extension to PdfTreeNode or PdfObjProps
# branch: pypdf_6.6.0__local_pypdf_changes__objstm
def get_stream_preview_rows(node: 'PdfTreeNode') -> list[list[Text]]:  # noqa: F821
    """Get rows that preview the stream data"""
    if node.stream_length == 0:
        return []
    elif node.stream_data is None or len(node.stream_data) == 0:
        log.warning(node.__rich__().append(' is a stream object but had no stream data'))
        return []

    stream_preview = node.stream_data[:STREAM_PREVIEW_LENGTH_IN_TABLE]
    stream_preview_length = len(stream_preview)
    return_rows: list[list[Text]] = []

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
