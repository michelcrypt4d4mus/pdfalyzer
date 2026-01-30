"""
Unify font information spread across a bunch of PdfObjects (Font, FontDescriptor,
and FontFile) into a single class.
"""
from dataclasses import dataclass, field
from typing import Self, cast

from pypdf._cmap import prepare_cm
from pypdf._font import Font, FontDescriptor
from pypdf.generic import DictionaryObject, EncodedStreamObject, IndirectObject, NameObject, PdfObject
from rich.table import Table
from rich.text import Text
from yaralyzer.output.console import console
from yaralyzer.util.helpers.rich_helper import DEFAULT_TABLE_OPTIONS

from pdfalyzer.binary.binary_scanner import BinaryScanner
from pdfalyzer.output.character_mapping import print_character_mapping, print_prepared_charmap
from pdfalyzer.output.layout import print_section_subheader, subheading_width
from pdfalyzer.output.theme import get_class_style, get_label_style
from pdfalyzer.util.adobe_strings import (FONT, FONT_DESCRIPTOR, FONT_FILE, FONT_LENGTHS, RESOURCES,
     SUBTYPE, TO_UNICODE, TYPE, W, WIDTHS)
from pdfalyzer.util.logging import log

FONT_SECTION_PREVIEW_LEN = 30

ATTRIBUTES_TO_SHOW_IN_SUMMARY_TABLE = [
    'sub_type',
    'base_font',
    'flags',
    'bounding_box',
]


class FontInfo:
    @classmethod
    def extract_font_infos(cls, obj_with_resources: DictionaryObject) -> list[Self]:
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
        return [cls.build(label, font) for label, font in fonts.items()]

    @classmethod
    def build(cls, label: str, font_ref: IndirectObject) -> Self:
        """Build a FontInfo object from a IndirectObject ref to a /Font"""
        font_obj = cast(DictionaryObject, font_ref.get_object())
        font_descriptor = None
        font_file = None

        if font_obj.get(TYPE) != FONT:
            raise TypeError(f"{TYPE} of {font_ref} is not {FONT}")

        if font_obj.get(FONT_DESCRIPTOR):
            font_descriptor = font_obj[FONT_DESCRIPTOR].get_object()
            font_file_keys = [k for k in font_descriptor.keys() if FONT_FILE in k]

            # There's /FontFile, /FontFile2, etc. but whichever it is there should be only one
            if len(font_file_keys) > 1:
                raise RuntimeError(f"Too many /FontFile keys in {font_descriptor}: {font_file_keys}")
            elif len(font_file_keys) == 0:
                log.info(f"No font_file found in {font_descriptor}")
            else:
                font_file = font_descriptor[font_file_keys[0]].get_object()

        return cls(label, font_ref.idnum, font_obj, font_descriptor, font_file)

    def __init__(
        self,
        label: NameObject | str,
        idnum: int,
        font: DictionaryObject,
        font_descriptor: DictionaryObject,
        font_file: EncodedStreamObject
    ):
        self.label = label
        self.idnum = idnum
        self.font_file = font_file
        self.descriptor = font_descriptor
        self.font_obj = Font.from_font_resource(font)

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
        if self.font_obj.font_descriptor is not None:
            self.bounding_box = self.font_obj.font_descriptor.bbox
            self.flags = self.font_obj.font_descriptor.flags
        else:
            self.bounding_box = None
            self.flags = None

        self.prepared_char_map = prepare_cm(font) if TO_UNICODE in font else None
        self.character_mapping = self.font_obj.character_map if self.font_obj.character_map else None

        # /FontFile attributes
        if font_file is not None:
            self.lengths = [font_file[k] for k in FONT_LENGTHS if k in font_file]
            self.stream_data = font_file.get_data()
            self.advertised_length = sum(self.lengths)
            scanner_label = Text(self.display_title, get_label_style(FONT_FILE))
            self.binary_scanner = BinaryScanner(self.stream_data, self, scanner_label)
        else:
            self.lengths = None
            self.stream_data = None
            self.advertised_length = None
            self.binary_scanner = None

    def print_summary(self):
        """Prints a table of info about the font drawn from the various PDF objects. quote_type of None means all."""
        print_section_subheader(str(self), style='font.title')
        console.print(self._summary_table())
        console.line()

        if self.character_mapping:
            print_character_mapping(self)
        else:
            log.info(f"No character map found in {self}")

        if self.prepared_char_map:
            print_prepared_charmap(self)
        else:
            log.info(f"No prepared_charmap found in {self}")

        console.line()

    def _summary_table(self) -> Table:
        """Build a Rich `Table` with important info about the font"""
        table = Table(show_header=False, **DEFAULT_TABLE_OPTIONS)
        table.add_column(style='font.property', justify='right')
        table.add_column()

        def add_table_row(name, value):
            table.add_row(name, Text(str(value), get_class_style(value)))

        for attr in ATTRIBUTES_TO_SHOW_IN_SUMMARY_TABLE:
            attr_value = getattr(self, attr)
            add_table_row(attr, attr_value)

        add_table_row('/Length properties', self.lengths)
        add_table_row('total advertised length', self.advertised_length)

        if self.binary_scanner is not None:
            add_table_row('actual length', self.binary_scanner.stream_length)
        if self.prepared_char_map is not None:
            add_table_row('prepared charmap length', len(self.prepared_char_map))
        if self.character_mapping:
            add_table_row('character mapping count', len(self.character_mapping))
        if self.widths is not None:
            for k, v in self._width_stats().items():
                add_table_row(f"char width {k}", v)

            # Check if there's a single number repeated over and over.
            if len(set(self.widths)) == 1:
                table.add_row(
                    'char widths',
                    Text(
                        f"{self.widths[0]} (single value repeated {len(self.widths)} times)",
                        style=get_class_style([])
                    )
                )
            else:
                add_table_row('char widths', self.widths)
                add_table_row('char widths(sorted)', sorted(self.widths))

        col_0_width = max([len(entry) for entry in table.columns[0]._cells]) + 4
        table.columns[1].max_width = subheading_width() - col_0_width - 3
        return table

    def _width_stats(self):
        if self.widths is None:
            return {}

        return {
            'min': min(self.widths),
            'max': max(self.widths),
            'count': len(self.widths),
            'unique_count': len(set(self.widths)),
        }

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
