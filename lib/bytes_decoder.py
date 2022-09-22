"""
Class to handle attempt various turning bytes into strings via various encoding options
"""
from numbers import Number
from sys import byteorder

from rich.table import Table
from rich.text import Text

from lib.chardet_manager import ChardetManager
from lib.util.bytes_helper import (DANGEROUS_INSTRUCTIONS, UNICODE_2_BYTE_PREFIX, UNICODE_PREFIX_BYTES,
     BytesSequence, clean_byte_string, get_bytes_before_and_after_sequence, num_surrounding_bytes,
     build_rich_text_view_of_raw_bytes)
from lib.util.dict_helper import get_dict_key_by_value
from lib.util.logging import log
from lib.util.rich_text_helper import BYTES_BRIGHTER, BYTES_BRIGHTEST, BYTES_HIGHLIGHT, GREY, GREY_ADDRESS
from lib.util.string_utils import console


# As in 2%, 0.05, etc.  Encodings w/confidences below this will not be displayed in the decoded table
CHARDET_CUTOFF = 2
RAW_BYTES = Text('raw bytes', style=f"{GREY} italic")
NA = Text('n/a', style='dark_grey_italic')

UNPRINTABLE_ASCII = {
    0: 'Nul',
    1: 'HEAD',  # 'StartHeading',
    2: 'TXT',  # 'StartText',
    3: 'EndTxt',
    4: 'EOT',  # End of transmission
    5: 'ENQ',  # 'Enquiry',
    6: 'ACK',  # 'Acknowledgement',
    7: 'BEL',  # 'Bell',
    8: 'BS',   # 'BackSpace',
    #9: 'HorizontalTab',
    #10: 'LFEED',  # 'LineFeed',
    11: 'VTAB',  # 'VerticalTab',
    12: 'FEED',  # 'FormFeed',
    13: 'CR',  # 'CarriageReturn',
    14: 'S.OUT',  # 'ShiftOut',
    15: 'S.IN',  # 'ShiftIn',
    16: 'DLE',  # 'DataLineEscape',
    17: 'DEV1',  # DeviceControl1',
    18: 'DEV2',  # 'DeviceControl2',
    19: 'DEV3',  # 'DeviceControl3',
    20: 'DEV4',  # 'DeviceControl4',
    21: 'NEG',   # NegativeAcknowledgement',
    22: 'IDLE',  # 'SynchronousIdle',
    23: 'ENDXMIT',  # 'EndTransmitBlock',
    24: 'CNCL',  # 'Cancel',
    25: 'ENDMED',  # 'EndMedium',
    26: 'SUB',  # 'Substitute',
    27: 'ESC',  # 'Escape',
    28: 'FILESEP',  # 'FileSeparator',
    29: 'G.SEP',  #'GroupSeparator',
    30: 'R.SEP',  #'RecordSeparator',
    31: 'U.SEP',  # 'UnitSeparator',
    127: 'DEL',
}

ENCODINGS_TO_ATTEMPT_UNNORMALIZED = [
    'ascii',
    'utf-8',
    'utf-16',
    'utf-7',
    'iso-8859-1',
    'windows-1252',
]

ENCODINGS_TO_ATTEMPT = [enc.lower() for enc in ENCODINGS_TO_ATTEMPT_UNNORMALIZED]


