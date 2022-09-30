"""
Methods to build the rich.table used to display decoding attempts of a given bytes array.

Final output should be rich.table of decoding attempts that are sorted like this:

    1. String representation of undecoded bytes is always the first row
    2. Encodings which chardet.detect() ranked as > 0% likelihood are sorted based on that confidence
    3. Then the unchardetectable:
        1. Decodings that were successful, unforced, and new
        2. Decodings that 'successful' but forced
        3. Decodings that were the same as other decodings
        4. Failed decodings
"""

from collections import namedtuple

from rich.table import Table
from rich.text import Text

from pdfalyzer.binary.bytes_match import BytesMatch
from pdfalyzer.detection.encoding_assessment import EncodingAssessment
from pdfalyzer.helpers.bytes_helper import hex_view_of_raw_bytes, rich_text_view_of_raw_bytes
from pdfalyzer.helpers.rich_text_helper import CENTER, FOLD, MIDDLE, RIGHT, na_txt


DECODE_NOT_ATTEMPTED_MSG = Text('(decode not attempted)', style='no_attempt')
HEX = Text('HEX', style='bytes_title')
RAW_BYTES = Text('Raw', style=f"bytes")


def empty_decoding_attempts_table(bytes_match: BytesMatch) -> Table:
    """First rows are the raw / hex views of the bytes"""
    table = Table(show_lines=True, border_style='bytes', header_style='color(101) bold')

    def add_col(title, **kwargs):
        kwargs['justify'] = kwargs.get('justify', CENTER)
        table.add_column(title, overflow=FOLD, vertical=MIDDLE, **kwargs)

    add_col('Encoding', justify=RIGHT, width=12)
    add_col('Detect Odds', width=len('Detect'))
    add_col('Force?', width=len('Force?'))
    add_col('Decoded Output', justify='left')

    na = na_txt(style=HEX.style)
    table.add_row(HEX, na, na, hex_view_of_raw_bytes(bytes_match.surrounding_bytes, bytes_match))
    na = na_txt(style=RAW_BYTES.style)
    table.add_row(RAW_BYTES, na, na, rich_text_view_of_raw_bytes(bytes_match.surrounding_bytes, bytes_match))
    return table


# The confidence and encoding will not be shown in the final display - instead their Text versions are shown
DecodingTableRow = namedtuple(
    'DecodingTableRow',
    [
        'encoding_text',
        'confidence_text',
        'errors_while_decoded',
        'decoded_string',
        'confidence',
        'encoding',
        'sort_score'
    ])


def decoding_table_row(assessment: EncodingAssessment, is_forced: Text, txt: Text, score: float) -> DecodingTableRow:
    """Get a table row for a decoding attempt"""
    return DecodingTableRow(
        assessment.encoding_text,
        assessment.confidence_text,
        is_forced,
        txt,
        assessment.confidence,
        assessment.encoding,
        sort_score=score)


def assessment_only_row(assessment: EncodingAssessment, score) -> DecodingTableRow:
    """Build a row with just chardet assessment data and no actual decoded string"""
    return decoding_table_row(assessment, na_txt(), DECODE_NOT_ATTEMPTED_MSG, score)
