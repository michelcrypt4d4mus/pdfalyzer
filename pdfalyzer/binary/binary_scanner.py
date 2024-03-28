"""
Class for handling binary data - scanning through it for various suspicious patterns as well as forcing
various character encodings upon it to see what comes out.
"""
from collections import defaultdict
from typing import Iterator, Optional, Tuple

from rich.panel import Panel
from rich.text import Text
from yaralyzer.bytes_match import BytesMatch
from yaralyzer.decoding.bytes_decoder import BytesDecoder
from yaralyzer.encoding_detection.character_encodings import BOMS
from yaralyzer.helpers.bytes_helper import hex_string, print_bytes
from yaralyzer.helpers.string_helper import escape_yara_pattern
from yaralyzer.output.rich_console import BYTES_NO_DIM, console, console_width
from yaralyzer.output.regex_match_metrics import RegexMatchMetrics
from yaralyzer.yara.yara_rule_builder import HEX, REGEX, safe_label
from yaralyzer.yaralyzer import Yaralyzer
from yaralyzer.util.logging import log

from pdfalyzer.config import PdfalyzerConfig
from pdfalyzer.decorators.pdf_tree_node import PdfTreeNode
from pdfalyzer.detection.constants.binary_regexes import (BACKTICK, DANGEROUS_PDF_KEYS_TO_HUNT_ONLY_IN_FONTS,
     DANGEROUS_PDF_KEYS_TO_HUNT_ONLY_IN_FONTS, DANGEROUS_STRINGS, FRONTSLASH, GUILLEMET, QUOTE_PATTERNS)
from pdfalyzer.helpers.string_helper import generate_hyphen_line
from pdfalyzer.output.layout import print_headline_panel, print_section_sub_subheader
from pdfalyzer.util.adobe_strings import CONTENTS, CURRENTFILE_EEXEC, FONT_FILE_KEYS


