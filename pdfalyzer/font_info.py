from dataclasses import asdict, dataclass, field, fields
from typing import Self, cast

from pypdf._cmap import prepare_cm
from pypdf._font import Font
from pypdf.generic import ArrayObject, DictionaryObject, IndirectObject, NameObject, PdfObject, is_null_or_none
from rich.table import Table
from rich.text import Text
from yaralyzer.output.console import console
from yaralyzer.util.helpers.rich_helper import DEFAULT_TABLE_OPTIONS
from yaralyzer.util.logging import log

from pdfalyzer.binary.binary_scanner import BinaryScanner
from pdfalyzer.decorators.pdf_tree_node import PdfTreeNode
from pdfalyzer.output.character_mapping import print_character_mapping, print_prepared_charmap
from pdfalyzer.output.layout import print_section_subheader, subheading_width
from pdfalyzer.output.theme import get_class_style, get_label_style
from pdfalyzer.util.adobe_strings import (FONT, FONT_DESCRIPTOR, FONT_FILE, FONT_LENGTHS, RESOURCES,
     SUBTYPE, TO_UNICODE, TYPE, W, WIDTHS)
from pdfalyzer.util.helpers.collections_helper import without_falsey

FONT_SECTION_PREVIEW_LEN = 30
MAX_REPR_STR_LEN = 20
RAW_CHAR_WIDTHS = 'raw char widths'

FONT_FLAG_BIT_POSITIONS = {
    1: 'monospace',
    2: 'serif',
    3: 'symbolic',
    4: 'script',
    6: 'nonsymbolic',
    7: 'italic',
    17: 'allcaps',
    18: 'smallcaps',
    19: 'forcebold',
}


