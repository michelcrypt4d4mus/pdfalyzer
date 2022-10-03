"""
Simple class to keep track of regex matches against binary data.  Basically an re.match object with
some (not many) extra bells and whistles, most notably the surrounding_bytes property.

pre_capture_len and post_capture_len refer to the regex sections before and after the capture group,
e.g. a regex like '123(.*)x:' would have pre_capture_len of 3 and post_capture_len of 2.
"""
import re
from typing import Iterator, Optional

from rich.text import Text

from pdfalyzer.config import PdfalyzerConfig
from pdfalyzer.detection.constants.binary_regexes import DANGEROUS_INSTRUCTIONS, CAPTURE_BYTES
from pdfalyzer.helpers.rich_text_helper import BYTES_BRIGHTER, GREY_ADDRESS, prefix_with_plain_text_obj
from pdfalyzer.util.logging import log

# Regex Capture used when extracting quoted chunks of bytes
ALERT_STYLE = 'error'


class BytesMatch:
    def __init__(
            self,
            matched_against: bytes,
            start_idx: int,
            length: int,
            label: str,
            ordinal: int,
            match: Optional[re.Match] = None  # It's rough to get the regex from yara :(
        ) -> None:
        """
        Ordinal means it's the Nth match with this regex (not super important but useful)
        YARA makes it a little rouch to get the actual regex that matched. Can be done with plyara eventually.
        """
        self.matched_against: bytes = matched_against
        self.start_idx: int = start_idx
        self.end_idx: int = start_idx + length
        self.match_length: int = length
        self.length: int = length
        self.label: str = label
        self.ordinal: int = ordinal
        self.match: Optional[re.Match] = match
        # Maybe should be called "matched_bytes"
        self.bytes = matched_against[start_idx:self.end_idx]
        self.match_groups: Optional[tuple] = match.groups() if match else None
        self._find_surrounding_bytes()
        # Adjust the highlighting start point in case this match is very early in the stream
        self.highlight_start_idx = start_idx - self.surrounding_start_idx
        self.highlight_end_idx = self.highlight_start_idx + self.length

        if self.bytes in DANGEROUS_INSTRUCTIONS:
            self.highlight_style = ALERT_STYLE
        else:
            self.highlight_style = BYTES_BRIGHTER

    @classmethod
    def from_regex_match(cls, matched_against: bytes, match: re.Match, ordinal: int) -> 'BytesMatch':
        return cls(matched_against, match.start(), len(match[0]), match.re.pattern, ordinal, match)

    @classmethod
    def from_yara_str(cls, matched_against: bytes, rule_name: str, yara_str: dict, ordinal: int) -> 'BytesMatch':
        """Build a BytesMatch from a yara string match. matched_against is the set of bytes yara was run against"""
        return cls(matched_against, yara_str[0], len(yara_str[2]), rule_name + ' ' + yara_str[1], ordinal)

    @classmethod
    def for_yara_strings_in_match(cls, matched_against: bytes, yara_match: dict) -> Iterator['BytesMatch']:
        """
        Iterator over all strings returned as part of a yara match dict, which looks like this:
        {
            'tags': ['foo', 'bar'],
            'matches': True,
            'namespace': 'default',
            'rule': 'my_rule',
            'meta': {},
            'strings': [(81L, '$a', 'abc'), (141L, '$b', 'def')]
        }
        """
        for i, yara_str in enumerate(yara_match['strings']):
            yield(cls.from_yara_str(matched_against, yara_match['rule'], yara_str, i + 1))

    def style_at_position(self, idx) -> str:
        """Get the style for the byte at position idx within the matched bytes"""
        if idx < self.highlight_start_idx or idx >= self.highlight_end_idx:
            return GREY_ADDRESS
        else:
            return self.highlight_style

    def _find_surrounding_bytes(self, num_before: Optional[int] = None, num_after: Optional[int] = None) -> None:
        """Find the surrounding bytes, making sure not to step off the beginning or end"""
        num_after = num_after or num_before or PdfalyzerConfig.NUM_SURROUNDING_BYTES
        num_before = num_before or PdfalyzerConfig.NUM_SURROUNDING_BYTES
        self.surrounding_start_idx: int = max(self.start_idx - num_before, 0)
        self.surrounding_end_idx: int = min(self.end_idx + num_after, len(self.matched_against))
        self.surrounding_bytes: bytes = self.matched_against[self.surrounding_start_idx:self.surrounding_end_idx]

    def __rich__(self) -> Text:
        headline = prefix_with_plain_text_obj(str(self.match_length), style='number', root_style='decode.subheading')
        headline.append(f" bytes matching ")
        headline.append(f"{self.label} ", style=ALERT_STYLE if self.highlight_style == ALERT_STYLE else 'regex')
        headline.append('at ')
        headline.append(f"(start idx: ", style='off_white')
        headline.append(str(self.start_idx), style='number')
        headline.append(', end idx: ', style='off_white')
        headline.append(str(self.end_idx), style='number')
        headline.append(')', style='off_white')
        return headline

    def __str__(self):
        return self.__rich__().plain
