"""
Class to handle attempting to decode a chunk of bytes into strings with various possible encodings.
Leverages the chardet library to both guide what encodings are attempted as well as to rank decodings
in the results.

Final output is a set of deoding attempts that are represented in a Rich.table, sorted like this:

    1. String representation of undecoded bytes is always the first row
    2. Encodings which chardet.detect() ranked as > 0% likelihood are sorted based on that confidence
    3. Then the unchardetectable:
        1. Decodings that were successful, unforced, and new
        2. Decodings that 'successful' but forced
        3. Decodings that were the same as other decodings
        4. Failed decodings
"""
from collections import defaultdict, namedtuple
from operator import attrgetter
from typing import List

from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from lib.binary.bytes_match import BytesMatch
from lib.binary.decoding_attempt import DecodingAttempt
from lib.config import PdfalyzerConfig
from lib.detection.constants.character_encodings import ENCODING, ENCODINGS_TO_ATTEMPT
from lib.detection.encoding_detector import ChardetEncodingAssessment, EncodingDetector
from lib.helpers.bytes_helper import clean_byte_string, rich_text_view_of_raw_bytes
from lib.helpers.dict_helper import get_dict_key_by_value
from lib.helpers.rich_text_helper import (CENTER, DECODE_NOT_ATTEMPTED_MSG, FOLD, MIDDLE, NO_DECODING_ERRORS_MSG,
     DECODING_ERRORS_MSG, NA, RAW_BYTES, RIGHT, console)
from lib.util.logging import log


# Messages used in the table to show true vs. false (a two element array can be indexed by booleans)
WAS_DECODABLE_YES_NO = [NO_DECODING_ERRORS_MSG, DECODING_ERRORS_MSG]
# Multiply chardet scores by 100 (again) to make sorting the table easy
SCORE_SCALER = 100.0


