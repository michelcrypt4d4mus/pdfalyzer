from sys import byteorder

from rich.markup import escape
from rich.panel import Panel
from rich.text import Text

from pdfalyzer.binary.bytes_match import ALERT_STYLE, BytesMatch
from pdfalyzer.detection.constants.character_encodings import (ENCODINGS_TO_ATTEMPT, SINGLE_BYTE_ENCODINGS,
     UTF_8, UTF_16, UTF_32)
from pdfalyzer.detection.javascript_hunter import JavascriptHunter
from pdfalyzer.helpers.bytes_helper import clean_byte_string
from pdfalyzer.helpers.rich_text_helper import (BYTES_BRIGHTER, BYTES_BRIGHTEST, BYTES_NO_DIM, GREY_ADDRESS,
     prefix_with_plain_text_obj, unprintable_byte_to_text)
from pdfalyzer.util.logging import log


class DecodingAttempt:
    def __init__(self, bytes_match: BytesMatch, encoding: str) -> None:
        self.bytes_match = bytes_match
        self.encoding = encoding
        self.bytes = bytes_match.surrounding_bytes
        self.was_force_decoded = False
        self.failed_to_decode = False
        self._decode_bytes()
        self.javascript_keyword_substrings = JavascriptHunter.js_keyword_matches(self.decoded_string.plain)
        self.javascript_keyword_count = len(self.javascript_keyword_substrings)

    def _decode_bytes(self) -> None:
        """
        Sets self.decoded_string. Tries builtin decode, hands off to other methods for harsher treatement
        (Byte shifting for UTF-16/32 and custom decode for the rest) if that fails
        """
        try:
            self.decoded_string = self._to_rich_text(escape(self.bytes.decode(self.encoding)))
            log.info(f"{self.encoding} auto-decoded {self.bytes_match}")
            return
        except UnicodeDecodeError:
            log.info(f"{self.encoding} failed on 1st pass decoding {self.bytes_match} capture; custom decoding...")

        self.was_force_decoded = True

        if self.encoding in [UTF_16, UTF_32]:
            self.decoded_string = self._decode_utf_multibyte_with_byte_offset()
        else:
            self.decoded_string = self._custom_decode()

    def _custom_decode(self) -> Text:
        """Returns a Text obj representing an attempt to force a UTF-8 encoding upon an array of bytes"""
        log.info(f"Custom decoding {self.bytes_match} with {self.encoding}...")
        unprintable_char_map = ENCODINGS_TO_ATTEMPT.get(self.encoding)
        output = Text('', style='bytes_decoded')

        # We use this to skip over bytes consumed by multi-byte UTF-n chars
        skip_next = 0

        for i, b in enumerate(self.bytes):
            if skip_next > 0:
                skip_next -= 1
                continue

            _byte = b.to_bytes(1, byteorder)

            # Color the before and after bytes grey
            if i < self.bytes_match.highlight_start_idx or i > self.bytes_match.highlight_end_idx:
                style = GREY_ADDRESS
            else:
                style = self.bytes_match.highlight_style

            if style not in [GREY_ADDRESS, ALERT_STYLE]:
                if b <= 126:
                    style = BYTES_NO_DIM
                elif b <= 192:
                    style = BYTES_BRIGHTER
                else:
                    style = BYTES_BRIGHTEST

            try:
                if unprintable_char_map is not None and b in unprintable_char_map:
                    output.append(unprintable_byte_to_text(unprintable_char_map[b], style=style))
                elif b < 127:
                    output.append(_byte.decode(self.encoding), style=style)
                elif self.encoding != UTF_8:
                    output.append(_byte.decode(self.encoding), style=style)
                # At this point we know it's UTF-8, so it must be a continuation byte
                elif b <= 192:
                    # In UTF-8 bytes from 128 to 192 is a continuation byte
                    output.append(unprintable_byte_to_text(f"CHAR{b}", style=style))
                else:
                    if b <= 223:
                        char_width = 2
                    elif b <= 239:
                        char_width = 3
                    else:
                        char_width = 4

                    wide_char = self.bytes[i:i + char_width].decode(self.encoding)
                    output.append(wide_char, style=style)
                    skip_next = char_width - 1  # Won't be set if there's a decoding exception
                    log.info(f"Skipping next {skip_next} bytes because UTF-8 multibyte char '{wide_char}' used them")
            except UnicodeDecodeError:
                output.append(clean_byte_string(_byte), style=style)

        return output

    def _decode_utf_multibyte_with_byte_offset(self) -> Text:
        """ UTF-16/32 are fixed width (and wide)"""
        char_width = 2 if self.encoding == UTF_16 else 4
        log.debug(f"Decoding {self.encoding}, char_width is {char_width}...")
        last_exception = None
        decoded_str = None
        bytes_offset = 1

        while bytes_offset < char_width:
            try:
                decoded_str = self.bytes[bytes_offset:].decode(self.encoding)
            except UnicodeDecodeError as e:
                log.info(f"Exception decoding w/offset {bytes_offset} in {self.encoding}: {e}")
                last_exception = e

            if decoded_str is not None:
                break

            bytes_offset += 1

        if decoded_str is None:
            self.failed_to_decode = True
            return prefix_with_plain_text_obj(f"(failed to decode: {last_exception})", style='red dim italic')

        return self._to_rich_text(decoded_str, bytes_offset, char_width)

    def _to_rich_text(self, _string: str, bytes_offset: int=0, char_width: int=1) -> Text:
        """Convert a decoded string to highlighted Text representation"""
        # Adjust where we start the highlighting given the multibyte nature of the encodings
        highlight_byte_start_idx = self.bytes_match.highlight_start_idx + bytes_offset
        highlight_start_idx = int(highlight_byte_start_idx / char_width)
        highlight_end_idx = int((highlight_byte_start_idx + self.bytes_match.capture_len) / char_width)

        # Prevent unprintable chars other than newline. Some of them disfigure the terminal output permanently
        if self.encoding in SINGLE_BYTE_ENCODINGS:
            log.debug(f"Stepping through {self.encoding} encoded string...")
            unprintable_chars = ENCODINGS_TO_ATTEMPT[self.encoding]
            txt = Text('', style=self.bytes_match.style_at_position(0))

            for i, c in enumerate(_string):
                style = self.bytes_match.style_at_position(i)

                # 10 is newline
                if c.isprintable() or ord(c) == 10:
                    txt.append(c, style)
                elif ord(c) == 9:
                    txt.append(unprintable_byte_to_text('\\t', style=style))
                elif ord(c) in unprintable_chars:
                    txt.append(unprintable_byte_to_text(unprintable_chars[ord(c)], style=style))
                else:
                    txt.append(unprintable_byte_to_text(f"CHAR{ord(c)}", style=style))
        elif self.encoding not in ENCODINGS_TO_ATTEMPT:
            txt = Text('', style=self.bytes_match.style_at_position(0))

            for i, c in enumerate(_string):
                style = self.bytes_match.style_at_position(i)

                # 10 is newline
                if c.isprintable():
                    txt.append(c, style)
                else:
                    txt.append(unprintable_byte_to_text(f"CHAR{ord(c)}", style=style))
        else:
            log.debug(f"{self.bytes_match} w/{self.encoding}: Starting highlight at {highlight_start_idx} in:\n{_string}")
            txt = Text(_string, GREY_ADDRESS)
            txt.stylize(self.bytes_match.highlight_style, highlight_start_idx, highlight_end_idx)

        return txt
