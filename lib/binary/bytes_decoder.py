"""
Class to handle attempt various turning bytes into strings via various encoding options
"""
from numbers import Number
from sys import byteorder

from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from lib.binary.bytes_match import BytesMatch
from lib.detection.character_encodings import (ENCODINGS_TO_ATTEMPT, UTF_8, UTF_16, UTF_32,
     build_encodings_metric_dict)
from lib.detection.encoding_detector import EncodingDetector
from lib.helpers.bytes_helper import (DANGEROUS_INSTRUCTIONS, clean_byte_string, num_surrounding_bytes,
     build_rich_text_view_of_raw_bytes)
from lib.helpers.dict_helper import get_dict_key_by_value
from lib.helpers.rich_text_helper import (BYTES_BRIGHTER, BYTES_BRIGHTEST, BYTES_HIGHLIGHT,
     DECODE_NOT_ATTEMPTED_MSG, NO_DECODING_ERRORS_MSG, GREY, GREY_ADDRESS, DECODING_ERRORS_MSG, NA, RAW_BYTES,
     console, prefix_with_plain_text_obj, unprintable_byte_to_text)
from lib.util.logging import log



class BytesDecoder:
    def __init__(self, _bytes: bytes, bytes_match: BytesMatch, label=None) -> None:
        """Instantiated with _bytes as the whole stream; :bytes_seq tells it how to pull the bytes it will decode"""
        self.bytes = _bytes
        self.bytes_len = len(_bytes)
        self.label = label
        self.bytes_match = bytes_match

        # Note we send both the bytes in BytesMatch as well as the surrounding bytes used when presenting
        self.chardet_manager = EncodingDetector(self.bytes)

        # Adjust the highlighting start point in case this bytes_seq is very early in the stream
        self.highlight_start_idx = min(self.bytes_match.start_idx, num_surrounding_bytes())

        # Build table with raw byte representation in the first row. Rows are collected in self.table_rows to
        # be sorted before actually inserted them in to the table.
        self.table_rows = []
        self.decoded_table = _build_decoded_bytes_table()
        self.decoded_table.add_row(RAW_BYTES, NA, NA, build_rich_text_view_of_raw_bytes(self.bytes, self.bytes_match))

        if self.bytes_match.bytes in DANGEROUS_INSTRUCTIONS:
            self.highlight_style = 'error'
        else:
            self.highlight_style = BYTES_HIGHLIGHT

        # Metrics tracking variables
        self.were_matched_bytes_decodable = build_encodings_metric_dict()
        self.decoded_strings = {}  # Keys are enconding names, vals are the result of Text().plain()

    def force_print_with_all_encodings(self) -> None:
        """Prints a table showing the result of forcefully decoding self.surrounding bytes in different encodings"""
        console.print(self._decode_attempt_subheading_panel())

        for encoding in ENCODINGS_TO_ATTEMPT.keys():
            decoded_string = self._decode_bytes(encoding)
            plain_decoded_string = decoded_string.plain

            if plain_decoded_string in self.decoded_strings.values():
                encoding_with_same_output = get_dict_key_by_value(self.decoded_strings, plain_decoded_string)
                decoded_string = Text('same output as ', style='color(66) dim italic')
                decoded_string.append(encoding_with_same_output, style='encoding')
                decoded_string.append('...', style='white')
            else:
                self.decoded_strings[encoding] = plain_decoded_string

            self._add_table_row(encoding, decoded_string)

        # Add table rows for encodings chardet thinks are high likelihood"""
        self._add_unscanned_encodings_chardet_has_confidence_in()

        # Sort the rows top to bottom based on chardet's reported confidence in a given encoding.
        for row in sorted(self.table_rows, key=_decoded_table_sorter, reverse=True):
            self.decoded_table.add_row(*row[0:4])

        console.print(self.decoded_table)

    def _add_unscanned_encodings_chardet_has_confidence_in(self):
        """Add table rows for encodings chardet thinks are high likelihood even if we didn't"""
        for assessment in self.chardet_manager.unique_results:
            _encoding = assessment.encoding.plain

            if self._is_in_table(_encoding) or assessment.confidence <= EncodingDetector.force_display_threshold:
                continue
            elif assessment.confidence >= EncodingDetector.force_decode_threshold:
                self.were_matched_bytes_decodable[_encoding] = 0
                log.info(f"chardet: {assessment.confidence}% confidence in {_encoding}... we'll try it")

                try:
                    decoded_string = self._decode_bytes(_encoding)
                    log.info(f"  Successfully decoded with nonstandard encoding {_encoding}!")
                except RuntimeError as e:
                    decoded_string = Text(f"Tried nonstandard encoding bc chardet confidence. It failed: {e}", style='dark_red')

                self._add_table_row(_encoding, decoded_string)
                continue
            else:
                self.table_rows.append(_build_no_decode_attempt_row(assessment))

    def _is_in_table(self, encoding) -> bool:
        """Check whether a given encoding is in the table already"""
        return any(row[0].plain == encoding for row in self.table_rows)

    def _add_table_row(self, encoding, decoded_string) -> None:
        self.table_rows.append([
            prefix_with_plain_text_obj(encoding, style='encoding'),         # Encoding fancy Text
            self.chardet_manager.get_confidence_formatted_txt(encoding),    # Confidence metric fancy Text
            DECODING_ERRORS_MSG if self.were_matched_bytes_decodable[encoding] > 0 else NO_DECODING_ERRORS_MSG, # easy vs. hard to decode
            decoded_string,
            self.chardet_manager.get_confidence_score(encoding),             # Numerical confidence metric
            self.chardet_manager.get_encoding_assessment(encoding)           # Full assessment
        ])

    def _decode_bytes(self, encoding: str) -> Text:
        """
        Tries builtin decode, hands off to other methods for harsher treatement
        (Byte shifting for UTF-16/32 and custom decode for the rest) if that fails
        """
        decoded_string = None

        try:
            decoded_string = self.bytes.decode(encoding)
            log.info(f"Auto-decoded {self.bytes_match} with {encoding}")
            self.were_matched_bytes_decodable[encoding] += 1
            return Text(decoded_string, style='bytes')
        except UnicodeDecodeError:
            log.info(f"1st pass decoding {self.bytes_match} capture with {encoding} failed; custom decoding...")

        if encoding in [UTF_16, UTF_32]:
            return self._decode_utf_multibyte(encoding)

        # If all that fails... custom decode
        return self._custom_decode(encoding)

    def _custom_decode(self, encoding: str) -> Text:
        """Returns a Text obj representing an attempt to force a UTF-8 encoding upon an array of bytes"""
        log.info(f"Custom decoding {self.bytes_match} with {encoding}")
        unprintable_char_map = ENCODINGS_TO_ATTEMPT.get(encoding)
        output = Text('', style='bytes_decoded')
        # We use this to skip over bytes consumed by multi-byte UTF-8 chars
        skip_next = 0

        for i, b in enumerate(self.bytes):
            if skip_next > 0:
                skip_next -= 1
                continue

            _byte = b.to_bytes(1, byteorder)

            # Color the before and after bytes grey
            if i < self.highlight_start_idx or i >= (self.highlight_start_idx + self.bytes_match.total_length()):
                style = GREY_ADDRESS
            else:
                style = self.highlight_style

            try:
                if unprintable_char_map is not None and b in unprintable_char_map:
                    output.append(unprintable_byte_to_text(unprintable_char_map[b], style=style))
                elif b < 127:
                    output.append(_byte.decode(encoding), style=style)
                elif encoding != UTF_8:
                    output.append(_byte.decode(encoding), style=style)
                elif b <= 192:
                    # At this point we know it's UTF_8, so it must be a continuation byte
                    output.append(unprintable_byte_to_text(f"NC{b}", style=style))
                else:
                    # Now it must be UTF-8: https://en.wikipedia.org/wiki/UTF-8
                    if b <= 223:
                        char_width = 2
                    elif b <= 239:
                        char_width = 3
                    else:
                        char_width = 4

                    wide_char = self.bytes[i:i + char_width].decode(encoding)
                    output.append(wide_char, style=style or BYTES_BRIGHTEST)
                    skip_next = char_width - 1  # Won't be set if there's a decoding exception
                    log.info(f"Skipping next {skip_next} bytes because UTF-8 multibyte char '{wide_char}' used them")
            except UnicodeDecodeError:
                output.append(clean_byte_string(_byte), style=style or BYTES_BRIGHTER)

        return output

    def _decode_utf_multibyte(self, encoding: str) -> Text:
        """# UTF-16/32 are fixed width (and wide)"""
        divisor = 2 if encoding == UTF_16 else 4
        log.debug(f"Decoding {encoding}, divisor is {divisor}...")

        # NOTE! This is only a way to check valid byte start for UTF-16 as long as the surrounding bytes count is even
        #start_idx = 0 if is_even(self.bytes_match.start_idx) else 1
        # in UTF-16/32 everything is halved/quartered bc using more bytes
        highlight_start_idx = int(self.highlight_start_idx / divisor)
        highlight_end_idx = int((self.highlight_start_idx + self.bytes_match.total_length()) / divisor)
        decoded_str = None

        try:
            decoded_str = self.bytes.decode(encoding)
            log.info(f"... Decoded {len(decoded_str)} with {encoding}!")
        except UnicodeDecodeError as e:
            log.info(f"Exception while trying to parse in {encoding}: {e}\nTrying offset by 1 byte")

            try:
                decoded_str = self.bytes[1:].decode(encoding)
            except UnicodeDecodeError as e2:
                log.info(f"Failed to decode when offset by 1; giving up on {encoding}")
                return prefix_with_plain_text_obj('(failed to decode)', style='red dim italic')

        log.debug(f"Decoded with {encoding}: {decoded_str}")
        txt = prefix_with_plain_text_obj('', style='white')
        txt = Text(str(decoded_str[0:highlight_start_idx]), style='dark_grey')
        txt.append(str(decoded_str[highlight_start_idx:highlight_end_idx]), style=self.highlight_style)
        txt.append(str(decoded_str[highlight_end_idx:]), style='dark_grey')
        return txt

    def _decode_attempt_subheading_panel(self) -> Panel:
        """Generate a Rich panel for decode attempts"""
        headline = Text('Found ', style='decode_subheading')
        headline.append(str(self.bytes_match.capture_len), style='number')
        headline.append(f" bytes matching ")
        headline.append(f"{self.bytes_match.regex.pattern} ", style=self.highlight_style or 'regex')
        headline.append(f"between {self.label.lower()} ")
        headline.append(f"(start idx: ", style='off_white')
        headline.append(str(self.bytes_match.start_idx), style='number')
        headline.append(', end idx: ', style='off_white')
        headline.append(str(self.bytes_match.end_idx), style='number')
        headline.append(')', style='off_white')
        return Panel(headline, style='decode_subheading', expand=False)


