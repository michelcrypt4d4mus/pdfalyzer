"""
Manager class to ease dealing with the chardet encoding detection library 'chardet'.
"""
import logging
from collections import namedtuple
from numbers import Number

import chardet
from rich import box
from rich.table import Table
from rich.text import Text

from lib.util.dict_helper import get_value_as_lowercase_and_none_if_blank
from lib.util.logging import log
from lib.util.string_utils import console


METER_COLORS = list(reversed([82, 85, 87, 60, 69, 63, 27, 17]))
MIN_BYTES_FOR_CHARDET = 9


# Suppress chardet logs
for submodule in ['universaldetector', 'charsetprober', 'codingstatemachine']:
    logging.getLogger(f"chardet.{submodule}").setLevel(logging.WARNING)


# chardet detects encodings but the return values are messy; this is for tidying them up
ChardetEncodingDetectResult = namedtuple(
    'ChardetEncodingDetectResult',
    ['encoding', 'language', 'confidence', 'confidence_str'])


class ChardetManager:
    def __init__(self, bytes: bytes) -> None:
        self.bytes = bytes
        self.bytes_len = len(bytes)
        self.unique_results = []  # Unique by encoding
        self.table = build_chardet_table()
        self.attempt_encoding_detection()

    def attempt_encoding_detection(self) -> None:
        """Use the chardet library to try to figure out the encoding of self.bytes"""
        if self.bytes_len < MIN_BYTES_FOR_CHARDET:
            log.info(f"{self.bytes_len} is not enough bytes to run chardet.detect()")
            return []

        detection_results = chardet.detect_all(self.bytes, ignore_threshold=True)
        already_seen_encodings = {}

        if len(detection_results) == 1 and detection_results[0]['encoding'] is None:
            console.print("\n (chardet.detect() has no idea what the encoding is)\n", style='grey')
            return []

        for i, detection_result in enumerate(detection_results):
            result_tuple = type(self).build_chardet_result(detection_result)
            self.table.add_row(f"{i + 1}.", result_tuple[0], result_tuple[1], result_tuple[3])

            # Only retain one result per encoding possibility - the highest confidence one.
            if result_tuple.encoding.plain not in already_seen_encodings:
                self.unique_results.append(result_tuple)
                already_seen_encodings[result_tuple.encoding.plain] = result_tuple
            else:
                same_encoding = already_seen_encodings.get(result_tuple.encoding.plain)
                log.debug(f"Ditching chardet: {result_tuple} (we already saw {same_encoding})")

        console.print(self.table, justify='right', width=50)
        console.print('')

    @staticmethod
    def build_chardet_result(chardet_result_dict) -> ChardetEncodingDetectResult:
        """Build a ChardetEncodingDetectResult tuple"""
        encoding = get_value_as_lowercase_and_none_if_blank(chardet_result_dict, 'encoding')
        encoding = None if encoding is None else Text(encoding.lower(), style='encoding_header')
        language = get_value_as_lowercase_and_none_if_blank(chardet_result_dict, 'language')
        language = None if language is None else Text(language.lower(), style='dark_green')
        confidence = 100 * (get_value_as_lowercase_and_none_if_blank(chardet_result_dict, 'confidence') or 0.0)

        if isinstance(confidence, Number):
            confidence_str = Text(f"{round(confidence, 1)}%", style=meter_style(confidence / 100.0))

            # As good a place as any to put the most likely language info
            if language is not None:
                confidence_str.append(f" ({language})", style='language')
        else:
            confidence_str = None

        return ChardetEncodingDetectResult(encoding, language, confidence, confidence_str)


def build_chardet_table():
    table = Table(
        'Rank', 'Encoding', 'Language', 'Confidence',
        title='chardet encoding detection',
        title_style='color(153) italic dim',
        header_style='off_white',
        style='dim',
        box=box.SIMPLE,
        show_edge=False,
        collapse_padding=True)

    table.columns[0].justify = 'right'
    return table


def meter_style(meter_pct):
    """For coloring numbers between 0 and 1 (pcts). Closer to 1.0 means greener, closer to 0.0 means bluer"""
    gradient_interval = (1.0 / float(len(METER_COLORS))) + 0.01
    return f"color({METER_COLORS[int(meter_pct / gradient_interval)]}) {'dim' if meter_pct < 0.4 else ''}"
