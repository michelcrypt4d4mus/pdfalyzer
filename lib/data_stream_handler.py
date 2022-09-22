"""
Class for handling binary data streams. Currently focused on font binaries.
"""
import re
from os import environ

from rich.panel import Panel
from rich.text import Text

from lib.util.adobe_strings import CURRENTFILE_EEXEC
from lib.bytes_decoder import BytesDecoder
from lib.util.bytes_helper import BOMS, DANGEROUS_INSTRUCTIONS, BytesSequence, print_bytes
from lib.util.string_utils import CONSOLE_PRINT_WIDTH, SUBHEADING_WIDTH, console, generate_hyphen_line
from lib.util.logging import log


# Command line options
LIMIT_DECODES_LARGER_THAN_ENV_VAR = 'LIMIT_DECODES_LARGER_THAN_ENV_VAR'
LIMIT_DECODE_OF_QUOTED_BYTES_LONGER_THAN = 256
# TODO: should be a command line option
BYTE_STREAM_PREVIEW_SIZE = 10 * int(CONSOLE_PRINT_WIDTH * 0.8)
SHORT_QUOTE_LENGTH = 128

# Bytes
ESCAPED_DOUBLE_QUOTE_BYTES = b'\\"'
ESCAPED_SINGLE_QUOTE_BYTES = b"\\'"
FRONT_SLASH_BYTE = b"/"
CAPTURE_BYTES = b'(.*?)'

# Regexes used to create iterators to find quoted bytes/strings/etc of interest
QUOTE_REGEXES = {
    'backtick': re.compile(b'`(.*?)`', re.DOTALL),
    'guillemet': re.compile(b'\xab(.*?)\xbb', re.DOTALL),
    'escaped double quote': re.compile(ESCAPED_DOUBLE_QUOTE_BYTES + CAPTURE_BYTES + ESCAPED_DOUBLE_QUOTE_BYTES, re.DOTALL),
    'escaped single quote': re.compile(ESCAPED_SINGLE_QUOTE_BYTES + CAPTURE_BYTES + ESCAPED_SINGLE_QUOTE_BYTES, re.DOTALL),
    'front slash': re.compile(FRONT_SLASH_BYTE + CAPTURE_BYTES + FRONT_SLASH_BYTE, re.DOTALL),
}