class BinaryScanner:
    def __init__(self, _bytes: bytes, owner: PdfTreeNode, label: Optional[Text] = None):
        """'owner' arg is an optional link back to the object containing this binary."""
        self.bytes = _bytes
        self.label = label
        self.owner = owner
        self.stream_length = len(_bytes)

        if label is None and isinstance(owner, PdfTreeNode):
             self.label = owner.__rich__()

        self.suppression_notice_queue = []
        self.regex_extraction_stats = defaultdict(lambda: RegexMatchMetrics())

    def check_for_dangerous_instructions(self) -> None:
        """Scan for all the strings in DANGEROUS_INSTRUCTIONS list and decode bytes around them."""
        subheader = "Scanning Binary For Anything That Could Be Described As 'sus'..."
        print_section_sub_subheader(subheader, style=f"bright_red")

        for instruction in DANGEROUS_STRINGS:
            yaralyzer = self._pattern_yaralyzer(instruction, REGEX)  # TODO maybe change REGEX const string?
            yaralyzer.highlight_style = 'bright_red bold'
            self.process_yara_matches(yaralyzer, instruction, force=True)

        # TODO code smell: This check should probably be in the calling code not here in the instance method
        if self.owner.type in FONT_FILE_KEYS:
            log.info(f"{self.owner} is a /FontFile. Scanning for short but dangerous PDF keys...")

            for instruction in DANGEROUS_PDF_KEYS_TO_HUNT_ONLY_IN_FONTS:
                yaralyzer = self._pattern_yaralyzer(instruction, REGEX)
                yaralyzer.highlight_style = 'bright_red bold'
                self.process_yara_matches(yaralyzer, instruction, force=True)

    def check_for_boms(self) -> None:
        """Check the binary data for BOMs."""
        print_section_sub_subheader("Scanning Binary for any BOMs...", style='BOM')

        for bom_bytes, bom_name in BOMS.items():
            yaralyzer = self._pattern_yaralyzer(hex_string(bom_bytes), HEX, bom_name)
            yaralyzer.highlight_style = 'BOM'
            self.process_yara_matches(yaralyzer, bom_name, force=True)

    def force_decode_quoted_bytes(self) -> None:
        """
        Find all strings matching QUOTE_PATTERNS (AKA between quote chars) and decode them with various encodings.
        The --quote-type arg will limit this decode to just one kind of quote.
        """
        quote_selections = PdfalyzerConfig._args.extract_quoteds

        if len(quote_selections) == 0:
            headline = "Skipping extract/decode of quoted bytes (--extract-quoted is empty)"
            print_section_sub_subheader(headline, style='grey')

        for quote_type in quote_selections:
            if self.owner and self.owner.type == CONTENTS and quote_type in [FRONTSLASH, GUILLEMET]:
                msg = f"Not attempting {quote_type} decode for {CONTENTS} node type..."
                print_headline_panel(msg, style='dim')
                continue

            quote_pattern = QUOTE_PATTERNS[quote_type]
            print_section_sub_subheader(f"Forcing Decode of {quote_type.capitalize()} Quoted Strings", style=BYTES_NO_DIM)
            yaralyzer = self._quote_yaralyzer(quote_pattern, quote_type)
            self.process_yara_matches(yaralyzer, f"{quote_type}_quoted")

    # -------------------------------------------------------------------------------
    # These extraction iterators will iterate over all matches for a specific pattern.
    # YARA rules are written on the fly and then YARA does the matching.
    # -------------------------------------------------------------------------------
    def extract_guillemet_quoted_bytes(self) -> Iterator[Tuple[BytesMatch, BytesDecoder]]:
        """Iterate on all strings surrounded by Guillemet quotes, e.g. «string»"""
        return self._quote_yaralyzer(QUOTE_PATTERNS[GUILLEMET], GUILLEMET).match_iterator()

    def extract_backtick_quoted_bytes(self) -> Iterator[Tuple[BytesMatch, BytesDecoder]]:
        """Returns an interator over all strings surrounded by backticks"""
        return self._quote_yaralyzer(QUOTE_PATTERNS[BACKTICK], BACKTICK).match_iterator()

    def extract_front_slash_quoted_bytes(self) -> Iterator[Tuple[BytesMatch, BytesDecoder]]:
        """Returns an interator over all strings surrounded by front_slashes (hint: regular expressions)."""
        return self._quote_yaralyzer(QUOTE_PATTERNS[FRONTSLASH], FRONTSLASH).match_iterator()

    def print_stream_preview(self, num_bytes=None, title_suffix=None) -> None:
        """Print a preview showing the beginning and end of the embedded stream data."""
        num_bytes = num_bytes or PdfalyzerConfig._args.preview_stream_length or console_width()
        snipped_byte_count = self.stream_length - (num_bytes * 2)
        console.line()

        if snipped_byte_count < 0:
            title = f"ALL {self.stream_length} BYTES IN STREAM"
        else:
            title = f"FIRST AND LAST {num_bytes} BYTES OF {self.stream_length} BYTE STREAM"

        title += title_suffix if title_suffix is not None else ''
        title = f"BEGIN {title}".upper()
        console.print(generate_hyphen_line(title=title), style='dim')

        if snipped_byte_count < 0:
            print_bytes(self.bytes)
        else:
            print_bytes(self.bytes[:num_bytes])
            console.print(f"\n    <...skip {snipped_byte_count} bytes...>\n", style='dim')
            print_bytes(self.bytes[-num_bytes:])

        console.print(generate_hyphen_line(title="END " + title), style='dim')
        console.line()

    def process_yara_matches(self, yaralyzer: Yaralyzer, pattern: str, force: bool = False) -> None:
        """Decide whether to attempt to decode the matched bytes, track stats. force param ignores min/max length."""
        for bytes_match, decoder in yaralyzer.match_iterator():
            log.debug(f"Trackings stats for match: {pattern}, bytes_match: {bytes_match}, is_decodable: {bytes_match.is_decodable()}")

            # Send suppressed decodes to a queue and track the reason for the suppression in the stats
            if not (bytes_match.is_decodable() or force):
                self.suppression_notice_queue.append(bytes_match.suppression_notice())
                continue

            # Print out any queued suppressed notices before printing non suppressed matches
            self._print_suppression_notices()
            console.print(decoder)
            self.regex_extraction_stats[pattern].tally_match(decoder) # TODO: This call must come after print(decoder)

        self._print_suppression_notices()

        # This check initializes the defaultdict for 'pattern'
        if self.regex_extraction_stats[pattern].match_count == 0:
            pass

    def bytes_after_eexec_statement(self) -> bytes:
        """Get the bytes after the 'eexec' demarcation line (if it appears). See Adobe docs for details."""
        return self.bytes.split(CURRENTFILE_EEXEC)[1] if CURRENTFILE_EEXEC in self.bytes else self.bytes

    def _quote_yaralyzer(self, quote_pattern: str, quote_type: str):
        """Helper method to build a Yaralyzer for a quote_pattern"""
        label = f"{quote_type}_Quoted"

        if quote_type == GUILLEMET:
            return self._pattern_yaralyzer(quote_pattern, HEX, label, label)
        else:
            return self._pattern_yaralyzer(quote_pattern, REGEX, label, label)

    def _pattern_yaralyzer(
            self,
            pattern: str,
            pattern_type: str,
            rules_label: Optional[str] = None,
            pattern_label: Optional[str] = None
        ) -> Yaralyzer:
        """Build a yaralyzer to scan self.bytes"""
        return Yaralyzer.for_patterns(
            patterns=[escape_yara_pattern(pattern)],
            patterns_type=pattern_type,
            scannable=self.bytes,
            scannable_label=self.label.plain,
            rules_label=safe_label(rules_label or pattern),  # TODO: maybe safe_label() belongs in yaralyzer
            pattern_label=safe_label(pattern_label or pattern)
        )

    def _print_suppression_notices(self) -> None:
        """Print the notices in queue in a single display panel and then empty the queue."""
        if len(self.suppression_notice_queue) == 0:
            return

        suppression_notices_txt = Text("\n").join([notice for notice in self.suppression_notice_queue])
        panel = Panel(suppression_notices_txt, style='bytes', expand=False)
        console.print(panel)
        self.suppression_notice_queue = []

    def _eexec_idx(self) -> int:
        """Returns the location of CURRENTFILES_EEXEC within the binary stream data (or 0 if it's not there)."""
        return self.bytes.find(CURRENTFILE_EEXEC) if CURRENTFILE_EEXEC in self.bytes else 0
