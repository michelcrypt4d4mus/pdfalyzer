"""
Simple class to keep track of regex matches against binary data.  Basically an re.match object with
some (not many) extra bells and whistles, most notably the surrounding_bytes property.

pre_capture_len and post_capture_len refer to the regex sections before and after the capture group,
e.g. a regex like '123(.*)x:' would have pre_capture_len of 3 and post_capture_len of 2.
"""
import re

from rich.text import Text

from pdfalyzer.config import PdfalyzerConfig
from pdfalyzer.detection.constants.binary_regexes import DANGEROUS_INSTRUCTIONS, CAPTURE_BYTES
from pdfalyzer.helpers.rich_text_helper import BYTES_BRIGHTER, GREY_ADDRESS, prefix_with_plain_text_obj
from pdfalyzer.util.logging import log

# Regex Capture used when extracting quoted chunks of bytes
ALERT_STYLE = 'error'


class BytesMatch:
    def __init__(self, match: re.Match, surrounding_bytes: bytes, ordinal: int) -> None:
        """Ordinal means it's the Nth match with this regex (not super important but useful)"""
        self.match = match
        self.regex = match.re
        self.pattern = match.re.pattern
        self.surrounding_bytes = surrounding_bytes
        self.ordinal = ordinal

        try:
            self.bytes = match[1]
        except IndexError:
            self.bytes = self.pattern

        if self.bytes in DANGEROUS_INSTRUCTIONS:
            self.highlight_style = ALERT_STYLE
        else:
            self.highlight_style = BYTES_BRIGHTER

        self.capture_len = len(self.bytes)
        # Adjust the highlighting start point in case this match is very early in the stream
        self.highlight_start_idx = min(match.start(), PdfalyzerConfig.NUM_SURROUNDING_BYTES)
        self.highlight_end_idx = self.highlight_start_idx + self.capture_len
        self._compute_pre_and_post_capture_lengths()

    def total_length(self) -> int:
        """Include the length of the rest of the regex. Mostly works but sometimes we highly a few extra bytes"""
        return self.pre_capture_len + self.capture_len + self.post_capture_len

    def style_at_position(self, idx) -> str:
        """Not entirely sure why we need the +1 but we somehow do"""
        if idx < self.highlight_start_idx or idx > self.highlight_end_idx + 1:
            return GREY_ADDRESS
        else:
            return self.highlight_style

    def _compute_pre_and_post_capture_lengths(self) -> None:
        """Deside which non capture chars in the regex are pre vs. post capture group"""
        regex_len_divmod_2 = divmod(len(self.pattern), 2)

        # If there's no capture group (as there is not for regexes like b'/JS') split it down the middle
        if CAPTURE_BYTES in self.pattern :
            self.pre_capture_len, self.post_capture_len = [len(b) for b in self.pattern.split(CAPTURE_BYTES)]
        else:
            self.pre_capture_len = self.post_capture_len = regex_len_divmod_2[0]
            self.post_capture_len += regex_len_divmod_2[1] # Assign the odd byte to the latter half

    def __rich__(self) -> Text:
        headline = prefix_with_plain_text_obj(str(self.capture_len), style='number', root_style='decode_subheading')
        headline.append(f" bytes matching ")
        headline.append(f"{self.regex.pattern} ", style=ALERT_STYLE if self.highlight_style == ALERT_STYLE else 'regex')
        headline.append('at ')
        headline.append(f"(start idx: ", style='off_white')
        headline.append(str(self.match.start()), style='number')
        headline.append(', end idx: ', style='off_white')
        headline.append(str(self.match.end()), style='number')
        headline.append(')', style='off_white')
        return headline

    def __str__(self):
        return self.__rich__().plain