class DataStreamHandler:
    def __init__(self, _bytes: bytes):
        self.bytes = _bytes
        limit_decode_value = int(environ.get(LIMIT_DECODES_LARGER_THAN_ENV_VAR, LIMIT_DECODE_OF_QUOTED_BYTES_LONGER_THAN))
        self.limit_decodes_larger_than = limit_decode_value

    def check_for_dangerous_instructions(self) -> None:
        console.print(Panel("Scanning font binary for 'mad sus' bytes", style='danger_header', width=SUBHEADING_WIDTH))

        for instruction in DANGEROUS_INSTRUCTIONS:
            instruction_regex = re.compile(re.escape(instruction), re.DOTALL)
            explainer = f"({BOMS[instruction]}) " if instruction in BOMS else ''
            instructions_instances_found = 0

            for byte_seq in self.extract_regex_capture_bytes(instruction_regex):
                msg = f"Found {instruction} {explainer}at idx {byte_seq.start_position} of {len(self.bytes)}!"
                console.print(msg,style='bytes_highlighted')
                instructions_instances_found += 1
                decoder = BytesDecoder(self.bytes, byte_seq)
                decoder.force_print_with_all_encodings()
                console.print("\n")

            if instructions_instances_found == 0:
                console.print(f"{instruction} not found...", style='dim')

    def print_stream_preview(self, num_bytes=BYTE_STREAM_PREVIEW_SIZE, title_suffix=None) -> None:
        """Print a preview showing the beginning and end of the stream data"""
        snipped_byte_count = self.stream_length() - (num_bytes * 2)

        if snipped_byte_count < 0:
            title = f"All {self.stream_length()} bytes in stream"
        else:
            title = f"First and last {num_bytes} bytes of {self.stream_length()} byte stream"

        title += title_suffix if title_suffix is not None else ''
        console.print('')
        console.print(Panel(title, style='bytes_title', expand=False))
        console.print(generate_hyphen_line(title='BEGIN BYTES'), style='dim')

        if snipped_byte_count < 0:
            print_bytes(self.bytes)
        else:
            print_bytes(self.bytes[:num_bytes])
            console.print(f"\n    <...skip {snipped_byte_count} bytes...>\n", style='dim')
            print_bytes(self.bytes[-num_bytes:])

        console.print(generate_hyphen_line(title='END BYTES'), style='dim')
        console.print('')

    def force_decode_all_quoted_bytes(self) -> None:
        """Find all strings matching QUOTE_REGEXES (AKA between quote chars) and decode them with various encodings"""
        for quote_type, regex in QUOTE_REGEXES.items():
            console.print("\n\n")
            msg = f"Force Decode All {quote_type.capitalize()} Quoted Strings"
            console.print(Panel(msg, style='decode_section', width=SUBHEADING_WIDTH))
            quoted_byte_seqs_found = 0

            for quoted_bytes in self.extract_regex_capture_bytes(regex):
                if quoted_bytes.length > self.limit_decodes_larger_than or quoted_bytes.length == 0:
                    self._print_suppressed_decode(quoted_bytes, quote_type)
                    continue

                quoted_byte_seqs_found += 1
                console.print(self._decode_attempt_subheading_panel(quoted_bytes, quote_type))
                decoder = BytesDecoder(self.bytes, quoted_bytes)
                decoder.force_print_with_all_encodings()
                console.print("")

            if quoted_byte_seqs_found == 0:
                console.print(f"No {quote_type} quoted byte sequences found in binary data...", style='grey')

    # These iterators will iterate over all the first capture groups of all the matches they find for the
    # regex they pass to extract_regex_capture_bytes() as an argument. It's very easy to build a similar
    # iterator if you find a pattern you want to dig for.
    def extract_guillemet_quoted_bytes(self):
        """Iterate on all strings surrounded by Guillemet quotes, e.g. «string»"""
        return self.extract_regex_capture_bytes(QUOTE_REGEXES['guillemet'])

    def extract_backtick_quoted_bytes(self):
        """Returns an interator over all strings surrounded by backticks"""
        return self.extract_regex_capture_bytes(QUOTE_REGEXES['backtick'])

    def extract_front_slash_quoted_bytes(self):
        """Returns an interator over all strings surrounded by front_slashes (hint: regular expressions)"""
        return self.extract_regex_capture_bytes(QUOTE_REGEXES['front_slaash'])

    def extract_regex_capture_bytes(self, regex_with_one_capture: re) -> BytesSequence:
        """Finds all matches of regex_with_one_capture in self.bytes and calls yield() with BytesSequence tuples"""
        for match in regex_with_one_capture.finditer(self.bytes, self._eexec_idx()):
            try:
                match_bytes = match[1]
            except IndexError:
                log.debug(f"No capture group for {regex_with_one_capture}")
                match_bytes = regex_with_one_capture.pattern

            yield(BytesSequence(match_bytes, match.start(), match.end(), len(match_bytes)))

    def bytes_after_eexec_statement(self) -> bytes:
        """Get the bytes after the 'eexec' demarcation line (if it appears). See Adobe docs for details."""
        return self.bytes.split(CURRENTFILE_EEXEC)[1] if CURRENTFILE_EEXEC in self.bytes else self.bytes

    def stream_length(self) -> int:
        """Returns the number of bytes in the stream"""
        return len(self.bytes)

    def _decode_attempt_subheading_panel(self, quoted_bytes: bytes, quote_type: str) -> Panel:
        """Generate a Rich panel for decode attempts"""
        headline = Text('Found ', style='decode_subheading')
        headline.append(str(quoted_bytes.length), style='number')
        headline.append(f" bytes between {quote_type.lower()} quotes ")
        headline.append(f"(start idx: ", style='off_white')
        headline.append(str(quoted_bytes.start_position), style='number')
        headline.append(', end idx: ', style='off_white')
        headline.append(str(quoted_bytes.end_position), style='number')
        headline.append(')', style='off_white')
        return Panel(headline, style='decode_subheading', expand=False)

    def _print_suppressed_decode(self, quoted_bytes: bytes, quote_type: str) -> None:
        """Print a message indicating that we are not going to decode a given block of bytes"""
        if quoted_bytes.length == 0:
            msg = f"  Skipping zero length {quote_type} quoted bytes at {quoted_bytes.start_position}...\n"
            console.print(msg, style='dark_grey_italic')
            return

        msg = f"Suppressing decode of {quoted_bytes.length} byte {quote_type} at "
        txt = Text(msg + f"position {quoted_bytes.start_position} (", style='bytes_title')
        txt.append(f"--limit-decodes is {self.limit_decodes_larger_than} bytes", style='grey')
        txt.append(')', style='bytes_title dim')
        console.print(Panel(txt, style='bytes', expand=False))

    def _eexec_idx(self) -> int:
        """Returns the location of CURRENTFILES_EEXEC or 0"""
        return self.bytes.find(CURRENTFILE_EEXEC) if CURRENTFILE_EEXEC in self.bytes else 0
