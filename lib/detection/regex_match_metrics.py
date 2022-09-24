"""
Class to  measure what we enounter as we iterate over every single match of a relatively simple byte level regex
(e.g. "bytes between quotes") against a relatively large pool of close to random encrypted binary data

Things like how much many of our matched bytes were we able to decode easily vs. by force vs. not at all,
were some encodings have a higher pct of success than others (indicating part of our mystery data might be encoded
that way?
"""
from lib.detection.character_encodings import ENCODINGS_TO_ATTEMPT


class RegexMatchMetrics:
    def __init__(self) -> None:
        self.match_count = 0
        self.bytes_matched = 0
        self.matches_decoded = 0
        self.matches_skipped_for_being_too_big = 0
        self.matches_skipped_for_being_empty = 0
        self.easy_decode_count = 0
        self.forced_decode_count = 0
        self.were_matched_bytes_decodable = {k: 0 for k in ENCODINGS_TO_ATTEMPT.keys()}
        self.bytes_match_objs = []

    def __str__(self):
        return f"<matches: {self.match_count}, bytes: {self.bytes_matched}, decoded: {self.matches_decoded} " + \
               f"too_big: {self.matches_skipped_for_being_too_big}, empty: {self.matches_skipped_for_being_empty}>"

