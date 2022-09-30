"""
Manager class to ease dealing with the chardet encoding detection library 'chardet'.
Each instance of this classes managed a chardet.detect_all() scan on a single set of bytes.
"""
from collections import namedtuple
from numbers import Number
from operator import attrgetter
from typing import List

import chardet
from rich import box
from rich.padding import Padding
from rich.table import Table
from rich.text import Text

from pdfalyzer.detection.encoding_assessment import ENCODING, EncodingAssessment
from pdfalyzer.helpers.rich_text_helper import console
from pdfalyzer.util.logging import log


# TODO: move to config.py?
MIN_BYTES_FOR_ENCODING_DETECTION = 9
CONFIDENCE_SCORE_RANGE = range(0, 100)


class EncodingDetector:
    # 10 as in 10%, 0.02, etc.  Encodings w/confidences below this will not be displayed in the decoded table
    force_display_threshold = 20.0

    # At what chardet.detect() confidence % should we force a decode with an obscure encoding?
    force_decode_threshold = 50.0

    def __init__(self, _bytes: bytes) -> None:
        self.bytes = _bytes
        self.bytes_len = len(_bytes)
        self.table = _empty_chardet_results_table()

        if not self.has_enough_bytes():
            log.debug(f"{self.bytes_len} is not enough bytes to run chardet.detect()")
            self._set_empty_results()
            self.has_any_idea = None  # not false!
            return

        # Unique by encoding, ignoring language.  Ordered from highest to lowest confidence
        self.unique_assessments = []
        self.raw_chardet_assessments = chardet.detect_all(self.bytes, ignore_threshold=True)

        if len(self.raw_chardet_assessments) == 1 and self.raw_chardet_assessments[0][ENCODING] is None:
            log.info(f"chardet.detect() has no idea what the encoding is, result: {self.raw_chardet_assessments}")
            self._set_empty_results()
            self.has_any_idea = False
            return

        self.has_any_idea = True
        self.assessments = [EncodingAssessment(a) for a in self.raw_chardet_assessments]
        self._uniquify_results_and_build_table()
        self.force_decode_assessments = self.assessments_above_confidence(type(self).force_decode_threshold)
        self.force_display_assessments = self.assessments_above_confidence(type(self).force_display_threshold)

    def get_encoding_assessment(self, encoding) -> EncodingAssessment:
        """If chardet produced one, return it, otherwise return a dummy node with confidence of 0"""
        assessment = next((r for r in self.unique_assessments if r.encoding == encoding), None)
        return assessment or EncodingAssessment.dummy_encoding_assessment(encoding)

    def has_enough_bytes(self) -> bool:
        return self.bytes_len >= MIN_BYTES_FOR_ENCODING_DETECTION

    def assessments_above_confidence(self, cutoff: float) -> List[EncodingAssessment]:
        return [a for a in self.unique_assessments if a.confidence >= cutoff]

    def __rich__(self) -> Padding:
        return Padding(self.table, (0, 0, 0, 20))

    def _uniquify_results_and_build_table(self) -> None:
        """Keep the highest result per encoding, ignoring the language chardet has indicated"""
        already_seen_encodings = {}

        for i, result in enumerate(self.assessments):
            self.table.add_row(f"{i + 1}", result.encoding_text, result.confidence_text)

            # self.unique_assessments retains one result per encoding possibility (the highest confidence one)
            # Some encodings are not language specific and for those we don't care about the language
            if result.encoding not in already_seen_encodings:
                self.unique_assessments.append(result)
                already_seen_encodings[result.encoding] = result
            else:
                log.debug(f"Skipping chardet result {result}: we already saw {already_seen_encodings[result.encoding]})")

        self.unique_assessments.sort(key=attrgetter('confidence'), reverse=True)

    def _set_empty_results(self) -> None:
        self.assessments = []
        self.unique_assessments = []
        self.raw_chardet_assessments = []
        self.force_decode_assessments = []
        self.force_display_assessments = []


def _empty_chardet_results_table():
    """Returns a fresh table"""
    table = Table(
        'Rank', 'Encoding', 'Confidence',
        title='chardet encoding detection',
        title_style='color(153) italic dim',
        header_style='off_white',
        style='dim',
        box=box.SIMPLE,
        show_edge=False,
        collapse_padding=True)

    table.columns[0].justify = 'right'
    table.columns
    return table
