"""
Class for handling binary data - scanning through it for various suspicious patterns as well as forcing
various character encodings upon it to see what comes out.
"""
import re
from collections import defaultdict
from numbers import Number
from typing import Any, Iterator, Pattern

from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from pdfalyzer.binary.bytes_decoder import BytesDecoder
from pdfalyzer.binary.bytes_match import BytesMatch
from pdfalyzer.config import PdfalyzerConfig
from pdfalyzer.detection.constants.binary_regexes import QUOTE_REGEXES
from pdfalyzer.detection.constants.character_encodings import BOMS
from pdfalyzer.detection.constants.binary_regexes import DANGEROUS_INSTRUCTIONS
from pdfalyzer.detection.regex_match_metrics import RegexMatchMetrics
from pdfalyzer.helpers.bytes_helper import clean_byte_string, get_bytes_before_and_after_match, print_bytes
from pdfalyzer.helpers.rich_text_helper import (CENTER, DANGER_HEADER, NOT_FOUND_MSG, console, console_width,
     generate_subtable, na_txt, pad_header, prefix_with_plain_text_obj, subheading_width)
from pdfalyzer.helpers.string_helper import generate_hyphen_line, print_section_header
from pdfalyzer.util.adobe_strings import CURRENTFILE_EEXEC
from pdfalyzer.util.logging import log


# For rainbow colors
CHAR_ENCODING_1ST_COLOR_NUMBER = 203


