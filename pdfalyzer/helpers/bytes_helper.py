import re
from io import StringIO

from rich.console import Console
from rich.text import Text

from pdfalyzer.binary.bytes_match import BytesMatch
from pdfalyzer.config import PdfalyzerConfig
from pdfalyzer.detection.constants.character_encodings import NEWLINE_BYTE
from pdfalyzer.helpers.rich_text_helper import BYTES_HIGHLIGHT, console
from pdfalyzer.util.logging import log

HEX_CHARS_PER_GROUP = 8
HEX_GROUPS_PER_LINE = 4


def get_bytes_before_and_after_match(_bytes: bytes, match: re.Match, num_before=None, num_after=None) -> bytes:
    """
    Get all bytes from num_before the start of the sequence up until num_after the end of the sequence
    num_before and num_after will both default to the env var/CLI options having to do with surrounding
    bytes. If only num_before is provided then num_after will use it as a default.
    """
    return get_bytes_surrounding_range(_bytes, match.start(), match.end(), num_before, num_after)


def get_bytes_surrounding_range(_bytes: bytes, start_idx: int, end_idx: int, num_before=None, num_after=None) -> bytes:
    num_after = num_after or num_before or PdfalyzerConfig.NUM_SURROUNDING_BYTES
    num_before = num_before or PdfalyzerConfig.NUM_SURROUNDING_BYTES
    start_idx = max(start_idx - num_before, 0)
    end_idx = min(end_idx + num_after, len(_bytes))
    return _bytes[start_idx:end_idx]


def clean_byte_string(bytes_array: bytes) -> str:
    """Gives you a string representation of bytes w/no cruft e.g. '\x80\nx44' instead of "b'\x80\nx44'"."""
    byte_printer = Console(file=StringIO())
    byte_printer.out(bytes_array, end='')
    bytestr = byte_printer.file.getvalue()

    if bytestr.startswith("b'"):
        bytestr = bytestr.removeprefix("b'").removesuffix("'")
    elif bytestr.startswith('b"'):
        bytestr = bytestr.removeprefix('b"').removesuffix('"')
    else:
        raise RuntimeError(f"Unexpected byte string {bytestr}")

    return bytestr


def rich_text_view_of_raw_bytes(_bytes: bytes, bytes_match: BytesMatch) -> Text:
    """Print raw bytes to a Text object, highlighing the bytes in the bytes_match BytesMatch"""
    surrounding_bytes_str = clean_byte_string(_bytes)
    highlighted_bytes_str = clean_byte_string(bytes_match.bytes)
    highlighted_bytes_str_length = len(highlighted_bytes_str)
    highlight_idx = _find_str_rep_of_bytes(surrounding_bytes_str, highlighted_bytes_str, bytes_match)

    txt = Text(surrounding_bytes_str[:highlight_idx], style='grey')
    matched_bytes_str = surrounding_bytes_str[highlight_idx:highlight_idx + highlighted_bytes_str_length]
    txt.append(matched_bytes_str, style=bytes_match.highlight_style)
    txt.append(surrounding_bytes_str[highlight_idx + highlighted_bytes_str_length:], style='grey')
    return txt


def hex_view_of_raw_bytes(_bytes: bytes, bytes_match: BytesMatch) -> Text:
    hex_str = Text(' '.join([hex(b).removeprefix('0x').rjust(2, '0') for i, b in enumerate(_bytes)]), style='grey')
    highlight_start_idx = bytes_match.highlight_start_idx * 3
    highlight_end_idx = bytes_match.highlight_end_idx * 3
    hex_str.stylize(bytes_match.highlight_style, highlight_start_idx, highlight_end_idx)
    lines = hex_str.wrap(console, HEX_CHARS_PER_GROUP * HEX_GROUPS_PER_LINE * 3)
    return Text("\n").join([Text('  ').join(line.wrap(console, HEX_CHARS_PER_GROUP * 3)) for line in lines])


def print_bytes(bytes_array: bytes, style=None) -> None:
    """Convert bytes to a string representation and print to console"""
    for line in bytes_array.split(NEWLINE_BYTE):
        console.print(clean_byte_string(line), style=style or 'bytes')


def _find_str_rep_of_bytes(surrounding_bytes_str: str, highlighted_bytes_str: str, highlighted_bytes: BytesMatch):
    """
    Find the position of bytes_str in surrounding_byte_str. Both args are raw text dumps of binary data.
    Because strings are longer than bytes (stuff like '\xcc' are 4 chars when printed are one byte and the ANSI unprintables
    include stuff like 'NegativeAcknowledgement' which is over 20 chars) they represent so we have to re-find the location to highlight the bytes
    correctly.
    """
    # Start a few chars in to avoid errors: sometimes we're searching for 1 or 2 bytes and there's a false positive
    # in the extra bytes. Tthis isn't perfect - it's starting us at the first index into the *bytes* that's safe to
    # check but this is almost certainly far too soon given the large % of bytes that take 4 chars to print ('\x02' etc)
    highlight_idx = surrounding_bytes_str.find(highlighted_bytes_str, highlighted_bytes.highlight_start_idx)

    # TODO: Somehow \' and ' don't always come out the same :(
    if highlight_idx == -1:
        log.info(f"Failed to find highlighted_bytes in first pass so deleting single quotes and retrying." + \
                "  Highlighting may be off by a few chars,")

        surrounding_bytes_str = surrounding_bytes_str.replace("\\'", "'")
        highlight_idx = surrounding_bytes_str.find(highlighted_bytes_str)

        if highlight_idx == -1:
            log.warning(f"Failed to find\n{highlighted_bytes_str}\nin surrounding bytes:\n{surrounding_bytes_str}")
            log.warning("Highlighting will not work on this decoded string.")

    return highlight_idx