class BytesDecoder:
    def __init__(self, bytes_match: BytesMatch, label=None) -> None:
        """Instantiated with _bytes as the whole stream; :bytes_seq tells it how to pull the bytes it will decode"""
        self.bytes_match = bytes_match
        self.bytes = bytes_match.surrounding_bytes
        self.label = label or clean_byte_string(bytes_match.regex.pattern)
        self.was_match_decodable = _build_encodings_metric_dict()
        self.was_match_force_decoded = _build_encodings_metric_dict()
        self.was_match_undecodable = _build_encodings_metric_dict()
        self.undecoded_rows = []

        # Note we send both the bytes in BytesMatch as well as the surrounding bytes used when presenting
        self.encoding_detector = EncodingDetector(self.bytes)
        self.decodings = [DecodingAttempt(self.bytes_match, encoding) for encoding in ENCODINGS_TO_ATTEMPT.keys()]
        self.decoded_strings = {}  # dict[encoding: decoded string]

        # Attempt decodings we don't usually attempt if chardet is insistent enough
        forced_decodes = self._undecoded_assessments(self.encoding_detector.force_decode_assessments)
        self.decodings += [DecodingAttempt(self.bytes_match, a.encoding) for a in forced_decodes]

        # If we still haven't decoded chardets top choice, decode it
        if len(self._forced_displays()) > 0 and not self._was_decoded(self._forced_displays()[0].encoding):
            chardet_top_encoding = self._forced_displays()[0].encoding
            log.debug(f"Decoding {chardet_top_encoding} because it's chardet top choice...")
            self.decodings.append(DecodingAttempt(self.bytes_match, chardet_top_encoding))

        # Track the stats
        for decoding in self.decodings:
            if decoding.failed_to_decode:
                self.was_match_undecodable[decoding.encoding] += 1
                continue

            self.was_match_decodable[decoding.encoding] += 1

            if decoding.was_force_decoded:
                self.was_match_force_decoded[decoding.encoding] += 1

    def generate_decodings_table(self) -> Table:
        table = _empty_decodings_table()
        table.add_row(RAW_BYTES, NA, NA, rich_text_view_of_raw_bytes(self.bytes, self.bytes_match))
        rows = [self._row_from_decoding_attempt(decoding) for decoding in self.decodings]
        rows += [_row_from_chardet_assessment(assessment) for assessment in self._forced_displays()]

        for row in sorted(rows, key=attrgetter('sort_score'), reverse=True):
            table.add_row(*row[0:4])

        return table

    def print_decode_attempts(self) -> None:
        if not PdfalyzerConfig.suppress_chardet_output:
            console.print(self.encoding_detector)

        self._print_decode_attempt_subheading()
        console.print(self.generate_decodings_table())

    def _forced_displays(self) -> List[ChardetEncodingAssessment]:
        """Returns assessments over the display threshold that are not yet decoded"""
        return self._undecoded_assessments(self.encoding_detector.force_display_assessments)

    def _undecoded_assessments(self, assessments: List[ChardetEncodingAssessment]) -> List[ChardetEncodingAssessment]:
        """Fiter out the already decoded assessments from a set of assessments"""
        return [a for a in assessments if not self._was_decoded(a.encoding)]

    def _was_decoded(self, encoding: str) -> bool:
        """Check whether a given encoding is in the table already"""
        return any(row.encoding == encoding for row in self.decodings)

    def _print_decode_attempt_subheading(self) -> None:
        """Generate a rich.Panel for decode attempts"""
        headline = Text(f"Found {self.label.lower()} ", style='decode_subheading') + self.bytes_match.__rich__()
        panel = Panel(headline, style='decode_subheading', expand=False)
        console.print(panel, justify=CENTER)

    def _row_from_decoding_attempt(self, decoding: DecodingAttempt) -> 'DecodingTableRow':
        assessment = self.encoding_detector.get_encoding_assessment(decoding.encoding)
        plain_decoded_string = decoding.decoded_string.plain
        sort_score = assessment.confidence * SCORE_SCALER

        # Replace the decoded text with a "same output as X" where X is the encoding that gave the same result
        if plain_decoded_string in self.decoded_strings.values():
            encoding_with_same_output = get_dict_key_by_value(self.decoded_strings, plain_decoded_string)
            display_text = Text('same output as ', style='color(66) dim italic')
            display_text.append(encoding_with_same_output, style='encoding').append('...', style='white')
        else:
            self.decoded_strings[decoding.encoding] = plain_decoded_string
            display_text = decoding.decoded_string

        # Set failures negative, shave off a little for forced decodes
        if decoding.failed_to_decode:
            sort_score = sort_score * -1 - 100
        elif decoding.was_force_decoded:
            sort_score -= 10

        return DecodingTableRow(
            assessment.encoding_text,
            assessment.confidence_text,
            WAS_DECODABLE_YES_NO[int(decoding.was_force_decoded)],
            display_text,
            assessment.confidence,
            assessment.encoding,
            sort_score=sort_score)


def _empty_decodings_table() -> Table:
    """Empty table for decoding attempt presentation"""
    table = Table(show_lines=True, border_style='bytes', header_style='color(101) bold')

    def add_col(title, **kwargs):
        kwargs['justify'] = kwargs.get('justify', CENTER)
        table.add_column(title, overflow=FOLD, vertical=MIDDLE, **kwargs)

    add_col('Encoding', justify=RIGHT, width=12)
    add_col('Encoding Odds', max_width=len(ENCODING))
    add_col('Forced?', max_width=9)
    add_col('Decoded Output', justify='left')
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


def _row_from_chardet_assessment(assessment: ChardetEncodingAssessment) -> DecodingTableRow:
    """Build a row with just chardet assessment data and no actual decoded string"""
    return DecodingTableRow(
        assessment.encoding_text,
        assessment.confidence_text,
        NA,
        DECODE_NOT_ATTEMPTED_MSG,
        assessment.confidence,
        assessment.encoding,
        assessment.confidence * SCORE_SCALER)


def _build_encodings_metric_dict():
    """One key for each key in ENCODINGS_TO_ATTEMPT, values are all 0"""
    metrics_dict = defaultdict(lambda: 0)

    for encoding in ENCODINGS_TO_ATTEMPT.keys():
        metrics_dict[encoding] = 0

    return metrics_dict
