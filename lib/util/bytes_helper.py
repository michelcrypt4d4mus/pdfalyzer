from collections import namedtuple
from io import StringIO
from os import environ

from rich.console import Console
from rich.text import Text

from lib.util.adobe_strings import DANGEROUS_PDF_KEYS
from lib.util.logging import log
from lib.util.rich_text_helper import BYTES_HIGHLIGHT
from lib.util.string_utils import console


# Unicode prefix for 2 byte width unicode chars
UNICODE_2_BYTE_PREFIX = b'\xc0'
NEWLINE_BYTE = b"\n"

# Keys are bytes, values are number of bytes in a character starting with that byte
UNICODE_PREFIX_BYTES = {
    UNICODE_2_BYTE_PREFIX: 2,
    b'\xe0': 3,
    b'\xf0': 4
}

# Byte order marks
BOMS = {
    b'\x2b\x2f\x76': 'UTF-7 BOM',
    b'\xef\xbb\xbf': 'UTF-8 BOM',
    b'\xfe\xff':     'UTF-16 BOM',
    b'\x0e\xfe\xff': 'SCSU BOM',
}

# Remove the leading '/' from elements of DANGEROUS_PDF_KEYS and convert to bytes, except /F ("URL")
DANGEROUS_BYTES = [instruction[1:].encode() for instruction in DANGEROUS_PDF_KEYS] + [b'/F']
DANGEROUS_JAVASCRIPT_INSTRUCTIONS = [b'eval']
DANGEROUS_INSTRUCTIONS = DANGEROUS_BYTES + DANGEROUS_JAVASCRIPT_INSTRUCTIONS + list(BOMS.keys())

# Surrounding bytes
SURROUNDING_BYTES_ENV_VAR = 'SURROUNDING_BYTES'
SURROUNDING_BYTES_LENGTH_DEFAULT = 64
MINIMUM_EXTRA_BYTES = 16

# Unused cruft
ENCODINGS = [
    'big5',
    'big5hkscs',
    'cp950',
    'gb2312',
    'gbk',
    'gb18030',
    'hz',
    'iso2022_jp_2',
    'utf-7',
    'utf-8',
    'utf-16',
]

# Contains actual bytes as well as their location in a larger byte sequence
BytesSequence = namedtuple('BytesSequence', ['bytes', 'start_position', 'end_position', 'length'])


def get_bytes_before_and_after_sequence(_bytes: bytes, byte_seq: BytesSequence, num_before=None, num_after=None) -> bytes:
    """Get all bytes from num_before the start of the sequence up until num_after the end of the sequence"""
    num_before = num_before or num_surrounding_bytes()
    num_after = num_after or num_surrounding_bytes()
    start_idx = max(byte_seq.start_position - num_before, 0)
    end_idx = min(byte_seq.end_position + num_after, len(_bytes))
    return _bytes[start_idx:end_idx]


def num_surrounding_bytes():
    """Number of bytes to show before/after byte previews and decodes. Configured by command line options or env vars"""
    return int(environ.get(SURROUNDING_BYTES_ENV_VAR, SURROUNDING_BYTES_LENGTH_DEFAULT))


def clean_byte_string(bytes_array: bytes) -> str:
    """Gives you '\x80\nx44' instead of b'\x80\nx44'"""
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


def build_rich_text_view_of_raw_bytes(surrounding_bytes: bytes, highlighted_byte_seq: BytesSequence) -> Text:
    """Print raw bytes to a Text object, highlighing the bytes in the highlighted_byte_seq BytesSequence"""
    surrounding_bytes_str = clean_byte_string(surrounding_bytes)
    highlighted_bytes_str = clean_byte_string(highlighted_byte_seq.bytes)
    highlighted_bytes_str_length = len(highlighted_bytes_str)
    highlight_idx = _find_str_rep_of_bytes(surrounding_bytes_str, highlighted_bytes_str, highlighted_byte_seq)

    # Highlight the matched highlighted_byte_seq in the console output
    if highlighted_byte_seq.bytes in DANGEROUS_INSTRUCTIONS:
        highlight_style = 'fail'
    else:
        highlight_style = BYTES_HIGHLIGHT

    # Print bytes
    section = Text(surrounding_bytes_str[:highlight_idx], style='grey')
    section.append(surrounding_bytes_str[highlight_idx:highlight_idx + highlighted_bytes_str_length], style=highlight_style)
    section.append(surrounding_bytes_str[highlight_idx + highlighted_bytes_str_length:], style='grey')
    return section


def print_bytes(bytes_array: bytes, style=None) -> None:
    """Convert bytes to a string representation and print to console"""
    for line in bytes_array.split(NEWLINE_BYTE):
        console.print(clean_byte_string(line), style=style or 'bytes')


def _find_str_rep_of_bytes(surrounding_bytes_str: str, highlighted_bytes_str: str, highlighted_byte_seq: BytesSequence):
    """Find the position of bytes_str in surrounding_byte_str"""
    # Strings are longer bytes they represent so we have to re-find the location to highlight.
    # Start a few chars in to avoid errors: sometimes we're searching for 1 or 2 bytes and there's a false positive
    if highlighted_byte_seq.start_position > num_surrounding_bytes():
        start_search_idx = (num_surrounding_bytes() - 1)
    else:
        start_search_idx = highlighted_byte_seq.start_position

    highlight_idx = surrounding_bytes_str.find(highlighted_bytes_str, start_search_idx)

    # TODO: Somehow \' and ' don't always come out the same :(
    if highlight_idx == -1:
        log.warning(f"Failed to find highlighted_bytes in first pass. Deleting single quotes and retrying. Highlighting may be off by a few chars,")
        surrounding_bytes_str = surrounding_bytes_str.replace("\\'", "'")
        highlight_idx = surrounding_bytes_str.find(highlighted_bytes_str)

        if highlight_idx == -1:
            log.warning(f"Failed to find\n{highlighted_bytes_str}\nin surrounding bytes:\n{surrounding_bytes_str}")
            log.warning("Highlighting will not work on this decoded string.")

    return highlight_idx