class BytesDecoder:
    def __init__(self, _bytes: bytes, bytes_seq: BytesSequence) -> None:
        """Instantiated with _bytes as the whole stream; :bytes_seq tells it how to pull the bytes it will decode"""
        self.bytes = _bytes
        self.bytes_seq = bytes_seq
        # TODO: this should probably be the self.bytes var
        self.surrounding_bytes = get_bytes_before_and_after_sequence(_bytes, bytes_seq)
        # Adjust the highlighting start point in case this bytes_seq is very early in the stream
        self.highlight_start_idx = min(self.bytes_seq.start_position, num_surrounding_bytes())

    def custom_decode(self, encoding: str, highlight_style=None) -> Text:
        """Returns a Text obj representing an attempt to force a UTF-8 encoding upon an array of bytes"""
        output = Text('', style='bytes_decoded')
        skip_next = 0

        for i, b in enumerate(self.surrounding_bytes):
            if skip_next > 0:
                skip_next -= 1
                continue

            _byte = b.to_bytes(1, byteorder)
            style = highlight_style

            # Color the before and after bytes grey, like the dead zone
            if i < self.highlight_start_idx or i >= (self.highlight_start_idx + self.bytes_seq.length):
                style = GREY_ADDRESS

            try:
                if b in UNPRINTABLE_ASCII:
                    style = style or BYTES_HIGHLIGHT
                    txt = Text('[', style=style)
                    txt.append(UNPRINTABLE_ASCII[b].upper(), style=f"{style} italic dim")
                    txt.append(Text(']', style=style))
                    output.append(txt)
                elif b < 127:
                    output.append(_byte.decode(encoding), style=style or BYTES_BRIGHTEST)
                elif encoding == 'utf-8':
                    if _byte in UNICODE_PREFIX_BYTES:
                        char_width = UNICODE_PREFIX_BYTES[_byte]
                        wide_char = self.surrounding_bytes[i:i + char_width].decode(encoding)
                        output.append(wide_char, style=style or BYTES_BRIGHTEST)
                        skip_next = char_width - 1  # Won't be set if there's a decoding exception
                        log.info(f"Skipping next {skip_next} bytes because UTF-8 multibyte char '{wide_char}' used them")
                    elif b <= 2047:
                        output.append((UNICODE_2_BYTE_PREFIX + _byte).decode(encoding), style=style or BYTES_BRIGHTEST)
                    else:
                        output.append(clean_byte_string(_byte), style=style or BYTES_BRIGHTER)
                else:
                    output.append(_byte.decode(encoding), style=style or BYTES_BRIGHTER)
            except UnicodeDecodeError:
                output.append(clean_byte_string(_byte), style=style or BYTES_BRIGHTER)

        return output

    def force_print_with_all_encodings(self) -> None:
        chardet_results = ChardetManager(self.bytes_seq.bytes).unique_results
        decoded_table = _build_decoded_bytes_table()
        chardet_results_in_table = []
        highlight_style = None
        table_rows = []

        # raw bytes is always first row - unlike the other rows we don't sort it by confidence
        decoded_table.add_row(RAW_BYTES, NA, build_rich_text_view_of_raw_bytes(self.surrounding_bytes, self.bytes_seq))

        # For checking duplicate decodes. Keys are encoding strings, values are the result of Text().plain()
        decoded_strings = {}

        # Highlight the highlighted_bytes_seq in the console output - in red if it's a mad sus one
        if self.bytes_seq.bytes in DANGEROUS_INSTRUCTIONS:
            highlight_style = 'fail'

        for encoding in ENCODINGS_TO_ATTEMPT:
            # Starting with a 'white' styled Text fixes the underlines filling the cell issue
            decoded_string = self.custom_decode(encoding, highlight_style)
            chardet_result = next((cr for cr in chardet_results if cr.encoding.plain == encoding), None)
            chardet_result = chardet_result or ChardetManager.build_chardet_result({'confidence': 0.0})
            log.debug(f"Found chardet_result for {encoding}: {chardet_result}")
            plain_decoded_string = decoded_string.plain

            if plain_decoded_string in decoded_strings.values():
                encoding_with_same_output = get_dict_key_by_value(decoded_strings, plain_decoded_string)
                decoded_string = Text('same output as ', style='color(66) bold')
                decoded_string.append(encoding_with_same_output, style='encoding')
                decoded_string.append('...', style='white')
            else:
                decoded_strings[encoding] = plain_decoded_string

            confidence_str = chardet_result.confidence_str or Text('-', style='color(242)')
            encoding_headline = Text('', style='white') + Text(encoding, style='encoding')
            table_rows.append([encoding_headline, confidence_str, decoded_string, chardet_result.confidence or 0.0])

            if chardet_result.encoding is not None:
                chardet_results_in_table.append(chardet_result)

        # Append the chardet confidence metrics that have not been paired with an actual decode attempt as extra table rows
        for result in chardet_results:
            if result in chardet_results_in_table or result.confidence is None or result.confidence < CHARDET_CUTOFF:
                continue



            table_rows.append([
                result.encoding,
                result.confidence_str,
                Text('decode not attempted', style='color(247) italic'),
                result.confidence or 0.0])

        table_rows.sort(key=_decoded_table_sorter, reverse=True)

        for row in table_rows:
            decoded_table.add_row(*row[0:3])

        console.print(decoded_table)


def _build_decoded_bytes_table() -> Table:
    decoded_table = Table(
        'Encoding',
        'Encoding\nConfidence\n(chardet lib)',
        'Forced Decode Output',
        show_lines=True,
        border_style='bytes',
        header_style=f"color(100) italic")

    decoded_table.columns[0].style = 'white'
    decoded_table.columns[0].justify = 'right'
    decoded_table.columns[1].overflow = 'fold'
    decoded_table.columns[1].justify = 'center'
    decoded_table.columns[2].overflow = 'fold'

    for col in decoded_table.columns:
        col.vertical = 'middle'

    return decoded_table


def _decoded_table_sorter(row: list) -> Number:
    """Sorts the decoded strings table by chardet's returned confidence, with the alphabeet breaking ties"""
    return (row[3]) + (0.01 * ord(row[0].plain[0]))
