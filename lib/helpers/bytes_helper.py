from io import StringIO
from os import environ

from rich.console import Console
from rich.text import Text

from lib.binary.bytes_match import BytesMatch
from lib.detection.character_encodings import BOMS, NEWLINE_BYTE
from lib.helpers.rich_text_helper import BYTES_HIGHLIGHT, console
from lib.util.adobe_strings import DANGEROUS_PDF_KEYS
from lib.util.logging import log


# Remove the leading '/' from elements of DANGEROUS_PDF_KEYS and convert to bytes, except /F ("URL")
DANGEROUS_BYTES = [instruction[1:].encode() for instruction in DANGEROUS_PDF_KEYS] + [b'/F']
DANGEROUS_JAVASCRIPT_INSTRUCTIONS = [b'eval']
DANGEROUS_INSTRUCTIONS = DANGEROUS_BYTES + DANGEROUS_JAVASCRIPT_INSTRUCTIONS + list(BOMS.keys())

# Surrounding bytes
SURROUNDING_BYTES_ENV_VAR = 'PDFALYZER_SURROUNDING_BYTES'
SURROUNDING_BYTES_LENGTH_DEFAULT = 64



def get_bytes_before_and_after_match(_bytes: bytes, byte_seq: BytesMatch, num_before=None, num_after=None) -> bytes:
    """
    Get all bytes from num_before the start of the sequence up until num_after the end of the sequence
    num_before and num_after will both default to the env var/CLI options having to do with surrounding
    bytes. If only num_before is provided then num_after will use it as a default.
    """
    num_after = num_after or num_before or num_surrounding_bytes()
    num_before = num_before or num_surrounding_bytes()
    start_idx = max(byte_seq.start_idx - num_before, 0)
    end_idx = min(byte_seq.end_idx + num_after, len(_bytes))
    return _bytes[start_idx:end_idx]


def num_surrounding_bytes():
    """Number of bytes to show before/after byte previews and decodes. Configured by command line or env var"""
    return int(environ.get(SURROUNDING_BYTES_ENV_VAR, SURROUNDING_BYTES_LENGTH_DEFAULT))


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


def build_rich_text_view_of_raw_bytes(surrounding_bytes: bytes, highlighted_bytes: BytesMatch) -> Text:
    """Print raw bytes to a Text object, highlighing the bytes in the highlighted_bytes BytesMatch"""
    surrounding_bytes_str = clean_byte_string(surrounding_bytes)
    highlighted_bytes_str = clean_byte_string(highlighted_bytes.bytes)
    highlighted_bytes_str_length = len(highlighted_bytes_str)
    highlight_idx = _find_str_rep_of_bytes(surrounding_bytes_str, highlighted_bytes_str, highlighted_bytes)

    # Highlight the matched highlighted_bytes in the console output
    if highlighted_bytes.bytes in DANGEROUS_INSTRUCTIONS:
        highlight_style = 'error'
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


def _find_str_rep_of_bytes(surrounding_bytes_str: str, highlighted_bytes_str: str, highlighted_bytes: BytesMatch):
    """
    Find the position of bytes_str in surrounding_byte_str. Both args are raw text dumps of binary data.
    Because strings are longer than bytes (stuff like '\xcc' are 4 chars when printed are one byte and the ANSI unprintables
    include stuff like 'NegativeAcknowledgement' which is over 20 chars) they represent so we have to re-find the location to highlight the bytes
    correctly.
    Start a few chars in to avoid errors: sometimes we're searching for 1 or 2 bytes and there's a false positive in the extra bytes
    Note that this isn't perfect - it's starting us at the first index into the *bytes* that's safe to check but this is
    almost certainly far too soon given the large % of bytes that take 4 chars to print ('\x02' etc)
    """
    if highlighted_bytes.start_idx > num_surrounding_bytes():
        start_search_idx = (num_surrounding_bytes() - 1)
    else:
        start_search_idx = highlighted_bytes.start_idx

    highlight_idx = surrounding_bytes_str.find(highlighted_bytes_str, start_search_idx)

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
