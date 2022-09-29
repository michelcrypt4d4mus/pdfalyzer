"""
Methods to build the rich.table used to display decoding attempts of a given bytes array
"""

from collections import namedtuple

from rich.table import Table
from rich.text import Text

from lib.binary.bytes_match import BytesMatch
from lib.detection.encoding_assessment import EncodingAssessment
from lib.helpers.bytes_helper import hex_view_of_raw_bytes, rich_text_view_of_raw_bytes
from lib.helpers.rich_text_helper import CENTER, FOLD, MIDDLE, NA, RIGHT


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

    na = NA.copy()
    na.style = HEX.style
    table.add_row(HEX, na, na, hex_view_of_raw_bytes(bytes_match.bytes, bytes_match))

    na = NA.copy()
    na.style = RAW_BYTES.style
    table.add_row(RAW_BYTES, na, na, rich_text_view_of_raw_bytes(bytes_match.bytes, bytes_match))
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
    return decoding_table_row(assessment, NA, DECODE_NOT_ATTEMPTED_MSG, score)
