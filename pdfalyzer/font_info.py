"""
Unify font information spread across a bunch of PdfObjects (Font, FontDescriptor,
and FontFile) into a single class.
"""

from pypdf._cmap import build_char_map, prepare_cm
from pypdf.generic import IndirectObject, PdfObject
from rich.text import Text
from yaralyzer.output.rich_console import console
from yaralyzer.util.logging import log

from pdfalyzer.binary.binary_scanner import BinaryScanner
from pdfalyzer.output.character_mapping import print_character_mapping, print_prepared_charmap
from pdfalyzer.output.tables.font_summary_table import font_summary_table
from pdfalyzer.output.layout import print_section_subheader
from pdfalyzer.output.styles.node_colors import get_label_style
from pdfalyzer.util.adobe_strings import (FONT, FONT_DESCRIPTOR, FONT_FILE, FONT_LENGTHS, RESOURCES,
     SUBTYPE, TO_UNICODE, TYPE, W, WIDTHS)

FONT_SECTION_PREVIEW_LEN = 30


class FontInfo:
    @classmethod
    def extract_font_infos(cls, obj_with_resources: PdfObject) -> ['FontInfo']:
        """
        Extract all the fonts from a given /Resources PdfObject node.
        obj_with_resources must have '/Resources' because that's what _cmap module expects
        """
        resources = obj_with_resources[RESOURCES]

        if isinstance(resources, IndirectObject):
            resources = resources.get_object()

        fonts = resources.get(FONT)

        if fonts is None:
            log.info(f'No fonts found in {obj_with_resources}')
            return []

        fonts = fonts.get_object()
        return [cls.build(label, font, obj_with_resources) for label, font in fonts.items()]

    @classmethod
    def build(cls, label: str, font_ref: IndirectObject, obj_with_resources) -> 'FontInfo':
        """Build a FontInfo object from a IndirectObject ref to a /Font"""
        font_obj = font_ref.get_object()
        font_descriptor = None
        font_file = None

        if font_obj.get(TYPE) != FONT:
            raise TypeError(f"{TYPE} of {font_ref} is not {FONT}")

        if FONT_DESCRIPTOR in font_obj:
            font_descriptor = font_obj[FONT_DESCRIPTOR].get_object()
            font_file_keys = [k for k in font_descriptor.keys() if FONT_FILE in k]

            # There's /FontFile, /FontFile2, etc. but whichever it is there should be only one
            if len(font_file_keys) > 1:
                raise RuntimeError(f"Too many /FontFile keys in {font_descriptor}: {font_file_keys}")
            elif len(font_file_keys) == 0:
                log.info(f"No font_file found in {font_descriptor}")
            else:
                font_file = font_descriptor[font_file_keys[0]].get_object()

        return cls(label, font_ref.idnum, font_obj, font_descriptor, font_file, obj_with_resources)

    def __init__(self, label, idnum, font, font_descriptor, font_file, obj_with_resources):
        self.label = label
        self.idnum = idnum
        self.font_file = font_file
        self.descriptor = font_descriptor

        # /Font attributes
        self.font = font
        self.sub_type = font.get(SUBTYPE)
        self.widths = font.get(WIDTHS) or font.get(W)

        if isinstance(self.widths, IndirectObject):
            self.widths = self.widths.get_object()

        self.base_font = font.get('/BaseFont')
        self.first_and_last_char = [font.get('/FirstChar'), font.get('/LastChar')]
        self.display_title = f"{self.idnum}. Font {self.label} "

        if self.sub_type is None:
            log.warning(f"Font type not given for {self.display_title}")
            self.display_title += "(UNKNOWN FONT TYPE)"
        else:
            self.display_title += f"({self.sub_type[1:]})"

        # FontDescriptor attributes
        if font_descriptor is not None:
            self.bounding_box = font_descriptor.get('/FontBBox')
            self.flags = font_descriptor.get('/Flags')
        else:
            self.bounding_box = None
            self.flags = None

        # /FontFile attributes
        if font_file is not None:
            self.lengths = [font_file[k] for k in FONT_LENGTHS if k in font_file]
            self.stream_data = font_file.get_data()
            self.advertised_length = sum(self.lengths)
            scanner_label = Text(self.display_title, get_label_style(FONT_FILE))
            self.binary_scanner = BinaryScanner(self.stream_data, self, scanner_label)
            self.prepared_char_map = prepare_cm(font) if TO_UNICODE in font else None
            # TODO: shouldn't we be passing ALL the widths?
            self._char_map = build_char_map(label, self.widths[0], obj_with_resources)

            try:
                self.character_mapping = self._char_map[3]
            except (IndexError, TypeError):
                log.warning(f"Exception trying to get character mapping for {self}")
                self.character_mapping = []
        else:
            self.lengths = None
            self.stream_data = None
            self.advertised_length = None
            self.binary_scanner = None
            self.prepared_char_map = None
            self._char_map = None
            self.character_mapping = None

    def width_stats(self):
        if self.widths is None:
            return {}

        return {
            'min': min(self.widths),
            'max': max(self.widths),
            'count': len(self.widths),
            'unique_count': len(set(self.widths)),
        }

    def print_summary(self):
        """Prints a table of info about the font drawn from the various PDF objects. quote_type of None means all."""
        print_section_subheader(str(self), style='font.title')
        console.print(font_summary_table(self))
        console.line()
        print_character_mapping(self)
        print_prepared_charmap(self)
        console.line()

    # TODO: currently unused
    def preview_bytes_at_advertised_lengths(self):
        """Show the bytes at the boundaries provided by /Length1, /Length2, and /Length3, if they exist"""
        lengths = self.lengths or []

        if self.lengths is None or len(lengths) <= 1:
            console.print("No length demarcations to preview.", style='grey.dark')

        for i, demarcation in enumerate(lengths[1:]):
            console.print(f"{self.font_file} at /Length{i} ({demarcation}):")
            print(f"\n  Stream before: {self.stream_data[demarcation - FONT_SECTION_PREVIEW_LEN:demarcation + 1]}")
            print(f"\n  Stream after: {self.stream_data[demarcation:demarcation + FONT_SECTION_PREVIEW_LEN]}")

        print(f"\nfinal bytes back from {self.stream_data.lengths[2]} + 10: {self.stream_data[-10 - -f.lengths[2]:]}")

    def __str__(self) -> str:
        return self.display_title
