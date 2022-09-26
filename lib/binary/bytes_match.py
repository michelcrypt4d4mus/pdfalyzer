"""
Simple class to keep track of regex matches against binary data.  Basically an re.match object with
some (not many) extra bells and whistles, most notably the surrounding_bytes property.

pre_capture_len and post_capture_len refer to the regex sections before and after the capture group,
e.g. a regex like '123(.*)x:' would have pre_capture_len of 3 and post_capture_len of 2.
"""
import re

from rich.text import Text

from lib.config import num_surrounding_bytes
from lib.detection.constants.dangerous_instructions import DANGEROUS_INSTRUCTIONS
from lib.helpers.rich_text_helper import BYTES_BRIGHTEST, BYTES_HIGHLIGHT, GREY_ADDRESS, prefix_with_plain_text_obj
from lib.util.logging import log


# Regex Capture used when extracting quoted chunks of bytes
CAPTURE_BYTES = b'(.*?)'
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
            self.highlight_style = BYTES_BRIGHTEST

        self.capture_len = len(self.bytes)
        # Adjust the highlighting start point in case these bytes_seq is very early in the stream
        self.highlight_start_idx = min(match.start(), num_surrounding_bytes())
        self.highlight_end_idx = self.highlight_start_idx + self.capture_len
        self._compute_pre_and_post_capture_lengths()

    def total_length(self):
        """Include the length of the rest of the regex. Mostly works but sometimes we highly a few extra bytes"""
        return self.pre_capture_len + self.capture_len + self.post_capture_len

    def match_idx_text(self) -> Text:
        """Returns a colored Text object describing the location and size of the pattern match"""
        if self.capture_len == 0:
            style = 'grey'
        else:
            style = 'bytes'

        txt = prefix_with_plain_text_obj(f"{self.capture_len} byte ", style='number', root_style=style)
        txt.append('match found at ').append(f"idx {self.match.start()}", style='number')
        return txt

    def style_at_position(self, idx):
        # Not entirely sure why we need the +1 but we somehow do...
        if idx < self.highlight_start_idx or idx > self.highlight_end_idx + 1:
            return GREY_ADDRESS
        else:
            return self.highlight_style

    def _compute_pre_and_post_capture_lengths(self):
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
