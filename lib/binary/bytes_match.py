"""
Simple class to keep track of regex matches against binary data.  Basically an re.match object with a very few
extra bells and whistles.
pre and post_capture_lens refer to the regex sections before and after the capture group, e.g. a regex like
'123(.*)x' would have pre_capture_len of 3 and post_capture_len of 2.
"""
import re

from lib.util.logging import log


# Regex Capture used with extracting quoted chunks of bytes
CAPTURE_BYTES = b'(.*?)'


class BytesMatch:
    def __init__(self, match: re.Match , ordinal: int) -> None:
        """Ordinal means it's the Nth match with this regex (not super important but useful)"""
        self.pattern = match.re.pattern
        self.start_idx = match.start()
        self.end_idx = match.end()
        self.regex = match.re
        self.ordinal = ordinal

        try:
            self.bytes = match[1]
        except IndexError:
            log.debug(f"No capture group for {self.pattern}, setting bytes to be the regex itself")
            self.bytes = self.pattern

        self.capture_len = len(self.bytes)
        self._compute_pre_and_post_capture_lens()

    def total_length(self):
        """Include the length of the rest of the regex. Mostly works but sometimes we highly a few extra bytes"""
        return self.pre_capture_len + self.capture_len + self.post_capture_len

    def _compute_pre_and_post_capture_lens(self):
        """Deside which non capture chars in the regex are pre vs. post capture group"""
        regex_len_divmod_2 = divmod(len(self.pattern), 2)

        # If there's no capture group (as there is not for regexes like b'/JS') split it down the middle
        if CAPTURE_BYTES in self.pattern :
            self.pre_capture_len, self.post_capture_len = [len(b) for b in self.pattern.split(CAPTURE_BYTES)]
        else:
            self.pre_capture_len = self.post_capture_len = regex_len_divmod_2[0]
            self.post_capture_len += regex_len_divmod_2[1] # Assign the odd byte to the latter half

    def __str__(self):
        return f"<({self.pattern}) #{self.ordinal}: {self.capture_len} bytes from {self.start_idx} to {self.end_idx}>"
