"""
Manager class to ease dealing with the chardet encoding detection library 'chardet'.
Each instance of this classes managed a chardet.detect_all() scan on a single set of bytes.
"""
from collections import namedtuple
from os import environ

import chardet
from rich import box
from rich.table import Table
from rich.text import Text

from lib.helpers.dict_helper import get_lowercase_value
from lib.helpers.rich_text_helper import (DIM_COUNTRY_THRESHOLD, NA, console, meter_style,
     prefix_with_plain_text_obj, to_rich_text)
from lib.util.logging import log


MIN_BYTES_FOR_ENCODING_DETECTION = 9
SUPPRESS_CHARDET_TABLE_ENV_VAR = 'PDFALYZER_SUPPRESS_CHARDET_TABLE'
CONFIDENCE_SCORE_RANGE = range(0, 100)


class EncodingDetector:
    # 10 as in 10%, 0.02, etc.  Encodings w/confidences below this will not be displayed in the decoded table
    force_display_threshold = 20.0
    # At what chardet.detect() confidence % should we force a decode with an obscure encoding?
    force_decode_threshold = 50.0

    def __init__(self, _bytes: bytes) -> None:
        self.bytes = _bytes
        self.bytes_len = len(_bytes)
        self.unique_results = []  # Unique by encoding
        self.table = build_chardet_table()
        self.attempt_encoding_detection()

    def attempt_encoding_detection(self) -> None:
        """Use the chardet library to try to figure out the encoding of self.bytes"""
        if self.bytes_len < MIN_BYTES_FOR_ENCODING_DETECTION:
            log.info(f"{self.bytes_len} is not enough bytes to run chardet.detect()")
            return []

        detection_results = chardet.detect_all(self.bytes, ignore_threshold=True)
        already_seen_encodings = {}

        if len(detection_results) == 1 and detection_results[0]['encoding'] is None:
            console.print("\n (chardet.detect() has no idea what the encoding is)\n", style='grey')
            return []

        for i, detection_result in enumerate(detection_results):
            result_tuple = build_chardet_encoding_assessment(detection_result)
            self.table.add_row(f"{i + 1}", result_tuple[0], result_tuple[3])

            # Only retain one result per encoding possibility (the highest confidence one)
            if result_tuple.encoding.plain not in already_seen_encodings:
                self.unique_results.append(result_tuple)
                already_seen_encodings[result_tuple.encoding.plain] = result_tuple
            else:
                same_encoding = already_seen_encodings.get(result_tuple.encoding.plain)
                log.debug(f"Discarding chardet result {result_tuple} (we already saw {same_encoding})")

        if environ.get(SUPPRESS_CHARDET_TABLE_ENV_VAR) is None:
            console.print(self.table, justify='right', width=50)
            console.print('')

    def get_encoding_assessment(self, encoding):
        """If chardet produced one, return it, otherwise return a dummy node with confidence of 0"""
        assessment = next((r for r in self.unique_results if r.encoding.plain == encoding), None)
        return assessment or empty_encoding_assessment()  # TODO: this could be a constant

    def get_confidence_formatted_txt(self, encoding):
        assessment = self.get_encoding_assessment(encoding)
        return NA if assessment.encoding is None else assessment.confidence_str

    def get_confidence_score(self, encoding):
        assessment = self.get_encoding_assessment(encoding)
        return -1 if assessment.encoding is None else assessment.confidence


# chardet detects encodings but the return values are messy; this is for tidying them up
ChardetEncodingAssessment = namedtuple(
    'ChardetEncodingAssessment',
    [
        'encoding',
        'language',
        'confidence',
        'confidence_str',
    ])


def empty_encoding_assessment():
    return ChardetEncodingAssessment(None, None, confidence=-1, confidence_str=NA)


def build_chardet_encoding_assessment(chardet_result: dict) -> ChardetEncodingAssessment:
    """Build a ChardetEncodingAssessment namedtuple"""
    def get_text_for(field, style):
        value = get_lowercase_value(chardet_result, field)
        return to_rich_text(value, style=style)

    encoding = get_text_for('encoding', 'encoding_header')
    language = get_text_for('language', 'dark_green')
    confidence = 100 * (get_lowercase_value(chardet_result, 'confidence') or 0.0)
    confidence_str = prefix_with_plain_text_obj(f"{round(confidence, 1)}%", style=meter_style(confidence))

    # Pair the language info with the confidence level into one Text obj
    if language is not None:
        dim = 'dim' if confidence < DIM_COUNTRY_THRESHOLD else ''
        language_capitalized = Text(' '.join([word.capitalize() for word in language._text]))
        confidence_str.append(f" ({language_capitalized})", style=f"color(23) {dim}")

    return ChardetEncodingAssessment(encoding, language, confidence, confidence_str)


def build_chardet_table():
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
