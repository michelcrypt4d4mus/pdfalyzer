"""
Unify font information spread across a bunch of PdfObjects (Font, FontDescriptor,
and FontFile) into a single class.
"""
from dataclasses import dataclass, field
from typing import cast

from pypdf._cmap import prepare_cm
from pypdf._font import Font
from pypdf.generic import DictionaryObject, IndirectObject, NameObject, PdfObject
from rich.text import Text
from yaralyzer.output.rich_console import console
from yaralyzer.util.logging import log

from pdfalyzer.binary.binary_scanner import BinaryScanner
from pdfalyzer.output.character_mapping import print_character_mapping, print_prepared_charmap
from pdfalyzer.output.layout import print_section_subheader
from pdfalyzer.output.styles.node_colors import get_label_style
from pdfalyzer.output.tables.font_summary_table import font_summary_table
from pdfalyzer.util.adobe_strings import (FONT, FONT_FILE, FONT_LENGTHS, RESOURCES,
     SUBTYPE, TO_UNICODE, TYPE, W, WIDTHS)

FONT_SECTION_PREVIEW_LEN = 30


class FontInfo:
    @classmethod
    def extract_font_infos(cls, obj_with_resources: DictionaryObject) -> ['FontInfo']:
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
        return [cls(label, font.idnum, font.get_object()) for label, font in fonts.items()]

    def __init__(self, label: NameObject | str, idnum: int, font: DictionaryObject):
        self.label = label
        self.idnum = idnum
        self.font_obj = Font.from_font_resource(font)
        self.font_file = self.font_obj.font_descriptor.font_file

        # /Font attributes
        self.font = font
        self.base_font = f"/{self.font_obj.name}"
        self.sub_type = f"/{self.font_obj.sub_type}"
        self.widths = font.get(WIDTHS) or font.get(W)

        if isinstance(self.widths, IndirectObject):
            self.widths = self.widths.get_object()

        self.first_and_last_char = [font.get('/FirstChar'), font.get('/LastChar')]
        self.display_title = f"{self.idnum}. Font {self.label} "

        if (self.sub_type or "Unknown") == "Unknown":
            log.warning(f"Font type not given for {self.display_title}")
            self.display_title += "(UNKNOWN FONT TYPE)"
        else:
            self.display_title += f"({self.sub_type[1:]})"

        # FontDescriptor attributes
        if self.font_obj.font_descriptor is not None:
            self.bounding_box = self.font_obj.font_descriptor.bbox
            self.flags = self.font_obj.font_descriptor.flags
        else:
            self.bounding_box = None
            self.flags = None

        self.prepared_char_map = prepare_cm(font) if TO_UNICODE in font else None
        self.character_mapping = self.font_obj.character_map if self.font_obj.character_map else None

        # /FontFile attributes
        if self.font_file is not None:
            self.lengths = [self.font_file[k] for k in FONT_LENGTHS if k in self.font_file]
            self.stream_data = self.font_obj.font_descriptor.font_file.get_data()
            self.advertised_length = sum(self.lengths)
            scanner_label = Text(self.display_title, get_label_style(FONT_FILE))
            self.binary_scanner = BinaryScanner(self.stream_data, self, scanner_label)
        else:
            self.lengths = None
            self.stream_data = None
            self.advertised_length = None
            self.binary_scanner = None

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
    # def preview_bytes_at_advertised_lengths(self):
    #     """Show the bytes at the boundaries provided by /Length1, /Length2, and /Length3, if they exist"""
    #     lengths = self.lengths or []

    #     if self.lengths is None or len(lengths) <= 1:
    #         console.print("No length demarcations to preview.", style='grey.dark')

    #     for i, demarcation in enumerate(lengths[1:]):
    #         console.print(f"{self.font_file} at /Length{i} ({demarcation}):")
    #         print(f"\n  Stream before: {self.stream_data[demarcation - FONT_SECTION_PREVIEW_LEN:demarcation + 1]}")
    #         print(f"\n  Stream after: {self.stream_data[demarcation:demarcation + FONT_SECTION_PREVIEW_LEN]}")

    #     print(f"\nfinal bytes back from {self.stream_data.lengths[2]} + 10: {self.stream_data[-10 - -f.lengths[2]:]}")

    def __str__(self) -> str:
        return self.display_title