class BinaryScanner:
    def __init__(self, _bytes: bytes, owner: Any = None):
        self.bytes = _bytes
        self.owner = owner
        self.stream_length = len(_bytes)
        self.regex_extraction_stats = defaultdict(lambda: RegexMatchMetrics())
        self.suppression_notice_queue = []

    def check_for_dangerous_instructions(self) -> None:
        """Scan for all the strings in DANGEROUS_INSTRUCTIONS list and decode bytes around them"""
        print_section_header("Scanning Font Binary For Anything 'Mad Sus'...", style=DANGER_HEADER)

        for instruction in DANGEROUS_INSTRUCTIONS:
            instruction_regex = re.compile(re.escape(instruction), re.DOTALL)
            label = f"({BOMS[instruction]}) " if instruction in BOMS else clean_byte_string(instruction)
            self._process_regex_matches(instruction_regex, label, force=True)

    def force_decode_all_quoted_bytes(self) -> None:
        """Find all strings matching QUOTE_REGEXES (AKA between quote chars) and decode them with various encodings"""
        quote_types = QUOTE_REGEXES.keys() if PdfalyzerConfig.QUOTE_TYPE is None else [PdfalyzerConfig.QUOTE_TYPE]

        for quote_type in quote_types:
            quote_regex = QUOTE_REGEXES[quote_type]
            print_section_header(f"Forcing Decode of {quote_type.capitalize()} Quoted Strings", style='color(100)')
            self._process_regex_matches(quote_regex, label=f"{quote_type} quoted")

    def extract_regex_capture_bytes(self, regex: Pattern[bytes]) -> Iterator[BytesMatch]:
        """Finds all matches of regex_with_one_capture in self.bytes and calls yield() with BytesMatch tuples"""
        for i, match in enumerate(regex.finditer(self.bytes, self._eexec_idx())):
            surrounding_bytes = get_bytes_before_and_after_match(self.bytes, match)
            yield(BytesMatch(match, surrounding_bytes, i))


    # -------------------------------------------------------------------------------
    # These extraction iterators will iterate over all matches for a specific pattern.
    # extract_regex_capture_bytes() is the generalized method that acccepts any regex.
    # -------------------------------------------------------------------------------
    def extract_guillemet_quoted_bytes(self) -> Iterator[BytesMatch]:
        """Iterate on all strings surrounded by Guillemet quotes, e.g. «string»"""
        return self.extract_regex_capture_bytes(QUOTE_REGEXES['guillemet'])

    def extract_backtick_quoted_bytes(self) -> Iterator[BytesMatch]:
        """Returns an interator over all strings surrounded by backticks"""
        return self.extract_regex_capture_bytes(QUOTE_REGEXES['backtick'])

    def extract_front_slash_quoted_bytes(self) -> Iterator[BytesMatch]:
        """Returns an interator over all strings surrounded by front_slashes (hint: regular expressions)"""
        return self.extract_regex_capture_bytes(QUOTE_REGEXES['front_slaash'])


    def print_stream_preview(self, num_bytes=None, title_suffix=None) -> None:
        """Print a preview showing the beginning and end of the stream data"""
        num_bytes = num_bytes or console_width()
        snipped_byte_count = self.stream_length - (num_bytes * 2)
        console.line()

        if snipped_byte_count < 0:
            title = f"All {self.stream_length} bytes in stream"
        else:
            title = f"First and last {num_bytes} bytes of {self.stream_length} byte stream"

        title += title_suffix if title_suffix is not None else ''
        console.print(Panel(title, style='bytes_title', expand=False))
        console.print(generate_hyphen_line(title='BEGIN BYTES'), style='dim')

        if snipped_byte_count < 0:
            print_bytes(self.bytes)
        else:
            print_bytes(self.bytes[:num_bytes])
            console.print(f"\n    <...skip {snipped_byte_count} bytes...>\n", style='dim')
            print_bytes(self.bytes[-num_bytes:])

        console.print(generate_hyphen_line(title='END BYTES'), style='dim')
        console.line()

    def print_decoding_stats_table(self) -> None:
        """Diplay aggregate results on the decoding attempts we made on subsets of self.bytes"""
        stats_table = new_decoding_stats_table(f"{self.owner or ''}")
        regexes_not_found_in_stream = []

        for regex, stats in self.regex_extraction_stats.items():
            # Set aside the regexes we didn't find so that the ones we did find are at the top of the table
            if stats.match_count == 0:
                regexes_not_found_in_stream.append([str(regex.pattern), NOT_FOUND_MSG, na_txt()])
                continue

            regex_subtable = generate_subtable(cols=['Metric', 'Value'])
            decodes_subtable = generate_subtable(cols=['Encoding', 'Decoded', 'Forced', 'Failed'])

            for metric, measure in vars(stats).items():
                if isinstance(measure, Number):
                    regex_subtable.add_row(metric, str(measure))

            for i, (encoding, count) in enumerate(stats.was_match_decodable.items()):
                style = f"color({CHAR_ENCODING_1ST_COLOR_NUMBER + 2 * i})"
                decodes_subtable.add_row(
                    Text(encoding, style=style),
                    str(count),
                    str(self.regex_extraction_stats[regex].was_match_force_decoded[encoding]),
                    str(self.regex_extraction_stats[regex].was_match_undecodable[encoding]))

            stats_table.add_row(str(regex.pattern), regex_subtable, decodes_subtable)

        for row in regexes_not_found_in_stream:
            row[0] = Text(row[0], style='color(235)')
            stats_table.add_row(*row, style='color(232)')

        console.line(2)
        console.print(stats_table)

    def bytes_after_eexec_statement(self) -> bytes:
        """Get the bytes after the 'eexec' demarcation line (if it appears). See Adobe docs for details."""
        return self.bytes.split(CURRENTFILE_EEXEC)[1] if CURRENTFILE_EEXEC in self.bytes else self.bytes

    def _process_regex_matches(self, regex: Pattern[bytes], label: str, force: bool=False) -> None:
        """Decide whether to attempt to decode the matched bytes, track stats. force param ignores min/max length"""
        for bytes_match in self.extract_regex_capture_bytes(regex):
            self.regex_extraction_stats[regex].match_count += 1
            self.regex_extraction_stats[regex].bytes_matched += bytes_match.capture_len
            self.regex_extraction_stats[regex].bytes_match_objs.append(bytes_match)

            # Send suppressed decodes to a queue and track the reason for the suppression in the stats
            if not (force or PdfalyzerConfig.MIN_DECODE_LENGTH < bytes_match.capture_len < PdfalyzerConfig.MAX_DECODE_LENGTH):
                self._queue_suppression_notice(bytes_match, label)
                continue

            # Print out any queued suppressed notices before printing non suppressed matches
            self._print_suppression_notices()
            self._attempt_binary_decodes(bytes_match, label or clean_byte_string(regex.pattern))

        if self.regex_extraction_stats[regex].match_count == 0:
            console.print(f"{regex.pattern} was not found for {label}...", style='dim')

    def _attempt_binary_decodes(self, bytes_match: BytesMatch, label: str) -> None:
        """Attempt to decode _bytes with all configured encodings and print a table of the results"""
        decoder = BytesDecoder(bytes_match, label)
        decoder.print_decode_attempts()
        console.line()

        # Track stats on whether the bytes were decodable or not w/a given encoding
        self.regex_extraction_stats[bytes_match.regex].matches_decoded += 1

        for encoding, count in decoder.was_match_decodable.items():
            decode_stats = self.regex_extraction_stats[bytes_match.regex].was_match_decodable
            decode_stats[encoding] = decode_stats.get(encoding, 0) + count

        for encoding, count in decoder.was_match_undecodable.items():
            failure_stats = self.regex_extraction_stats[bytes_match.regex].was_match_undecodable
            failure_stats[encoding] = failure_stats.get(encoding, 0) + count

        for encoding, count in decoder.was_match_force_decoded.items():
            forced_stats = self.regex_extraction_stats[bytes_match.regex].was_match_force_decoded
            forced_stats[encoding] = forced_stats.get(encoding, 0) + count

    def _queue_suppression_notice(self, bytes_match: BytesMatch, quote_type: str) -> None:
        """Print a message indicating that we are not going to decode a given block of bytes"""
        self.regex_extraction_stats[bytes_match.regex].skipped_matches_lengths[bytes_match.capture_len] += 1
        txt = bytes_match.__rich__()

        if bytes_match.capture_len < PdfalyzerConfig.MIN_DECODE_LENGTH:
            txt = Text('Too little to actually attempt decode at ', style='grey') + txt
        else:
            txt.append(" is too large to decode ")
            txt.append(f"(--max-decode-length is {PdfalyzerConfig.MAX_DECODE_LENGTH} bytes)", style='grey')

        log.debug(Text('Queueing suppression notice: ') + txt)
        self.suppression_notice_queue.append(txt)

    def _print_suppression_notices(self) -> None:
        """Print notices in queue in a single panel; empty queue"""
        if len(self.suppression_notice_queue) == 0:
            return

        suppression_notices_txt = Text("\n").join([notice for notice in self.suppression_notice_queue])
        panel = Panel(suppression_notices_txt, style='bytes', expand=False)
        console.print(panel)
        self.suppression_notice_queue = []

    def _eexec_idx(self) -> int:
        """Returns the location of CURRENTFILES_EEXEC within the binary stream dataor 0"""
        return self.bytes.find(CURRENTFILE_EEXEC) if CURRENTFILE_EEXEC in self.bytes else 0


def new_decoding_stats_table(title) -> Table:
    """Build an empty table for displaying decoding stats"""
    table = Table(
        title=prefix_with_plain_text_obj(title, style='blue underline') + Text(f": Decoding Attempts Summary Statistics"),
        min_width=subheading_width(),
        show_lines=True,
        padding=[0, 1],
        style='color(18)',
        border_style='color(111) dim',
        header_style='color(235) on color(249) reverse',
        title_style='color(249) bold')

    def add_column(header, **kwargs):
        table.add_column(pad_header(header.upper()), **kwargs)

    add_column('Byte Pattern', vertical='middle', style='color(25) bold reverse', justify='right')
    add_column('Aggregate Metrics', overflow='fold', justify=CENTER)
    add_column('Per Encoding Metrics', justify=CENTER)
    return table