@dataclass(kw_only=True)
class FontInfo:
    """
    Extract and unify font information.
    """
    label: NameObject | str
    font_indirect: IndirectObject
    # Constructed properties
    binary_scanner: BinaryScanner | None = None
    descendant_fonts_subtype: str | None = None
    display_title: str = field(init=False)
    font_descriptor_dict: DictionaryObject = field(init=False)
    font_dict: DictionaryObject = field(init=False)
    font_obj: Font = field(init=False)
    idnum: int = field(init=False)
    lengths: list[int] | None = None
    prepared_char_map: bytes | None = None
    raw_widths: list[int] | None = None
    # TODO: make methods?
    advertised_length: int | None = None
    bounding_box: tuple[float, float, float, float] | None = None
    flags: int | None = None

    def __post_init__(self):
        self.idnum = self.font_indirect.idnum
        self.display_title = f"{self.idnum}. Font {self.label} "

        # /Font attributes
        self.font_dict = cast(DictionaryObject, self.font_indirect.get_object())
        self.font_obj = Font.from_font_resource(self.font_dict)
        self.raw_widths = self.font_dict.get(WIDTHS) or self.font_dict.get(W)

        if (self.font_obj.sub_type or "Unknown") == "Unknown":
            log.warning(f"Font type not given for {self.display_title}")
            self.display_title += "(UNKNOWN FONT TYPE)"
        else:
            self.display_title += f"({self.font_obj.sub_type})"

        try:
            self._extract_font_descriptor_props()
            self._extract_font_file_props()
        except Exception as e:
            log.warning(f"Failed to extract data from /FontDescriptor or /FontFile\n{self.font_descriptor_dict}, Error: {e}")
            self.font_descriptor_dict = None # TODO: should be a default maybe?

        if isinstance(self.raw_widths, IndirectObject):
            self.raw_widths = self.raw_widths.get_object()

        self.prepared_char_map = prepare_cm(self.font_dict) if TO_UNICODE in self.font_dict else None

    def print_summary(self):
        """Prints a table of info about the font drawn from the various PDF objects. quote_type of None means all."""
        print_section_subheader(str(self), style='font.title')
        console.print(self._summary_table())
        console.line()

        if self.font_obj.character_map:
            print_character_mapping(self)
        else:
            log.info(f"No character map found in {self}")

        if self.prepared_char_map:
            print_prepared_charmap(self)
        else:
            log.info(f"No prepared_charmap found in {self}")

        console.line()

    def _extract_font_descriptor_props(self) -> None:
        """Set various properties that come from /FontDescriptor."""
        if not (FONT_DESCRIPTOR in self.font_dict or DESCENDANT_FONTS in self.font_dict):
            return

        # CID or composite fonts have a 1 element array in /DescendantFonts that has the /FontDescriptor
        if DESCENDANT_FONTS in self.font_dict:
            descendant_font = self.font_dict[DESCENDANT_FONTS][0].get_object()

            if FONT_DESCRIPTOR in descendant_font:
                self.font_descriptor_dict = descendant_font[FONT_DESCRIPTOR].get_object()

            self.descendant_fonts_subtype = descendant_font.get(SUBTYPE)
            self.raw_widths = descendant_font.get(WIDTHS) or descendant_font.get(W)
        elif FONT_DESCRIPTOR in self.font_dict:
            self.font_descriptor_dict = cast(DictionaryObject, self.font_dict[FONT_DESCRIPTOR].get_object())

        # pypdf FontDescriptor fills in defaults for these props so we have to extract from source
        if self.font_descriptor_dict:
            self.bounding_box = self.font_descriptor_dict.get('/FontBBox')
            self.flags = int(self.font_descriptor_dict.get('/Flags'))
        else:
            log.warning(f"Found no {FONT_DESCRIPTOR} for font {self.display_title}")

    def _extract_font_file_props(self) -> None:
        """Set various properties that come from /FontFileX."""
        if not self.font_obj.font_descriptor.font_file:
            return

        self.lengths = [
            self.font_obj.font_descriptor.font_file[k] for k in FONT_LENGTHS
            if k in self.font_obj.font_descriptor.font_file
        ]

        if len(without_falsey(self.lengths)) > 0:
            self.advertised_length = sum(without_falsey(self.lengths))

        stream_data = self.font_obj.font_descriptor.font_file.get_data()
        scanner_label = Text(self.display_title, get_label_style(FONT_FILE))
        self.binary_scanner = BinaryScanner(stream_data, self, scanner_label)

    def _first_and_last_char(self) -> list[int]:
        return without_falsey([self.font_dict.get('/FirstChar'), self.font_dict.get('/LastChar')])

    def _flag_names(self) -> list[str]:
        flags = self.flags or 0
        return [name for bit, name in FONT_FLAG_BIT_POSITIONS.items() if bool(flags & 1 << (bit - 1))]

    def _summary_table(self) -> Table:
        """Build a Rich `Table` with important info about the font"""
        table = Table(show_header=False, **DEFAULT_TABLE_OPTIONS)
        table.add_column(style='font.property', justify='right')
        table.add_column()

        def add_table_row(name, value, style: str = '', row_style: str = ''):
            value = value if isinstance(value, Text) else Text(str(value), style or get_class_style(value))
            table.add_row(name, value, style=row_style)

        add_table_row('Subtype', self.font_obj.sub_type)
        add_table_row('FontName', self.font_obj.name)  # TODO: is this really BaseFont?

        if self.descendant_fonts_subtype:
            add_table_row(f"Composite Subtype", self.descendant_fonts_subtype[1:])
        if self.flags:
            add_table_row('style flags', f"{self.flags} (" + ', '.join(self._flag_names()) + ')', 'cyan')

        add_table_row('bounding_box', self.bounding_box)
        add_table_row('/FirstChar, /LastChar', self._first_and_last_char())
        add_table_row('pypdf interpretable', self.font_obj.interpretable)

        if self.binary_scanner is not None:
            row_style = 'red_alert' if self.advertised_length and self.binary_scanner.stream_length != self.advertised_length else ''
            add_table_row('/Length properties', self.lengths)
            add_table_row('embedded binary length', self.binary_scanner.stream_length, row_style=row_style)
            add_table_row('advertised binary length', self.advertised_length, row_style=row_style)
        if self.prepared_char_map is not None:
            add_table_row('prepared charmap length', len(self.prepared_char_map))
        if self.font_obj.character_map:
            add_table_row('character mapping count', len( self.font_obj.character_map))
        if self.raw_widths is not None:
            if all([isinstance(e, int) for e in self.raw_widths]):  # DescendantFonts include arrays in the list of widths
                for k, v in self._width_stats().items():
                    add_table_row(f"char width {k}", v)

                # Check if there's a single number repeated over and over.
                if len(set(self.raw_widths)) == 1:
                    table.add_row(
                        RAW_CHAR_WIDTHS,
                        Text(
                            f"{self.raw_widths[0]} (single value repeated {len(self.raw_widths)} times)",
                            style=get_class_style([])
                        )
                    )
                else:
                    add_table_row(RAW_CHAR_WIDTHS, self.raw_widths)
            else:
                add_table_row(RAW_CHAR_WIDTHS, self.raw_widths)
        if self.font_obj.character_widths:
            add_table_row('char widths', self.font_obj.character_widths)

        col_0_width = max([len(entry) for entry in table.columns[0]._cells]) + 4
        table.columns[1].max_width = subheading_width() - col_0_width - 3
        return table

    def _width_stats(self) -> dict[str, int]:
        if not self.raw_widths:
            return {}
        try:
            return {
                'min': min(self.raw_widths),
                'max': max(self.raw_widths),
                'count': len(self.raw_widths),
                'unique_count': len(set(self.raw_widths)),
            }
        except Exception as e:
            log.error(f"{self.display_title} Failed to get width stats from raw_widths:\n{self.raw_widths}")
            return {}

    def __repr__(self) -> str:
        d = {}

        for f in fields(self):
            value = getattr(self, f.name)
            value = str(value) if isinstance(value, NameObject) else value

            if isinstance(value, (bytes, str)) and len(value) > MAX_REPR_STR_LEN:
                if isinstance(value, (bytes)):
                    value = value[0:MAX_REPR_STR_LEN] + b'...'
                else:
                    value = f'"{value[0:MAX_REPR_STR_LEN]}..."'
            elif isinstance(value, ArrayObject):
                value = list(value)
            elif isinstance(value, (BinaryScanner, PdfObject)):
                value = f"<{type(value).__name__} obj>"
            elif isinstance(value, Font):
                value = f'Font(name="{value.name}")'
            elif isinstance(value, str):
                value = f'"{value}"'

            #log.warning(f"{f.name} ({type(value).__name__}): {value}")
            d[f.name] = value

        return f"FontInfo(\n    " + ',\n    '.join([f"{k}={v}" for k,v in d.items()]) + '\n)'

    def __str__(self) -> str:
        return self.display_title

    @classmethod
    def extract_font_infos(cls, node: PdfTreeNode) -> list[Self]:
        """Extract all the fonts from a given /Font PdfObject node."""
        if not isinstance(node.obj, DictionaryObject):
            return []
        elif isinstance(node.obj.get(RESOURCES), DictionaryObject) and FONT in node.obj[RESOURCES]:
            log.debug(f"Extracting fonts from node with '{RESOURCES}' that isn't IndirectObject): {node}...")
            obj = node.obj[RESOURCES]
        elif FONT in node.obj:
            log.debug(f"Extracting fonts from node with '{FONT}': {node}...")
            obj = node.obj
        else:
            return []

        font_dict = obj.get(FONT)

        if is_null_or_none(font_dict):
            log.warning(f'No fonts found in /Font {node}')
            return []

        fonts = [cls(label=label, font_indirect=font) for label, font in font_dict.items()]
        return fonts


# TODO: this should probably check if the fonts are actually the same instead of just
# matching the names.
def uniquify_fonts(fonts: list[Font]) -> list[Font]:
    font_name_map = {unique_font_string(f): f for f in fonts}
    return [f for f in font_name_map.values()]


def unique_font_string(f: Font) -> str:
    font_str = f"{f.sub_type}: {f.name}"
    font_str += f" (embedded /FontFile ID: {f.font_descriptor.font_file.indirect_reference.idnum})" if f.font_descriptor.font_file else ''
    return font_str
