"""
Build a rich table to show the sizes of embedded streams.
"""

from typing import List

from rich.table import Table
from yaralyzer.helpers.rich_text_helper import size_in_bytes_text
from yaralyzer.output.file_hashes_table import LEFT

from pdfalyzer.decorators.pdf_tree_node import PdfTreeNode


def stream_objects_table(stream_nodes: List[PdfTreeNode]) -> Table:
    """Build a table of stream objects and their lengths."""
    table = Table('Stream Length', 'Node', title=' Embedded Streams', title_style='grey', title_justify=LEFT)
    table.columns[0].justify = 'right'

    for node in stream_nodes:
        table.add_row(size_in_bytes_text(node.stream_length), node.__rich__())

    return table
