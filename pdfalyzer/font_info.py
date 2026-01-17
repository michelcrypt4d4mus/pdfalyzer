"""
Unify font information spread across a bunch of PdfObjects (Font, FontDescriptor,
and FontFile) into a single class.
"""
from dataclasses import asdict, dataclass, field, fields
from typing import cast

from pypdf._cmap import prepare_cm
from pypdf._font import Font
from pypdf.generic import ArrayObject, DictionaryObject, IndirectObject, NameObject, PdfObject, StreamObject, is_null_or_none
from rich.text import Text
from yaralyzer.output.rich_console import console
from yaralyzer.util.logging import log

from pdfalyzer.binary.binary_scanner import BinaryScanner
from pdfalyzer.output.character_mapping import print_character_mapping, print_prepared_charmap
from pdfalyzer.output.layout import print_section_subheader
from pdfalyzer.output.styles.node_colors import get_label_style
from pdfalyzer.output.tables.font_summary_table import font_summary_table
from pdfalyzer.util.adobe_strings import FONT, FONT_FILE, FONT_LENGTHS, RESOURCES, TO_UNICODE, W, WIDTHS

FONT_SECTION_PREVIEW_LEN = 30
MAX_REPR_STR_LEN = 20


@dataclass(kw_only=True)
class FontInfo:
    label: NameObject | str
    font_indirect: IndirectObject
    font: PdfObject = field(init=False)
    font_obj: Font = field(init=False)
    font_file: StreamObject | None = None
    idnum: int = field(init=False)
    lengths: list[int] | None = None
    stream_data: bytes | None = None
    advertised_length: int | None = None
    binary_scanner: BinaryScanner | None = None
    prepared_char_map: bytes | None = None
    widths: list[int] | None = None
    # TODO: make methods
    base_font: str = ''
    sub_type: str = ''
    first_and_last_char: list[str] | None = None
    display_tile: str = ''
    bounding_box: tuple[float, float, float, float] | None = None
    flags: int | None = None
    character_mapping: dict[str, str] | None = None

    def __post_init__(self):
        self.idnum = self.font_indirect.idnum

        # /Font attributes
        self.font = self.font_indirect.get_object()
        self.font_obj = Font.from_font_resource(self.font.get_object())
        self.font_file = self.font_obj.font_descriptor.font_file
        self.base_font = f"/{self.font_obj.name}"
        self.sub_type = f"/{self.font_obj.sub_type}"
        self.widths = self.font.get(WIDTHS) or self.font.get(W)

        if isinstance(self.widths, IndirectObject):
            self.widths = self.widths.get_object()

        self.first_and_last_char = [self.font.get('/FirstChar'), self.font.get('/LastChar')]
        self.display_title = f"{self.idnum}. Font {self.label} "

        if (self.sub_type or "Unknown") == "Unknown":
            log.warning(f"Font type not given for {self.display_title}")
            self.display_title += "(UNKNOWN FONT TYPE)"
        else:
            self.display_title += f"({self.sub_type[1:]})"

        # FontDescriptor attributes
        if not is_null_or_none(self.font_obj.font_descriptor):
            self.bounding_box = self.font_obj.font_descriptor.bbox
            self.flags = int(self.font_obj.font_descriptor.flags)

        self.prepared_char_map = prepare_cm(self.font) if TO_UNICODE in self.font else None
        self.character_mapping = self.font_obj.character_map if self.font_obj.character_map else None

        # /FontFile attributes
        if self.font_file is not None:
            self.lengths = [self.font_file[k] for k in FONT_LENGTHS if k in self.font_file]
            self.stream_data = self.font_obj.font_descriptor.font_file.get_data()
            self.advertised_length = sum(self.lengths)
            scanner_label = Text(self.display_title, get_label_style(FONT_FILE))
            self.binary_scanner = BinaryScanner(self.stream_data, self, scanner_label)
            # import pdb;pdb.set_trace()

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

    def __repr__(self) -> str:
        d = {}
        print("\n\n")

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
    def extract_font_infos(cls, obj_with_resources: DictionaryObject) -> ['FontInfo']:
        """
        Extract all the fonts from a given /Resources PdfObject node.
        obj_with_resources must have '/Resources' because that's what _cmap module expects
        """
        resources = obj_with_resources[RESOURCES].get_object()
        fonts = resources.get(FONT)

        if is_null_or_none(fonts):
            log.info(f'No fonts found in {obj_with_resources}')
            return []

        fonts = fonts.get_object()
        return [cls(label=label, font_indirect=font) for label, font in fonts.items()]
