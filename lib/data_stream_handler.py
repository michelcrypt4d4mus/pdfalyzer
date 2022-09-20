"""
Class for handling binary data streams. Currently focused on font binaries.
"""
import chardet
import re

from rich.panel import Panel
from rich.text import Text

from lib.util.adobe_strings import CURRENTFILE_EEXEC, DANGEROUS_PDF_KEYS
from lib.util.string_utils import (CONSOLE_PRINT_WIDTH, clean_byte_string, console, force_utf8_print,
     generate_hyphen_line, print_bytes)
from lib.util.logging import log


BYTE_STREAM_PREVIEW_SIZE = 10 * int(CONSOLE_PRINT_WIDTH * 0.8)
SURROUNDING_BYTES_LENGTH = 256

BOMS = [
    b'\xef\xbb\xbf',   # UTF-8 BOM
    b'\xfe\xff,'       # UTF-16 BOM
    b'\x0e\xfe\xff',   # SCSU
    b'\x2b\x2f\x76'    # UTF-7
]

# Remove the leading '/' from elements of DANGEROUS_PDF_KEYS and convert to bytes, except /F ("URL")
DANGEROUS_BYTES = [instruction[1:].encode() for instruction in DANGEROUS_PDF_KEYS] + [b'/F']
DANGEROUS_JAVASCRIPT_INSTRUCTIONS = [b'eval']
DANGEROUS_INSTRUCTIONS = DANGEROUS_BYTES + DANGEROUS_JAVASCRIPT_INSTRUCTIONS + BOMS


class DataStreamHandler:
    def __init__(self, _bytes: bytes):
        self.bytes = _bytes

    def check_for_dangerous_instructions(self):
        console.print(Panel('Scanning font binary for dangerous PDF instructions', style='dark_red', expand=False))
        was_dangerous_instruction_found = False

        for instruction in DANGEROUS_INSTRUCTIONS:
            # Hacky way to ensure we start hunt at byte 0
            last_found_idx = -len(instruction)

            while instruction in self.bytes[last_found_idx + len(instruction):]:
                was_dangerous_instruction_found = True
                last_found_idx = self.bytes.find(instruction, last_found_idx + len(instruction))
                console.print(f"Found {instruction} at {last_found_idx} / {len(self.bytes)}!", style='bright_red bold')
                self._print_surrounding_bytes(last_found_idx, SURROUNDING_BYTES_LENGTH, instruction)

        if not was_dangerous_instruction_found:
            console.print('  No dangerous instructions found\n', style='dim')

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

    def attempt_encoding_detection(self, _bytes=None):
        """Use the chardet library to try to figure out the encoding of _bytes (or entire stream if _bytes is None)"""
        _bytes = self.bytes if _bytes is None else _bytes
        console.print("Attempting encoding detection with chardet library...")
        console.print(chardet.detect(_bytes))

    def extract_guillemet_quoted_strings(self):
        """Print out strings surrounded by Guillemet quotes, e.g. «string» would give 'string'"""
        self._extract_quoted_strings(rb'\xab(.*?)\xbb', 'guillemet')

    def extract_backtick_quoted_strings(self):
        """Print strings surrounded by backticks"""
        self._extract_quoted_strings(rb'`(.*?)`', 'backtick')

    def attempt_decode(self, chars, encoding):
        try:
            console.print(f"Decoded {encoding}: {chars.decode(encoding)}")

            if encoding != 'utf-16':
                input('decoded!')
        except UnicodeDecodeError:
            console.print(f"fail attempting decode of {len(chars)} chars in {encoding}:", style='grey')

    def bytes_after_eexec_statement(self):
        """Get the bytes after the 'eexec' (if it appears)"""
        if CURRENTFILE_EEXEC in self.bytes:
            return self.bytes.split(CURRENTFILE_EEXEC)[1]
        else:
            return self.bytes

    def stream_length(self):
        """Returns the number of bytes in the stream"""
        return len(self.bytes)

    def _extract_quoted_strings(self, quote_regex, label=None):
        """Generic method for use with quote regexes"""
        for match in re.finditer(quote_regex, self.bytes_after_eexec_statement(), re.S):
            match_bytes = match[1]
            label = '' if label is None else f'{label} '
            console.print(f"{label}quoted ({len(match_bytes)} bytes):\n {match_bytes}\n\n")

    def _print_surrounding_bytes(self, around_idx: int, size: int, highlighted_bytes):
        """Print the bytes before and after a given location in the stream"""
        start_idx = max(around_idx - SURROUNDING_BYTES_LENGTH, 0)
        end_idx = min(around_idx + SURROUNDING_BYTES_LENGTH + 2, len(self.bytes))
        surrounding_bytes = self.bytes[start_idx:end_idx]
        
        if len(surrounding_bytes) == 0:
            import pdb;pdb.set_trace()

        # Strings are longer than the bytes they represent so we have to re-find
        highlighted_bytes_str = clean_byte_string(highlighted_bytes)
        printable_bytes_str = clean_byte_string(surrounding_bytes)
        str_idx = printable_bytes_str.find(highlighted_bytes_str)
        highlighted_bytes_strlen = len(highlighted_bytes_str)

        # Highlight the matched highlighted_bytes in the console output
        section = Text(printable_bytes_str[:str_idx], style='bytes')
        section.append(printable_bytes_str[str_idx:str_idx + highlighted_bytes_strlen], style='fail')
        section.append(printable_bytes_str[str_idx + highlighted_bytes_strlen:], style='bytes')

        text = Text("Surrounding bytes: ", style='bright_white') + section
        console.print(text)
        console.print("Attempting UTF8 by force...")
        force_utf8_print(surrounding_bytes)
        console.print("\n")
