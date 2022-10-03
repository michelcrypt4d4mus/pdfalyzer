"""
Class to handle attempting to decode a chunk of bytes into strings with various possible encodings.
Leverages the chardet library to both guide what encodings are attempted as well as to rank decodings
in the results.
"""

from collections import defaultdict
from operator import attrgetter
from typing import List, Optional

from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from pdfalyzer.binary.bytes_match import BytesMatch
from pdfalyzer.binary.decoding_attempt import DecodingAttempt
from pdfalyzer.config import PdfalyzerConfig

from pdfalyzer.detection.encoding_assessment import EncodingAssessment
from pdfalyzer.detection.constants.character_encodings import ENCODING, ENCODINGS_TO_ATTEMPT
from pdfalyzer.detection.encoding_detector import EncodingDetector
from pdfalyzer.helpers.bytes_helper import clean_byte_string
from pdfalyzer.helpers.dict_helper import get_dict_key_by_value
from pdfalyzer.helpers.rich_text_helper import CENTER, DECODING_ERRORS_MSG, NO_DECODING_ERRORS_MSG, console
from pdfalyzer.output.decoding_attempts_table import (DecodingTableRow, assessment_only_row, empty_decoding_attempts_table,
     decoding_table_row)
from pdfalyzer.util.logging import log


# Messages used in the table to show true vs. false (a two element array can be indexed by booleans)
WAS_DECODABLE_YES_NO = [NO_DECODING_ERRORS_MSG, DECODING_ERRORS_MSG]

# Multiply chardet scores by 100 (again) to make sorting the table easy
SCORE_SCALER = 100.0


class BytesDecoder:
    def __init__(self, bytes_match: BytesMatch, label: Optional[str] = None) -> None:
        """Instantiated with _bytes as the whole stream; :bytes_seq tells it how to pull the bytes it will decode"""
        self.bytes_match = bytes_match
        self.bytes = bytes_match.surrounding_bytes
        self.label = label or bytes_match.label

        # Empty table/metrics/etc
        self.table = empty_decoding_attempts_table(bytes_match)
        self.was_match_decodable = _build_encodings_metric_dict()
        self.was_match_force_decoded = _build_encodings_metric_dict()
        self.was_match_undecodable = _build_encodings_metric_dict()
        self.decoded_strings = {}  # dict[encoding: decoded string]
        self.undecoded_rows = []

        # Note we send both the match and surrounding bytes used when detecting the encoding
        self.encoding_detector = EncodingDetector(self.bytes)

    def print_decode_attempts(self) -> None:
        if not PdfalyzerConfig.SUPPRESS_CHARDET_OUTPUT:
            console.print(self.encoding_detector)

        self._print_decode_attempt_subheading()
        console.print(self._generate_decodings_table())

    def _generate_decodings_table(self) -> Table:
        """First rows are the raw / hex views of the bytes"""
        self.decodings = [DecodingAttempt(self.bytes_match, encoding) for encoding in ENCODINGS_TO_ATTEMPT.keys()]

        # Attempt decodings we don't usually attempt if chardet is insistent enough
        forced_decodes = self._undecoded_assessments(self.encoding_detector.force_decode_assessments)
        self.decodings += [DecodingAttempt(self.bytes_match, a.encoding) for a in forced_decodes]

        # If we still haven't decoded chardets top choice, decode it
        if len(self._forced_displays()) > 0 and not self._was_decoded(self._forced_displays()[0].encoding):
            chardet_top_encoding = self._forced_displays()[0].encoding
            log.debug(f"Decoding {chardet_top_encoding} because it's chardet top choice...")
            self.decodings.append(DecodingAttempt(self.bytes_match, chardet_top_encoding))

        rows = [self._row_from_decoding_attempt(decoding) for decoding in self.decodings]
        rows += [assessment_only_row(a, a.confidence * SCORE_SCALER) for a in self._forced_displays()]
        self._track_decode_stats()

        for row in sorted(rows, key=attrgetter('sort_score'), reverse=True):
            self.table.add_row(*row[0:4])

        return self.table

    def _forced_displays(self) -> List[EncodingAssessment]:
        """Returns assessments over the display threshold that are not yet decoded"""
        return self._undecoded_assessments(self.encoding_detector.force_display_assessments)

    def _undecoded_assessments(self, assessments: List[EncodingAssessment]) -> List[EncodingAssessment]:
        """Fiter out the already decoded assessments from a set of assessments"""
        return [a for a in assessments if not self._was_decoded(a.encoding)]

    def _was_decoded(self, encoding: str) -> bool:
        """Check whether a given encoding is in the table already"""
        return any(row.encoding == encoding for row in self.decodings)

    def _print_decode_attempt_subheading(self) -> None:
        """Generate a rich.Panel for decode attempts"""
        headline = Text(f"Found {self.label.lower()} ", style='decode.subheading') + self.bytes_match.__rich__()
        panel = Panel(headline, style='decode.subheading', expand=False)
        console.print(panel, justify=CENTER)

    def _track_decode_stats(self):
        "Track stats about successful vs. forced vs. failed decode attempts"
        for decoding in self.decodings:
            if decoding.failed_to_decode:
                self.was_match_undecodable[decoding.encoding] += 1
                continue

            self.was_match_decodable[decoding.encoding] += 1

            if decoding.was_force_decoded:
                self.was_match_force_decoded[decoding.encoding] += 1

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

        was_forced = WAS_DECODABLE_YES_NO[int(decoding.was_force_decoded)]
        return decoding_table_row(assessment, was_forced, display_text, sort_score)


def _build_encodings_metric_dict():
    """One key for each key in ENCODINGS_TO_ATTEMPT, values are all 0"""
    metrics_dict = defaultdict(lambda: 0)

    for encoding in ENCODINGS_TO_ATTEMPT.keys():
        metrics_dict[encoding] = 0

    return metrics_dict