def _build_decoded_bytes_table() -> Table:
    decoded_table = Table(
        'Encoding',
        'How Likely Is It That This Is The Right Encoding? (chardet)',
        'Decoding Errors?',
        'Decoded Output',
        show_lines=True,
        border_style='bytes',
        header_style=f"color(101) bold")

    # 1st Col (encoding)
    decoded_table.columns[0].style = 'white'
    decoded_table.columns[0].justify = 'right'
    # 2nd col (chardet confidence/country)
    decoded_table.columns[1].overflow = 'fold'
    decoded_table.columns[1].justify = 'center'
    decoded_table.columns[1].no_wrap = False
    decoded_table.columns[1].max_width = 13
    # 3rd col (forced decode?)
    decoded_table.columns[2].max_width = 9
    decoded_table.columns[2].justify = 'center'
    # 4th col (decoded bytes)
    decoded_table.columns[3].overflow = 'fold'

    for i, col in enumerate(decoded_table.columns):
        col.vertical = 'middle'

    return decoded_table


def _decoded_table_sorter(row: list) -> Number:
    """
    Sorts the decoded strings by chardet's returned confidence (raw number is hiding in column we do not show)
    with the alphabet breaking ties
    """
    return row[4] + (0.01 * ord(row[0].plain[0]))


def _build_no_decode_attempt_row(assessment):
    """Build a row with just chardet assessment data and no actual decoded string"""
    return [
        assessment.encoding,
        assessment.confidence_str,
        NA,
        DECODE_NOT_ATTEMPTED_MSG,
        assessment.confidence,
        assessment
    ]
