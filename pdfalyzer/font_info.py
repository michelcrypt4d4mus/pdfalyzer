from dataclasses import asdict, dataclass, field, fields
from typing import Self, cast

from pypdf._cmap import prepare_cm
from pypdf._font import Font
from pypdf.generic import ArrayObject, DictionaryObject, IndirectObject, NameObject, PdfObject, StreamObject, is_null_or_none
from rich.table import Table
from rich.text import Text
from yaralyzer.output.rich_console import console
from yaralyzer.util.logging import log

from pdfalyzer.binary.binary_scanner import BinaryScanner
from pdfalyzer.decorators.pdf_tree_node import PdfTreeNode
from pdfalyzer.helpers.dict_helper import without_nones
from pdfalyzer.output.character_mapping import print_character_mapping, print_prepared_charmap
from pdfalyzer.output.layout import print_section_subheader, subheading_width
from pdfalyzer.output.styles.node_colors import get_class_style, get_label_style
from pdfalyzer.util.adobe_strings import DESCENDANT_FONTS, FONT, FONT_DESCRIPTOR, FONT_FILE, FONT_FILE_KEYS, FONT_LENGTHS, RESOURCES, TO_UNICODE, W, WIDTHS

FONT_SECTION_PREVIEW_LEN = 30
MAX_REPR_STR_LEN = 20

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
    display_title: str = field(init=False)
    font_dict: DictionaryObject = field(init=False)
    font_descriptor_dict: DictionaryObject = field(init=False)
    font_obj: Font = field(init=False)
    idnum: int = field(init=False)
    lengths: list[int] | None = None
    stream_data: bytes | None = None
    binary_scanner: BinaryScanner | None = None
    prepared_char_map: bytes | None = None
    widths: list[int] | None = None
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
        self.widths = self.font_dict.get(WIDTHS) or self.font_dict.get(W)

        if isinstance(self.widths, IndirectObject):
            self.widths = self.widths.get_object()

        if (self.font_obj.sub_type or "Unknown") == "Unknown":
            log.warning(f"Font type not given for {self.display_title}")
            self.display_title += "(UNKNOWN FONT TYPE)"
        else:
            self.display_title += f"({self.font_obj.sub_type})"

        if FONT_DESCRIPTOR in self.font_dict or DESCENDANT_FONTS in self.font_dict:
            # CID or composite fonts have a 1 element array in /DescendantFonts that has the /FontDescriptor
            if DESCENDANT_FONTS in self.font_dict and FONT_DESCRIPTOR in self.font_dict[DESCENDANT_FONTS][0]:
                self.font_descriptor_dict = self.font_dict[DESCENDANT_FONTS][0][FONT_DESCRIPTOR].get_object()
                self.widths = self.font_obj.character_widths
            elif FONT_DESCRIPTOR in self.font_dict:
                self.font_descriptor_dict = cast(DictionaryObject, self.font_dict[FONT_DESCRIPTOR].get_object())

            # pypdf FontDescriptor fills in defaults for these props so we have to extract from source
            if self.font_descriptor_dict:
                self.bounding_box = self.font_descriptor_dict['/FontBBox']
                self.flags = int(self.font_descriptor_dict['/Flags'])
            else:
                log.warning(f"Found no {FONT_DESCRIPTOR} for font {self.display_title}")

        # /FontFile attributes
        if self.font_obj.font_descriptor.font_file is not None:
            self.lengths = [
                self.font_obj.font_descriptor.font_file[k] for k in FONT_LENGTHS
                if k in self.font_obj.font_descriptor.font_file
            ]

            self.stream_data = self.font_obj.font_descriptor.font_file.get_data()
            self.advertised_length = sum(self.lengths)
            scanner_label = Text(self.display_title, get_label_style(FONT_FILE))
            self.binary_scanner = BinaryScanner(self.stream_data, self, scanner_label)

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

    def _first_and_last_char(self) -> list[int]:
        return without_nones([self.font_dict.get('/FirstChar'), self.font_dict.get('/LastChar')])

    def _flag_names(self) -> list[str]:
        flags = self.flags or 0
        return [name for bit, name in FONT_FLAG_BIT_POSITIONS.items() if bool(flags & 1 << (bit - 1))]

    def _summary_table(self) -> Table:
        """Build a Rich `Table` with important info about the font"""
        table = Table(show_header=False)
        table.add_column(style='font.property', justify='right')
        table.add_column()

        def add_table_row(name, value, style: str = ''):
            value = value if isinstance(value, Text) else Text(str(value), style or get_class_style(value))
            table.add_row(name, value)

        add_table_row('Subtype', self.font_obj.sub_type)
        add_table_row('FontName', self.font_obj.name)  # TODO: is this really BaseFont?
        # add_table_row('Encoding', self.font_dict["/Encoding"])
        add_table_row('pypdf interpretable?', self.font_obj.interpretable)
        add_table_row('bounding_box', self.bounding_box)
        add_table_row('/Length properties', self.lengths)
        add_table_row('/FirstChar, /LastChar', self._first_and_last_char())

        if self.flags:
            add_table_row('style flags', f"{self.flags} (" + ', '.join(self._flag_names()) + ')', 'cyan')

        add_table_row('total advertised length', self.advertised_length)

        if self.binary_scanner is not None:
            add_table_row('embedded binary length', self.binary_scanner.stream_length)
        if self.prepared_char_map is not None:
            add_table_row('prepared charmap length', len(self.prepared_char_map))
        if  self.font_obj.character_map:
            add_table_row('character mapping count', len( self.font_obj.character_map))
        if self.widths is not None:
            for k, v in self._width_stats().items():
                add_table_row(f"char width {k}", v)

            # Check if there's a single number repeated over and over.
            if len(set(self.widths)) == 1:
                table.add_row(
                    'char widths',
                    Text(
                        f"{self.widths[0]} (single value repeated {len(self.widths)} times)",
                        style=get_class_style(list)
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
        elif (RESOURCES in node.obj and isinstance(node.obj[RESOURCES], DictionaryObject)):
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
